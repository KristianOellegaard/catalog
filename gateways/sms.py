from catalog.gateways import MessageGateway, MessageGatewayNotConfigured
from django.conf import settings
import urllib

class SMSGateway(MessageGateway):
    def sendmessage(self):
        try:
            args = {
                'user': settings.SMSGATEWAY_USERNAME,
                'pass': settings.SMSGATEWAY_PASSWORD,
                'sender': settings.SMSGATEWAY_DISPLAY_NAME,
            }
        except AttributeError:
            raise MessageGatewayNotConfigured(value="Please provide SMS Gateway user, password and display name in settings.py")
        args['message'] = self.message.message
        args['mobile'] = u"45%s" % self.message.order.cellphone
        urlstr = ""
        for arg in args:
            urlstr += u"%s=%s&" % (arg, args[arg])
        try:
            response = urllib.urlopen("http://sms.stadel.dk/send.php", urlstr).read()
        except:
            self.error = "No connection to gateway"
            return False
        if response.split("|")[0] == "OK":
            self.error = ""
            return True
        else:
            self.error = response
            return False