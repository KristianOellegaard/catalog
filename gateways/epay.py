# -*- coding: utf-8 -*-
'''
   Created by       prinkk
   Developer        Kristian Øllegaard
   Mail         kristian@prinkk.net
   www          http://www.prinkk.net

   Date         29 12 2009

   License      Copyright 2009 prinkk
   Filename     epay.py
'''

from catalog.gateways import PaymentGateway
from catalog.models import OrderPayment, OrderFailedPayment
from django import forms
from django.conf import settings
from catalog.settings import options
from django.shortcuts import render_to_response, redirect
import hashlib
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

class EpayForm(forms.Form):
    paymenttype = forms.IntegerField(initial=0, widget=forms.HiddenInput)
    merchantnumber = forms.IntegerField(initial=options.merchant_number, widget=forms.HiddenInput)
    orderid = forms.IntegerField(widget=forms.HiddenInput)
    currency = forms.IntegerField(widget=forms.HiddenInput, initial=getattr(settings, "EPAY_CURRENCY", "208"))
    amount = forms.IntegerField(widget=forms.HiddenInput)
    accepturl = forms.CharField(widget=forms.HiddenInput)
    declineurl = forms.CharField(widget=forms.HiddenInput)
    callbackurl = forms.CharField(widget=forms.HiddenInput)
    md5key = forms.CharField(widget=forms.HiddenInput)
    
    cardno = forms.IntegerField(label="Kortnummer", widget=forms.TextInput(attrs={'maxlength':'16'}))
    cardholder = forms.IntegerField(label="Kortindehavers navn")
    expmonth = forms.IntegerField(label="Måned", widget=forms.TextInput(attrs={'maxlength':'2'}))
    expyear = forms.IntegerField(label="År", widget=forms.TextInput(attrs={'maxlength':'2'}))
    cvc = forms.IntegerField(label="CVC", widget=forms.TextInput(attrs={'maxlength':'3'}))
    
    def update(self, order, request):
        
        def makeurl(absolute_url):
            if request.get_host() == "relay.ditonlinebetalingssystem.dk":
                return u'https://relay.ditonlinebetalingssystem.dk/relay/relay.cgi/%(domain)s%(path)s' % {
                    'domain': request.get_host(), 'path': absolute_url}
            else:
                return request.build_absolute_uri(absolute_url)
        
        self.fields["amount"].initial = int(order.total()*100)
        self.fields["orderid"].initial = order.id
        
        self.fields["accepturl"].initial = makeurl(reverse('pay_accepted', args=[order.id]))
        self.fields["declineurl"].initial = makeurl(reverse('pay_denied', args=[order.id]))
        self.fields["callbackurl"].initial = makeurl(reverse('pay_callback', args=[order.id]))
        
        # must be last!
        # currency + amount + ordreID + "fælles nøgle som er sat op i betalingssystemet"
        md5key = unicode(self.fields["amount"].initial)
        md5key += unicode(self.fields["amount"].initial)
        md5key += unicode(self.fields["orderid"].initial)
        md5key += unicode(settings.SECRET_KEY)
        self.fields["md5key"].initial = hashlib.md5(md5key).hexdigest()
        return self

class Epay(PaymentGateway):
    payment_form = EpayForm
    
    def handle(self, request):
        if not request.is_secure() and not settings.DEBUG and not request.GET.has_key("remote"):
            return redirect(u'https://relay.ditonlinebetalingssystem.dk/relay/relay.cgi/%(domain)s%(path)s?remote=True' % {
            'domain': request.get_host(), 'path': request.get_full_path()})
        if not options.merchant_number:
            raise Exception("No merchant number in dbsettings")
        return None
    
    def form(self, request):
        return render_to_response("catalog/payment/form.html", {'form': self.payment_form().update(self.order, request), 'order': self.order})
        
    def accepted(self, request):
        #?tid=2152400&orderid=1&amount=50000&cur=208&date=20091229&cardid=2&transfee=0
        if request.GET.has_key("tid"):
            o = OrderPayment(order=self.order, gateway="catalog.gateways.epay.Epay",\
            transaction_id=request.GET["tid"], amount=int(request.GET["amount"])/100,\
            date=u"%s-%s-%s" % (request.GET["date"][0:4], request.GET["date"][4:6], request.GET["date"][6:8]))
            o.save()
            return redirect("pay_accepted", self.order.id)
        return render_to_response("catalog/payment/accepted.html", {'order': self.order})
        
    def denied(self, request):
        if request.GET.has_key("error"):
            o = OrderFailedPayment(order=self.order, gateway="catalog.gateways.epay.Epay", error_code=request.GET["error"],\
            error_text=request.GET["errortext"])
            o.save()
            return redirect("pay_denied", self.order.id)
        return render_to_response("catalog/payment/denied.html")
        
    def callback(self, request):
        pass
