from django.conf.urls.defaults import *
from catalog.models import Category, Item, Order
from django.contrib.auth.decorators import login_required
from django.contrib import databrowse

category_dict = {
    'queryset': Category.objects.all(),
}

item_dict = {
    'queryset': Item.objects.all(),
}

order_dict = {
    'queryset': Order.objects.all(),
}

urlpatterns = patterns('',
    # browse orders TODO: Create interface with databrowse
    #(r'^orders/(.*)', login_required(databrowse.site.root)),
    # checkout
    (r'^checkout/$', 'catalog.views.checkout', {}, 'checkout'),
    # payment
    (r'^pay/(?P<order_id>\d+)/$', 'catalog.views.pay', {}, 'pay'),
    (r'^pay/(?P<order_id>\d+)/accepted/$', 'catalog.views.pay_accepted', {}, 'pay_accepted'),
    (r'^pay/(?P<order_id>\d+)/denied/$', 'catalog.views.pay_denied', {}, 'pay_denied'),
    (r'^pay/(?P<order_id>\d+)/cb/$', 'catalog.views.pay_callback', {}, 'pay_callback'),
    # messages
    (r'^sms-service/$', 'catalog.views.sms', {}, 'sms-service'),
    # catalog
    (r'^$', 'django.views.generic.list_detail.object_list', category_dict, 'category_list'),
    (r'^order/(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', order_dict, 'order_detail'),
    (r'^(?P<slug>[\w, -]+)/$', 'django.views.generic.list_detail.object_detail', category_dict, 'category_detail'),
    (r'^(?P<category>[\w, -]+)/(?P<slug>[\w, -]+)/$', 'catalog.views.item_detail', item_dict, 'item_detail'),
    
    
    (r'^admin/packingslip/(?P<order_id>\d+)/$', 'catalog.views.packingslip', {}, 'packingslip'),
)
