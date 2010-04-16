from catalog.gateways import MessageGateway, MessageGatewayNotConfigured
from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import ugettext as _


class EmailGateway(MessageGateway):
    def sendmessage(self):
        title = _(u"Your order - F%0.3d" % (self.message.order.id, ))
        message = self.message.message
        try:
            send_mail(title, message, settings.DEFAULT_FROM_EMAIL, [self.message.order.email])
            return True
        except:
            self.error = "Could not send email / connect to gateway"
            return False