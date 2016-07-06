__author__ = 'mhebel'
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Blueprint, render_template, flash, request, redirect, url_for,session
from flask import current_app
from twilio.rest import TwilioRestClient
from partytxt.models import User, People, SMSLog, VoiceMailBox,VoiceStats

import re, os, time, requests
import twilio.twiml

## Ask to record a message, listen to new messages, popular messages
## New messages are recordings not her by you
## Popular messages are new recordings that are up voted
## TODO add important voice messages that alert group memebers of the voicemail

db = SQLAlchemy()
voice = Blueprint('voice', __name__)

@voice.route('/voice_menu',methods=['GET','POST'])
def voice_menu():
    resp = twilio.twiml.Response()

    from_number = request.values.get('From',None)
    call_sid = request.values.get("CallSid")


    caller = People.query.filter(People.number == from_number).first()



    if caller is None:
        resp.reject()
        return str(resp)

    #initial voice mail - if hang up occurs we have a log
    voice_mail = VoiceMailBox(caller.id,0,None,call_sid)
    db.session.add(voice_mail)
    log = SMSLog(from_=from_number,body="voice mail",name=caller.name,murls=None,type ='voice',sid = call_sid)
    db.session.add(log)
    db.session.commit()

    resp.say("Hello " + caller.name)

    with resp.gather(numDigits=1,action="/handle-key",methods="POST") as g:
        g.say("Press 1 to record a 15 second message. Press 2 to listen to new messages. Press 3 to listen to top 3 messages.")

    return str(resp)

@voice.route('/handle-key',methods=['GET','POST'])
def key_handler():
    digit_pressed = request.values.get("Digits")

    if digit_pressed == "1":
        resp = twilio.twiml.Response()
        resp.say("Record your message after the beep, press any key to end recording")
        resp.record(maxLength="15",action='/handle-recording')
        resp.gather().say("A message was not received,press any key to try again") # might need to change to press 1 or redirect
        return str(resp)
    elif digit_pressed == "2" or digit_pressed == "3":
        resp = twilio.twiml.Response()
        resp.redirect('/listen?message_type='+digit_pressed)
        return str(resp)
    else:
        return redirect('/voice_menu')


@voice.route('/handle-recording',methods=['GET','POST'])
def record_message():
    audio_url = request.values.get('RecordingUrl',None)
    from_number = request.values.get('From',None)
    call_sid = request.values.get("CallSid")
    #could combine these queries
    caller = People.query.filter(People.number == from_number).first()
    vm = db.session.query(VoiceMailBox).filter(VoiceMailBox.call_sid == call_sid).first()
    vm.audio_url = audio_url
    vm.status = 1 # have a url


    log = db.session.query(SMSLog).filter(SMSLog.sid == call_sid).first()
    log.media_urls = audio_url

    db.session.commit()

    resp = twilio.twiml.Response()
    resp.say("Message recorded")
    resp.say("Bye")
    resp.hangup()


    #download mp3
    mp3 = request.values.get("CallSid")+".mp3"
    file_name = "%s/partytxt/static/voicemail/%s" %(os.getcwd(),mp3)
    try:
        f = open(file_name,'wb')
        f.write(requests.get(audio_url+".mp3").content)
        f.close()
        ## clean up recording
        ## only delete if download success use hooks?
        recording_sid = audio_url.split("/Recordings/")[1]
        client = TwilioRestClient(current_app.config['TWILIO_SID'],current_app.config['TWILIO_TOKEN'])
        #client.recordings.delete(recording_sid) ## put this in a routine
    except requests.exceptions.RequestException as e:
        pass

    return str(resp)

@voice.route('/listen',methods=['GET','POST'])
def listen():

    current_message = request.values.get('current_msg',0)

    from_number =  request.values.get('From',None)

    first = current_message == 0

    digit = request.values.get('Digits',None)

    #all the messages not listened by me
    #make archive later
    person = People.query.filter(People.number == from_number).first()

    if person is None:
        resp = twilio.twiml.Response()
        resp.say("Unknown person")
        resp.hangup()
        return str(resp)

    if request.values.get('message_type') == 3:
        msgs = db.session.query(VoiceMailBox).join(VoiceStats).filter(VoiceStats.listened_by != person.name, VoiceMailBox.people_id != person.id).order_by(VoiceMailBox.vote_count.desc()).limit(3).all() # change query to get the top 3 popular.
    else:
        #don't listen to voice mails i made and ones I've already heard
        msgs = db.session.query(VoiceMailBox).join(VoiceStats).filter(VoiceStats.listened_by != person.name, VoiceMailBox.people_id != person.id).all()

    if current_message > len(msgs):
        resp = twilio.twiml.Response()
        resp.say("No more messages")
        resp.say("Bye!")
        resp.hangup()
        return str(resp)

    message = msgs[current_message]

    ## process digits


    if digit is not None:
        if digit == 1:
            pass # skip
        elif digit == 2:
            #mark give up vote
            ## bug - can upvote multiple messages
            message.vote_count = message.vote_count + 1
            db.session.commit()


        current_message = current_message + 1

    resp = twilio.twiml.Response()

    with resp.gather(numDigits = 1,action='/listen?current_msg='+str(current_message)+'&message_type='+request.values.get('message_type'),timeout=5) as g:
        if first:
            if request.values.get('message_type') == 2:
                g.say("Press 1 to skip, 2 to up vote")
            else:
                g.say("Press 1 to skip")
        else:
            g.say("Next Message")

        g.say(person.name+" left this beauty.")
        if 'http' in message.audio_url or 'https' in message.audio_url:
            g.play(message.audio_url)
        else:
            g.play(url_for('static',filename='voicemail/'+message.call_sid+'.mp3',_external=True))
        #mark as played
        #plays next message
        Vs = VoiceStats(message.id,person.name)
        db.session.add(Vs)
        db.session.commit()
        resp.redirect("/listen?current_message="+str(current_message)+"&Digits=1&message_type="+request.values.get('message_type'))

    return str(resp)
