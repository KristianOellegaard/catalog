from django.contrib import admin
from models import *
from django.contrib import databrowse
from django.forms import ModelForm
from django import forms

class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('__unicode__', 'amount_sold', 'amount_on_stock')
    filter_horizontal = ('related_items', )
    
class SubItemAdmin(ItemAdmin):
    prepopulated_fields = {"slug": ("name", "variant_title")}

admin.site.register(MainItem, ItemAdmin)
admin.site.register(SubItem, SubItemAdmin)
admin.site.register(SubItemType)

class CategoryAdmin(admin.ModelAdmin):
    
    list_display = ('name', 'sites_display')
    list_filter = ('sites',)
    search_fields = ['name']
    prepopulated_fields = {"slug": ("name",)}

admin.site.register(Category, CategoryAdmin)
admin.site.register(Fee)
admin.site.register(OrderFee)

class OrderPaymentInline(admin.TabularInline):
    model = OrderPayment
    extra = 0
    template = 'admin/catalog/inline.html'
    
class OrderLineInline(admin.TabularInline):
    model = OrderLine
    fields = ('name', 'amount', 'price')

class OrderFailedPaymentInline(admin.TabularInline):
    model = OrderFailedPayment
    extra = 0
    template = 'admin/catalog/inline.html'
    
class OrderMessageInline(admin.TabularInline):
    model = OrderMessage
    extra = 0
    template = 'admin/catalog/inline.html'
    fields = ('message', 'is_send', 'received_error', 'date')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'paid', 'delivered', 'get_full_name', 'get_payments', 'total')
    inlines = [OrderLineInline, OrderMessageInline, OrderPaymentInline, OrderFailedPaymentInline]

admin.site.register(Order, OrderAdmin)

class DeliveryLineModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(DeliveryLineModelForm, self).__init__(*args, **kwargs)
        try:
            if 'instance' in kwargs:
                order = kwargs['instance'].orderline.order
            else:
                order = tuple(i[0] for i in self.fields['delivery'].widget.choices)[1]
                order = Delivery.objects.get(pk=order)
                order = order.order
            self.fields['orderline'].queryset = OrderLine.objects.filter(order=order)
        except:
            self.fields["amount"] = forms.CharField( #Add room throws DoesNotExist error
                            widget=forms.HiddenInput,       
                            required=False,
                            label='Choose order and save delivery before adding lines')
            self.fields['orderline']=forms.CharField( #Add room throws DoesNotExist error
                            widget=forms.HiddenInput,       
                            required=False,
                            label='')

class DeliveryLineInline(admin.TabularInline):
    form = DeliveryLineModelForm
    model = DeliveryLine
    
class DeliveryAdmin(admin.ModelAdmin):
    inlines = [DeliveryLineInline]
admin.site.register(Delivery, DeliveryAdmin)

databrowse.site.register(Order)
databrowse.site.register(OrderPayment)