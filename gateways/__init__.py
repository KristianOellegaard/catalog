from django import forms
from catalog.models import OrderPayment, Order

class PaymentGateway:
    payment_form = None
    order = None
    error = None
    
    def handle(self, request):
        pass
    
    def form(self, request):
        return render_to_response("catalog/payment/form.html", {'form': self.payment_form(), })
        
    def accept(self, request):
        return render_to_response("catalog/payment/accept.html")
        
    def denied(self, request):
        return render_to_response("catalog/payment/denied.html")
        
    def callback(self, request):
        pass
    
    def __init__(self, order):
        self.order = order

class MessageGateway:
    error = ""
    def __init__(self, messageobj):
        '''
        Takes a catalog.models.OrderMessage instance as 1st argument
        '''
        self.message = messageobj
        
class MessageGatewayNotConfigured(Exception):
    def __init__(self, value):
        self.value = value
        
    def __unicode__(self):
        return repr(self.value)