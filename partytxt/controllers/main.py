from flask import Blueprint, render_template, flash, request, redirect, url_for
from flask.ext.login import login_user, logout_user, login_required

from partytxt import cache
from partytxt.forms import LoginForm
from partytxt.models import *

main = Blueprint('main', __name__)


@main.route('/vegas15')
@cache.cached(timeout=1000)
def group():
    messages = SMSLog.query.filter(SMSLog.sms_type == 'incoming',SMSLog.media_urls == '').all()
    images = SMSLog.query.filter(SMSLog.media_urls != '', SMSLog.sms_type == 'incoming').all()
    all_images = []
    for img in images:
        all_images = all_images + img.media_urls.split(',')

    voice_messages = VoiceMailBox.query.join(People).with_entities(People.name,VoiceMailBox.call_sid,VoiceMailBox.vote_count).filter(VoiceMailBox.status > 0).order_by(VoiceMailBox.vote_count.desc()).all()
    return render_template('viewer.html',sms = messages,imgs = all_images,vm=voice_messages)

@main.route('/')
def about():
    return render_template('info.html')

@main.route('/info')
def help():
    return render_template('help.html')

@main.route('/random')
def test():
    return 'test',200

@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)

            flash("Logged in successfully.", "success")
            return redirect(request.args.get("next") or url_for(".home"))
        else:
            flash("Login failed.", "danger")

    return render_template("login.html", form=form)

@main.route("/insult")
def insult():
    return render_template("insult.html")


@main.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "success")

    return redirect(url_for(".home"))


@main.route("/restricted")
@login_required
def restricted():
    return "You can only see this if you are logged in!", 200


@main.route("/register_number")
def register_number():
    return "register a number by adding phone number, then putting in varification code.", 200

@main.route("/upload",methods=['POST'])
def upload_img():
    media_url = request.values.get('image_url')
    file_name = request.values.get('file_name')
    #download the image using filepicker-python
    #then delete
    l = SMSLog("website",file_name,"anonymous",media_url,'incoming',None)
    db.session.add(l)
    db.session.commit()
    return 'Upload Successful',200

