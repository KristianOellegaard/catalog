from django.db import models
from decimal import Decimal
from django.conf import settings
from catalog import settings as default_settings
from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager
from django.utils.translation import ugettext_lazy as _
from PIL import Image
import os
import datetime
# Create your models here.

class OrderFee(models.Model):
    name = models.CharField(max_length=80)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    applies_below = models.DecimalField(max_digits=8, decimal_places=2)
    sites = models.ManyToManyField(Site)
    
    def __unicode__(self):
        return self.name
        
    class Meta:
        ordering = ['name']
        verbose_name, verbose_name_plural = _("order fee"), _("order fees")

class Fee(models.Model):
    name = models.CharField(max_length=80)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    def __unicode__(self):
        return self.name
        
    class Meta:
        ordering = ['name']
        verbose_name, verbose_name_plural = _(u"fee"), _(u"fees")

class Category(models.Model):
    """A category of Items in the Catalog"""
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    order = models.IntegerField(default=100)
    sites = models.ManyToManyField(Site)
    
    all_objects = models.Manager()
    objects = CurrentSiteManager("sites")
    
    def site_item_set(self):
        return self.item_set.all().filter(sites=Site.objects.get_current()).exclude(mainitem=None)

    class Meta:
        ordering = ['order', 'name']
        verbose_name, verbose_name_plural = _("category"), _("categories")
        
    def sites_display(self):
        l = []
        for site in self.sites.all():
            l.append(site.name)
        return ", ".join(l)

    def __unicode__(self):
        return self.name
        
    @models.permalink
    def url(self):
        return ('category_detail', (self.slug,), {})
    get_absolute_url = url

class Item(models.Model):
    """An item in the Catalog"""
    name = models.CharField(_("name"),max_length=80)
    slug = models.SlugField(_("slug"),unique=True)
    
    # Shops own item number, not to be confused with ID
    item_number = models.CharField(_("item number"),max_length=80, blank=True)
    
    price = models.DecimalField(_("price"),max_digits=8, decimal_places=2)
    description = models.TextField(_("description"),)
    category = models.ForeignKey(Category, verbose_name=_("category"),)
    
    amount_sold = models.IntegerField(_("amount sold"),editable=False, default=0)
    
    amount_on_stock = models.IntegerField(_("amount on stock"), default=0)
    
    related_items = models.ManyToManyField('Item', verbose_name=_("related items"),blank=True)
    
    extra_fees = models.ManyToManyField(Fee, verbose_name=_("extra fees"), blank=True)
    
    icon = models.FileField(_("icon"),upload_to="products/icons/", blank=True)
    image = models.FileField(_("image"),upload_to="products/images/", blank=True)
    sites = models.ManyToManyField(Site, verbose_name=_("sites"))
    
    @property
    def on_stock(self):
        if self.amount_on_stock > 0:
            return True
        else:
            return False

    class Meta:
        ordering = ['-amount_sold', 'name', 'price']
        verbose_name, verbose_name_plural = _("item"), _("items")

    def __unicode__(self):
        try:
            return u"%s - %s" % (self.name, self.subitem.variant_title)
        except:
            return self.name
    @models.permalink
    def url(self):
        return ('item_detail', (self.category.slug, self.slug), {})
    get_absolute_url = url
    
class MainItem(Item):
    class Meta:
        ordering = ['-amount_sold', 'name', 'price']
        verbose_name, verbose_name_plural = _("item"), _("items")

class SubItemType(models.Model):
    name = models.CharField(_("name"),max_length=80)
    class Meta:
        ordering = ['name',]
        verbose_name, verbose_name_plural = _("sub item type"), _("sub item types")
    def __unicode__(self):
        return self.name
    
class SubItem(Item):
    variant_of = models.ForeignKey(MainItem, related_name="subitem_set")
    variant_type = models.ForeignKey(SubItemType)
    variant_title = models.CharField(_("variant title"),max_length=80)
    
    class Meta:
        ordering = ['-amount_sold', 'name', 'price']
        verbose_name, verbose_name_plural = _("sub item"), _("sub items")
    

