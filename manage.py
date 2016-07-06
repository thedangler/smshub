#!/usr/bin/env python

import os

from flask.ext.script import Manager, Server
from flask.ext.script.commands import ShowUrls, Clean
from partytxt import create_app
from partytxt.sms import *
from partytxt.models import db, User, People, SMSLog,VoiceMailBox,VoiceStats

# default to dev config because no one should use this in
# production anyway
env = os.environ.get('PARTYTXT_ENV', 'dev')
app = create_app('partytxt.settings.%sConfig' % env.capitalize(), env=env)

manager = Manager(app)
manager.add_command("server", Server())
manager.add_command("show-urls", ShowUrls())
manager.add_command("clean", Clean())


@manager.shell
def make_shell_context():
    """ Creates a python REPL with several default imports
        in the context of the app
    """

    return dict(app=app, db=db, User=User, People=People,VoiceMailBox=VoiceMailBox,VoiceStats=VoiceStats,SMSLog=SMSLog)

@manager.command
def cleandb():
    db.drop_all()
    db.create_all()
    admin = User('admin','pass12345','test@example.com')
    db.session.add(admin)
    p3 = People("Chris","+15195558882",'inactive')
    p4 = People("Frank","+15195558883",'inactive')
    db.session.add_all((p3,p4))
    db.session.commit()


@manager.command
def createdb():
    """ Creates a database with all of the tables defined in
        your SQLAlchemy models
    """
    db.drop_all()
    db.create_all()

    admin = User('admin','pass12345','test@example.com')
    db.session.add(admin)

    people = People('Matt','+15196367784','active')
    p2 = People("Jim","+15195558881",'inactive')
    p3 = People("Chris","+15195558882",'active')
    p4 = People("Frank","+15195558883",'active')
    p5 = People("Karl","+15195558884",'active')
    p6 = People("Dave","+15195558885",'ignore')
    db.session.add(people)
    db.session.add(p2)
    db.session.add(p3)
    db.session.add(p4)
    db.session.add(p5)
    db.session.add(p6)
    db.session.commit()

    log1 = SMSLog(from_='+15195558883',body="JOIN Frank",name='Frank',murls=None,type ='JOIN')
    log2 = SMSLog(from_='+15195558883',body="Arrived, in room 2007 with bummer & hebel",name='Frank',murls=None,type ='incoming')
    log3 = SMSLog(from_='+15195558884',body="It smells like strippers and used dommer!!",name='Karl',murls=None,type ='incoming')
    log4 = SMSLog(from_='+15195558885',body="Dinner at Ruths tomorrow at 7pm",name='Dave',murls=None,type ='incoming')
    log5 = SMSLog(from_='+15195558881',body="Check these Titties out!!!",name='Jim',murls='sdff.jpg',type ='incoming')
    log6 = SMSLog(from_='+15195558883',body="Need players for BJ!!! Bring your green hat",name='Frank',murls=None,type ='incoming')
    log7 = SMSLog(from_='+15195558881',body="voice",name='Jim',murls='audio_url.com',type ='voice')
    log8 = SMSLog(from_='+15195558883',body="voice",name='Frank',murls='audio_url',type ='voice')
    log9 = SMSLog(from_='+15195558881',body=None,name='Jim',murls='sdfsdf.jpg',type ='incoming')
    log10 = SMSLog(from_='+15195558883',body=None,name='Frank',murls='sdfssf.jpg',type ='incoming')
    log11 = SMSLog(from_='+15195558881',body=None,name='Jim',murls='xchj.jpg',type ='incoming')

    db.session.add(log1)
    db.session.add(log2)
    db.session.add(log3)
    db.session.add(log4)
    db.session.add(log5)
    db.session.add(log6)
    db.session.add(log7)
    db.session.add_all((log8,log9,log10,log11))
    db.session.commit()

    vb = VoiceMailBox(p2.id,1,'sdfasf43534dsdfg.mp3','sdfasf43534dsdfg',votes=3)
    vb2 = VoiceMailBox(people.id,1,'sdfasfdfgsdfgdsf534dsdfg.mp3','sdfasfdfgsdfgdsf534dsdfg',votes=1)
    db.session.add_all((vb,vb2))
    db.session.commit()

    vbs = VoiceStats(msg_id=vb.id,person=p3.name)
    vbs2 = VoiceStats(msg_id=vb.id,person=people.name)
    vbs3 = VoiceStats(msg_id=vb.id,person=p4.name)
    vbs4 = VoiceStats(msg_id=vb.id,person=p6.name)
    vbs5 = VoiceStats(msg_id=vb2.id,person=p2.name)
    vbs6 = VoiceStats(msg_id=vb2.id,person=p6.name)
    db.session.add_all((vbs,vbs2,vbs3,vbs4,vbs5,vbs6))
    db.session.commit()



if __name__ == "__main__":
    manager.run()
