import logging
from logging.handlers import SMTPHandler

def email_on_error(app):
    if app.config['MAIL_SERVER'] == 'smtp.gmail.com':
        handler = TlsSMTPHandler
    else:
        handler = SMTPHandler
    mail_handler = handler((app.config['MAIL_SERVER'],
                            app.config['MAIL_PORT']),
                            app.config['MAIL_LOG_FROM'],
                           app.config['MAIL_LOG_ADMINS'],
                           app.config['MAIL_LOG_SUBJECT'],(app.config['MAIL_USER'],app.config['MAIL_PASS']))

    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter('''
        Message type:       %(levelname)s
        Location:           %(pathname)s:%(lineno)d
        Module:             %(module)s
        Function:           %(funcName)s
        Time:               %(asctime)s

        Message:

        %(message)s
    '''))
    app.logger.addHandler(mail_handler)

class TlsSMTPHandler(SMTPHandler):
    def emit(self, record):
        """
        Emit a record.

        Format the record and send it to the specified addressees.
        """
        try:
            import smtplib
            import string # for tls add this line
            try:
                from email.utils import formatdate
            except ImportError:
                formatdate = self.date_time
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port)
            msg = self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                            self.fromaddr,
                            string.join(self.toaddrs, ","),
                            self.getSubject(record),
                            formatdate(), msg)
            if self.username:
                smtp.ehlo() # for tls add this line
                smtp.starttls() # for tls add this line
                smtp.ehlo() # for tls add this line
                smtp.login(self.username, self.password)
            print 'sendmail'
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            print 'sent'
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
