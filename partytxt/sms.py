__author__ = 'mhebel3'

from twilio.rest import TwilioRestClient
from flask import current_app
import twilio.twiml
import plivo

class SMSAdapter(object):

    __provider = None

    def __init__(self,obj,**methods):
        self.obj = obj
        self.__provider = obj
        self.__dict__.update(methods)

    def __getattr__(self, item):
        return getattr(self.obj,item)

    ##diffirent implementation

    def reply(self,message):
        return self.__provider.reply(message)

    def send_sms(self,to,message):
        return self.__provider.send_sms(to,message)



class SMSTwilio(object):
    def __init__(self):
        self.client = TwilioRestClient(current_app.config['TWILIO_SID'],current_app.config['TWILIO_TOKEN'])
        self.twilio_number = current_app.config['TWILIO_NUMBER']
        self.name = "Twilio"


    def reply(self,message):
        resp = twilio.twiml.Response()
        resp.message(message)
        return str(resp)

    def send_sms(self,to,message):
        txt = self.client.messages.create(body=message,to=to,from_=self.twilio_number)
        return txt


class SMSPlivo(object):
    def __init__(self):
        self.client = plivo.RestAPI(current_app.config['PLIVO_AUTH'],current_app.config['PLIVO_TOKEN'])
        self.plivo_number = current_app.config['PLIVO_NUMBER']
        self.name = 'Plivo'


    def send_sms(self,to,message):
        return self.reply(to,message)

    def reply(self,to,message):
        """
        reply to the one number
        :param to: the recipent mobile number
        :param message: sms text
        :param from_: PLIVO number
        :return: 200
        """

        params = {
            'src' : self.plivo_number,'dst': to,'text':message,'type':'sms'

        }

        response = self.client.send_message(params)

        return response