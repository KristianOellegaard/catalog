from django.utils.translation import ugettext as _
import dbsettings

class Shop(dbsettings.Group):
	shop_name = dbsettings.StringValue(_("shop name"))
	shop_name_2 = dbsettings.StringValue(_("shop name 2"), required=False)

	address = dbsettings.TextValue(_("address"))
	extra_info = dbsettings.StringValue(_("extra information"))
	vat_no = dbsettings.StringValue(_("vat number"), required=False)
	
	terms_of_sale = dbsettings.TextValue(_("terms of sale"))

	payment = dbsettings.BooleanValue(_("enable payment"))

	merchant_number = dbsettings.StringValue(_("merchant id"), required=False)
	
	order_thanks = dbsettings.TextValue(_("Thank you text"), required=False)

options = Shop()

MSG_GATEWAYS = (
    ('catalog.gateways.sms.SMSGateway', 'SMS'),
    ('catalog.gateways.email.EmailGateway', 'E-Mail'),
)

MSG_GATEWAY_DEFAULT = "catalog.gateways.email.EmailGateway"

PAYMENT = options.payment or False

PAYMENT_GATEWAYS = (
    ('catalog.gateways.epay.Epay', 'Epay.dk'),
)

PAYMENT_GATEWAY_DEFAULT = "catalog.gateways.epay.Epay"