class Order(models.Model):
    first_name = models.CharField(_("first name"), max_length=80)
    last_name = models.CharField(_("last name"),max_length=80)
    address = models.CharField(_("address"),max_length=80)
    address_2 = models.CharField(_("address 2"),max_length=80, blank=True)
    postal_code = models.CharField(_("postal code"),max_length=80)
    city = models.CharField(_("city"),max_length=80)
    cellphone = models.IntegerField(_("cellphone"),max_length=8)
    email = models.EmailField(_("email"),max_length=80)
    IP = models.CharField(_("IP"),max_length=80, editable=False, blank=True)
    
    paid = models.BooleanField(_("paid"), editable=False)
    delivered = models.BooleanField(_("delivered"),)
    terms_accepted = models.BooleanField(_("terms accepted"),)
    newsletter = models.BooleanField(_("newsletter"),)
    
    site = models.ForeignKey(Site, verbose_name=_("site"),)
    
    @property
    def slug(self):
        return self.id
    
    def get_full_name(self):
        return u"%s %s" % (self.first_name, self.last_name)
    
    def get_payments(self):
        total = Decimal(0)
        for payment in self.orderpayment_set.all():
            total += payment.amount
        s = ""
        if self.orderfailedpayment_set.all():
            for error in self.orderfailedpayment_set.all():
                s = s + error.error_text + "\n"
        if total == self.total():
            return _(u"Paid")
        elif total == 0 and not self.orderfailedpayment_set.all():
            return _(u"Not paid")
        else:
            return _(u"Payment attempt, but not fully paid\nPaid: %(total)s\n%(errors)s" % {'total': total, 'errors': s})
    
    class Meta:
        verbose_name, verbose_name_plural = _("order"), _("orders")
    
    def total(self):
        total = Decimal(0)
        for item in self.orderline_set.all():
            total = total + item.total()
        return total
        
    def balance(self):
        total = Decimal(0)
        for payment in self.orderpayment_set.all():
            total += payment.amount
        balance = self.total() - total
        return balance
        
    def vat(self):
        return (self.total() * Decimal("0.2"))
    
    @models.permalink
    def url(self):
        return ('order_detail', (self.id,), {})
    get_absolute_url = url
    
    def __unicode__(self):
        return u"F%0.3d" % (self.id, )
    
class OrderLine(models.Model):
    order = models.ForeignKey(Order)
    item_id = models.IntegerField(blank=True, null=True, verbose_name=_(u"item id"))
    fee_id = models.IntegerField(blank=True, null=True, verbose_name=_(u"fee id"))
    name = models.CharField(max_length=80, verbose_name=_(u"name"))
    amount = models.IntegerField(verbose_name=_(u"pieces"))
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name=_(u"price"))
    
    def __unicode__(self):
        return self.name
    
    def item(self):
        if self.item_id:
            return Item.objects.get(pk=self.item_id)
        else:
            return None
    
    def delivered(self):
        amount = 0
        for delivery in self.deliveryline_set.all():
            amount += delivery.amount
        return amount
    
    def total(self):
        return (self.price * self.amount)
    
    class Meta:
        verbose_name, verbose_name_plural = _("order line"), _("order lines")

class OrderPayment(models.Model):
    order = models.ForeignKey(Order, verbose_name=_(u"order"))
    gateway = models.CharField(max_length=128, choices=default_settings.PAYMENT_GATEWAYS, verbose_name=_(u"gateway"))
    transaction_id = models.CharField(max_length=128, verbose_name=_(u"transaction id"))
    date = models.DateTimeField(verbose_name=_(u"date"))
    amount = models.DecimalField(max_digits=8, decimal_places=2, verbose_name=_(u"amount"))
    full_name = models.CharField(max_length=128, blank=True, verbose_name=_(u"full name"))
    
class OrderFailedPayment(models.Model):
    order = models.ForeignKey(Order, verbose_name=_(u"order"))
    gateway = models.CharField(max_length=128, choices=default_settings.PAYMENT_GATEWAYS, verbose_name=_(u"gateway"))
    error_code = models.IntegerField(blank=True, null=True, verbose_name=_(u"error code"))
    error_text = models.TextField(blank=True, verbose_name=_(u"error text"))

class OrderMessage(models.Model):
    order = models.ForeignKey(Order, verbose_name=_(u"order"))
    gateway = models.CharField(max_length=128, choices=default_settings.MSG_GATEWAYS, verbose_name=_(u"gateway"))
    message = models.TextField(verbose_name=_(u"message"))
    is_send = models.BooleanField(verbose_name=_(u"is send?"))
    received_error = models.BooleanField(verbose_name=_(u"received error?"))
    date = models.DateTimeField(verbose_name=_(u"date"), default=datetime.datetime.now())
    
    class Meta:
        verbose_name, verbose_name_plural = _("order message"), _("order messages")
    
    def save(self, *args, **kwargs):
        if self.is_send == False and self.received_error == False:
            self.send()
        else:
            super(OrderMessage, self).save(*args, **kwargs)
    
    def send(self):
        gateway = self.gateway.split(".")
        message = getattr(__import__(".".join(gateway[:-1]), globals(), locals(), [gateway[-1]], -1), gateway[-1])(self)
        if message.sendmessage():
            self.is_send = True
            self.received_error = False
        else:
            self.is_send = False
            self.received_error = True
        self.save()

class Delivery(models.Model):
    order = models.ForeignKey(Order)
    trackingnumber = models.CharField(max_length=80, blank=True)
    comments = models.TextField(blank=True)
    send = models.DateTimeField(blank=True, null=True)
    
class DeliveryLine(models.Model):
    delivery = models.ForeignKey(Delivery)
    orderline = models.ForeignKey(OrderLine)
    amount = models.IntegerField()