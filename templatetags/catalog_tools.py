from django import template
import locale
from django.utils.translation import ugettext_lazy as _
import catalog
try:
    locale.setlocale(locale.LC_ALL, 'da_DK')
except:
    locale.setlocale(locale.LC_ALL, 'da_DK.utf8')
register = template.Library()
 
 
@register.filter()
def currency(value):
    if value == 0:
        return _("free")
    elif value:
        return locale.currency(float(value), grouping=True)
    else:
        return value

@register.simple_tag
def option(attr, suffix=None, prefix=None):
    value = getattr(catalog.settings.options, attr, None)
    if prefix and value:
        value = prefix + value
    if suffix and value:
        value += suffix
    elif not value:
        value = ""
    return value
