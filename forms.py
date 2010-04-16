from django import forms
from models import Order
from django.utils.translation import ugettext_lazy as _

class OrderForm(forms.ModelForm):
    remember_my_address = forms.BooleanField(label=_("Remember information"), required=False)
    
    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
    
    def clean_terms_accepted(self):
        data = self.cleaned_data['terms_accepted']
        if not data:
            raise forms.ValidationError(_(u"Your forgot to accept our terms"))
        return data
    
    class Meta:
        model = Order
        exclude = ('paid', 'delivered', 'site')