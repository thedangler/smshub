from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import time

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String())
    password = db.Column(db.String())

    def __init__(self, username, password,email):
        self.username = username
        self.set_password(password)
        self.email = email

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, value):
        return check_password_hash(self.password, value)

    def is_authenticated(self):
        if isinstance(self, AnonymousUserMixin):
            return False
        else:
            return True

    def is_active(self):
        return True

    def is_anonymous(self):
        if isinstance(self, AnonymousUserMixin):
            return True
        else:
            return False

    def get_id(self):
        return self.id

    def __repr__(self):
        return '<User %r>' % self.username

#rename to person when you have the chance.
class People(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    name = db.Column(db.String())
    number = db.Column(db.String())
    status = db.Column(db.String(),default='inactive')
    update_date = db.Column(db.Integer())

    def __init__(self,name=None,number=None,status="inactive"):
        self.name = name
        self.number = number
        self.status = status
        self.update_date = int(time.time())


    def __repr__(self):
        return '<People %r - %r>' % (self.name,self.number)


class SMSLog(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    from_number = db.Column(db.String())
    body = db.Column(db.String())
    timestamp = db.Column(db.Integer())
    name = db.Column(db.String())
    media_urls = db.Column(db.Text())
    sid = db.Column(db.String())
    sms_type = db.Column(db.String()) #incoming outgoing voicemail


    def __init__(self,from_,body,name,murls=None,type ='incoming',sid=None):
        self.from_number = from_
        self.body = body
        self.name = name
        self.media_urls = murls
        self.sms_type = type
        self.timestamp = int(time.time())
        self.sid = sid


class VoiceMailBox(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    call_sid = db.Column(db.String())
    people_id = db.Column(db.Integer(),db.ForeignKey('people.id'))
    create_date = db.Column(db.Integer(), default = int(time.time()))
    status = db.Column(db.Integer(),default=0)
    audio_url = db.Column(db.String())
    vote_count = db.Column(db.Integer(), default = 0)

    def __init__(self,people_id,status,audio_url,sid,votes=0):
        self.people_id = people_id
        self.status = status
        self.audio_url = audio_url
        self.call_sid = sid
        self.vote_count = votes
    def __repr__(self):
        return '<Voice message %r>' % self.call_sid


class VoiceStats(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    message_id = db.Column(db.Integer(),db.ForeignKey('voice_mail_box.id'))
    listened_by = db.Column(db.String())
    update_date = db.Column(db.Integer(), default = int(time.time()))

    def __init__(self,msg_id,person):
        self.message_id = msg_id
        self.listened_by = person

    def __repr__(self):
        return '<Voice Stats %r>' % self.id