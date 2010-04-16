# Create your views here.

from django.views.generic.list_detail import object_detail
from models import Item, OrderLine, OrderMessage, OrderFee, Order
from django.shortcuts import redirect, render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext
from decimal import Decimal
from forms import OrderForm
from django.http import HttpResponse, Http404
from catalog import settings as default_settings
from django.contrib.sites.models import Site
import random
from django.conf import settings
from settings import options

def item_detail(request, category, slug, *args, **kwargs):
    kwargs["queryset"] = kwargs["queryset"].filter(sites=Site.objects.get_current())
    if request.GET.has_key("basket_add"):
        item = Item.objects.get(slug=slug)
        if not request.session.has_key("basket"):
            request.session["basket"] = []
        exists = False
        for itm in request.session["basket"]:
            if itm["item"] == item:
                itm["amount"] += 1
                exists = True
        if not exists:
            request.session["basket"].append({'item': item, 'amount': 1})
        request.session.modified = True
        return redirect(item)
    return object_detail(request, *args, slug=slug, **kwargs)
    
def checkout(request):
    if not request.session.has_key("basket"):
        return redirect("category_list")
    elif request.GET.has_key("add_item"):
        item = Item.objects.get(pk=request.GET["add_item"])
        match = 0
        for itm in request.session["basket"]:
            if itm["item"] == item:
                itm["amount"] += 1
                match = 1
        if match == 0:
            request.session["basket"].append({'item': item, 'amount': 1})
        request.session.modified = True
        return redirect("checkout")
    elif request.GET.has_key("remove_item"):
        item = Item.objects.get(pk=request.GET["remove_item"])
        for itm in request.session["basket"]:
            if itm["item"] == item:
                itm["amount"] -= 1
                if itm["amount"] == 0:
                    request.session["basket"].remove(itm)
        if request.session["basket"] == []:
            del request.session["basket"]
        request.session.modified = True
        return redirect("checkout")
        
    basket = request.session["basket"] or []
    total = 0
    itms = []
    for itm in basket:
        itm["price"] = (itm["item"].price * itm["amount"])
        itm["fees"] = []
        itms.append(itm["item"])
        total = total + itm["price"]
        for fee in itm["item"].extra_fees.all():
            d = {
                'fee': fee,
                'price': (fee.price * itm["amount"])
            }
            itm["fees"].append(d)
            total = total + d["price"]
    # Add eventual fees to order
    for orderfee in OrderFee.objects.filter(applies_below__gt=total).order_by('price'):
        avoid = False
        avoid_item = None
        diff = (orderfee.applies_below - total)
        total = total + orderfee.price
        print diff
        if diff < 150 and diff > 0:
            try:
                avoid_item = Item.objects.filter(price__gte=(diff), price__lte=(diff+30))
                if avoid_item.filter(related_items__in=itms).count() > 0:
                    avoid_item = avoid_item.filter(related_items__in=itms)
                avoid_item = avoid_item[random.randrange(0,avoid_item.count())]
                avoid = True
            except:
                pass
        if diff > 0:
            basket.append({
                'price': orderfee.price,
                'amount': 1,
                'name': orderfee.name,
                'avoid': avoid,
                'avoid_fee': diff,
                'avoid_item': avoid_item,
                'item': None,
            })
    if request.POST:
        form = OrderForm(request.POST, instance=Order(site=Site.objects.get_current()))
        if form.is_valid():
            order = form.save()
            for itm in basket:
                if itm["item"]:
                    o = OrderLine(item_id=itm["item"].id, name=itm["item"].name, amount=itm["amount"], price=itm["item"].price, order=order)
                    o.save()
                    i = Item.objects.get(pk=itm["item"].id)
                    i.amount_on_stock -= itm["amount"]
                    i.amount_sold += itm["amount"]
                    i.save()
                    for fee in itm["item"].extra_fees.all():
                        o = OrderLine(fee_id=fee.id, name=fee.name, amount=itm["amount"], price=fee.price, order=order)
                        o.save()
                else:
                    o = OrderLine(name=itm["name"], amount=itm["amount"], price=itm["price"], order=order)
                    o.save()
            msg = render_to_string("catalog/order_confirmation.html", {
                'order': order,
                'site': Site.objects.get_current(),
            })
            OrderMessage(order=order, gateway=default_settings.MSG_GATEWAY_DEFAULT, message=msg).save()
            request.session.flush()
            if request.POST.has_key("remember_my_address"):
                request.session["first_name"] = order.first_name
                request.session["last_name"] = order.last_name
                request.session["address"] = order.address
                request.session["address_2"] = order.address_2
                request.session["postal_code"] = order.postal_code
                request.session["city"] = order.city
                request.session["cellphone"] = order.cellphone
                request.session["email"] = order.email
                request.session["remember_my_address"] = request.POST["remember_my_address"]
            if options.payment == True:
                return redirect("pay", order_id=order.id)
            return redirect(order)
    else:
        
        form = OrderForm(initial=request.session)
    dictionary = {
        'basket': basket,
        'total': total,
        'vat': total * Decimal("0.2"),
        'form': form,
    }
    
    return render_to_response('catalog/checkout.html',
                              dictionary,
                              context_instance=RequestContext(request))
                              
                              
                              
def sms(request):
    print request.GET["message"]
    print request.GET["mobile"]
    return HttpResponse("")
    
def pay(request, order_id):
    if options.payment == False:
        raise Http404("Payment disabled in dbsettings")
    order = Order.objects.get(pk=order_id)
    if order.paid:
        return redirect("category_list")
    gateway = default_settings.PAYMENT_GATEWAY_DEFAULT.split(".")
    gateway = getattr(__import__(".".join(gateway[:-1]), globals(), locals(), [gateway[-1]], -1), gateway[-1])(order)
    handle = gateway.handle(request)
    if handle:
        return handle
    return gateway.form(request)
    
def pay_accepted(request, order_id):
    order = Order.objects.get(pk=order_id)
    if not order.paid:
        msg = render_to_string("catalog/payment/callback_email.html", {
            'order': order,
            'site': Site.objects.get_current(),
        })
        OrderMessage(order=order, gateway=default_settings.MSG_GATEWAY_DEFAULT, message=msg).save()
    order.paid = True
    order.save()
    gateway = default_settings.PAYMENT_GATEWAY_DEFAULT.split(".")
    gateway = getattr(__import__(".".join(gateway[:-1]), globals(), locals(), [gateway[-1]], -1), gateway[-1])(order)
    handle = gateway.handle(request)
    if handle:
        return handle
    return gateway.accepted(request)
    
def pay_denied(request, order_id):
    order = Order.objects.get(pk=order_id)
    if order.paid:
        return redirect("category_list")
    gateway = default_settings.PAYMENT_GATEWAY_DEFAULT.split(".")
    gateway = getattr(__import__(".".join(gateway[:-1]), globals(), locals(), [gateway[-1]], -1), gateway[-1])(order)
    handle = gateway.handle(request)
    if handle:
        return handle
    return gateway.denied(request)
    
def pay_callback(request, order_id):
    order = Order.objects.get(pk=order_id)
    gateway = default_settings.PAYMENT_GATEWAY_DEFAULT.split(".")
    gateway = getattr(__import__(".".join(gateway[:-1]), globals(), locals(), [gateway[-1]], -1), gateway[-1])(order)
    handle = gateway.handle(request)
    return gateway.callback(request)
    
    
def packingslip(request, order_id):
    order = Order.objects.get(pk=order_id)
    return render_to_response("catalog/admin/packingslip.html", {'order': order})