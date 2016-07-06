__author__ = 'mhebel'
##testing push2
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Blueprint, render_template, flash, request, redirect, url_for
from flask import current_app
from twilio.rest import TwilioRestClient
from partytxt.models import User, People, SMSLog

import re, os, time, requests
import twilio.twiml

db = SQLAlchemy()
sms = Blueprint('sms', __name__)


@sms.route('/message',methods=['GET','POST'])
def message():
    client = TwilioRestClient(current_app.config['TWILIO_SID'],current_app.config['TWILIO_TOKEN'])

    sms_from = request.values.get("From")
    sms_to = request.values.get("To") # should be the twilio or plivo number
    sms_body = request.values.get("Body").strip()
    sms_id = request.values.get("MessageSid")
    sms_media = request.values.get("NumMedia")

    # run the command if found. Some respond back to sender with a msg some don't
    result = command(sms_body,sms_from)
    if result is not False:
        return result


    p = db.session.query(People).filter(People.number == sms_from).first()

    #don't know what to do here just yet. Unknown number but didn't type a JOIN.
    # should I Send the HELP command?
    if p is None:
        sms_in_error = SMSLog(from_=sms_from,body=sms_body,name='unknown person',murls=None,sid=sms_id,type="incoming")
        db.session.add(sms_in_error)
        db.session.commit()
        return '',204



    mms = []
    mms_type = []
    if int(sms_media) > 0:
        for i in range(int(sms_media)):
            mms.append(request.values.get("MediaURL%s" % (i+1),None))
            mms_type.append(request.values.get("MediaContentType%s" % (i+1),None))
            # download to server and upload to instagram


    #get People
    #if current_app.debug:
    #    the_gang = People.query.filter( People.status == 'active').all() # i want to see if its working.
    #else:
    #
    the_gang = People.query.filter(People.number != sms_from, People.status == 'active').all()
    sms_out_log = []
    for person in the_gang:
        new_body = "%s \n- %s" % (sms_body,p.name)
        txt = client.messages.create(body=new_body,to=person.number,from_=current_app.config['TWILIO_NUMBER'])
        sms_out_log.append(SMSLog(from_=current_app.config['TWILIO_NUMBER'],body=new_body,name=p.name,murls=None,type='outgoing'))

    for sms_log in sms_out_log:
        db.session.add(sms_log)

    db.session.commit()

    #put th is in a process with celery somehow
    #https://media.twiliocdn.com/ACd065d16ea6b9fa3260928fafb96e5f26/b1caf41ba978e53ef00a32b688ac5118?Expires=1431443338&AWSAccessKeyId=0BEFPVCP30D65040M6G2&Signature=CisWsNs%2FkfngSLFZELG%2F1gnRgzc%3D
    log_media_urls = ""
    img = ""
    for j in range(len(mms)):

        content_type = mms_type[j]

        if content_type is None:
            continue

        if(content_type == 'image/jpeg'):
            img = "%s%s.jpg" % (sms_id,j)
        if(content_type == 'image/gif'):
            img = "%s%s.gif" % (sms_id,j)
        if(content_type == 'image/png'):
            img = "%s%s.png" % (sms_id,j)

        log_media_urls = log_media_urls+img+","
        # turn this into a function to use with voice recording urls too
        file_name = "%s/partytxt/static/images/%s" %(os.getcwd(),img)

        try:

            response = requests.get(mms[j])
            f = open(file_name,'wb')
            f.write(response.content)
            f.close()
            #delete image from server.
            if len(mms) > 0:
                mms_delete = client.media(sms_id).list()
                for item in mms_delete:
                    client.messages.get(sms_id).media_list.delete(item.sid)

        except requests.exceptions.RequestException as e:
            sms_in = SMSLog(from_=sms_from,body='error saving image',name=p.name,murls=log_media_urls,sid=sms_id,type="error")
            db.session.add(sms_in)
            db.session.commit()

    sms_in = SMSLog(from_=sms_from,body=sms_body,name=p.name,murls=log_media_urls,sid=sms_id,type="incoming")
    db.session.add(sms_in)
    db.session.commit()


    return "", 200
# https://media.twiliocdn.com/ACd065d16ea6b9fa3260928fafb96e5f26/b2f0c973633c35e290ac9c68211f7153?Expires=1429974106&AWSAccessKeyId=0BEFPVCP30D65040M6G2&Signature=a%2BhwNAkljhoqVF2D6XBWgIFJQKA%3D


def response_message(p = None,the_message = None):
    msg = the_message
    if msg == None:
        msg = 'Kill it with FIRE!!'

    #log
    sms_out = SMSLog(from_=current_app.config['TWILIO_NUMBER'],body=msg,name=p.name,murls=None,type='outgoing')
    db.session.add(sms_out)
    db.session.commit()

    resp = twilio.twiml.Response()
    resp.message(msg)
    return str(resp)


def command(sms_body=None,from_=None):
    # process body here look for keyworks like JOIN,IGNORE,LEAVE,NAME
    #reply to that number

    p = db.session.query(People).filter(People.number == from_).first()

    command_run = False
    pattern = '^JOIN|IGNORE|LEAVE|NAME|WAKE|HELP|STOP|\\?'
    m = re.match(pattern,sms_body,re.IGNORECASE)
    action = None

    if m:
        action = m.group()
        #need a pin number for security
        if action == 'JOIN':
            # get their name from split
            if p is None:
                name = " ".join(sms_body.split()[1:3])
                p = People(name,from_,"active")
                db.session.add(p)
                db.session.commit()
                command_run = response_message(p,"Welcome!\nText ? to list commands. Msg&Data Rates May Apply.\nAdd group contact:\n"+url_for('static', filename="vcards/vegas2015.vcf",_external=True)+"\n To save costs don't use this for 1 on 1 convos.")
            else:
                command_run = response_message(p,"You are already in the group")

        if action == 'IGNORE' and p is not None:
            p.status = "ignore"
            p.update_date = int(time.time())
            db.session.commit()
            #send a message saying how to come back
            command_run = response_message(p,"Text WAKE to rejoin party! Msg&Data Rates May Apply")

        if (action == 'LEAVE' or action == 'STOP') and p is not None:
            db.session.delete(p)
            db.session.commit()
            command_run = '',204

        if action == 'NAME' and p is not None:
            name = " ".join(sms_body.split()[1:3])
            p.name = name
            p.update_date = int(time.time())
            db.session.commit()
            command_run = '',204

        if action == 'WAKE' and p is not None:
            p.status = "active"
            p.update_date = int(time.time())
            db.session.commit()
            command_run = '',204

        if action == 'HELP' or action  == '?':
            command_run = response_message(p,"Text JOIN yourname to join the group!\nIGNORE for quiet time\nLEAVE to leave the group\nNAME yourname to set your name\nWAKE to rejoin ignored party\nMsg&Data Rates May Apply")

    return command_run
