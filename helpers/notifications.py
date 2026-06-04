import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import os
from database import db
from models.reminder import NotificationLog
from datetime import datetime

def send_email(user, subject, body, app=None):
    """
    Dispatches an email. If SMTP is configured, sends via smtp.
    Always logs to NotificationLog for simulation viewing.
    """
    # Create the log entry
    log = NotificationLog(
        user_id=user.id,
        recipient=user.email,
        channel='Email',
        subject=subject,
        message=body,
        created_at=datetime.utcnow()
    )
    
    # Save log to DB (handle application context if run from background scheduler thread)
    if app:
        with app.app_context():
            db.session.add(log)
            db.session.commit()
    else:
        db.session.add(log)
        db.session.commit()

    mail_server = os.getenv('MAIL_SERVER')
    mail_port = os.getenv('MAIL_PORT')
    mail_user = os.getenv('MAIL_USERNAME')
    mail_pass = os.getenv('MAIL_PASSWORD')
    mail_sender = os.getenv('MAIL_DEFAULT_SENDER', 'n-assist-no-reply@gmail.com')

    # If user has configured their email SMTP in .env, send the actual email
    if mail_user and mail_pass:
        try:
            msg = MIMEMultipart()
            msg['From'] = mail_sender
            msg['To'] = user.email
            msg['Subject'] = subject
            
            # Use HTML formatting for beautiful emails
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(mail_server, int(mail_port))
            server.starttls()
            server.login(mail_user, mail_pass)
            server.sendmail(mail_sender, user.email, msg.as_string())
            server.quit()
            print(f"[Notifications] Actual email successfully sent to {user.email}")
            return True
        except Exception as e:
            print(f"[Notifications] SMTP error sending to {user.email}: {e}")
            return False
    else:
        print(f"[Notifications] Simulation mode: Email to {user.email} saved to logs. (Configure SMTP settings in .env to activate actual emails)")
        return True

def send_whatsapp(user, body, app=None):
    """
    Dispatches a WhatsApp message. If Twilio is configured, sends via API.
    Always logs to NotificationLog for simulation viewing.
    """
    recipient_phone = user.phone
    if not recipient_phone:
        print(f"[Notifications] WhatsApp skipped for {user.name} - no phone number set.")
        return False
        
    log = NotificationLog(
        user_id=user.id,
        recipient=recipient_phone,
        channel='WhatsApp',
        subject=None,
        message=body,
        created_at=datetime.utcnow()
    )
    
    if app:
        with app.app_context():
            db.session.add(log)
            db.session.commit()
    else:
        db.session.add(log)
        db.session.commit()

    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER', 'whatsapp:+14155238886')

    if account_sid and auth_token:
        try:
            # Twilio WhatsApp numbers require a "whatsapp:" prefix
            to_number = recipient_phone
            if not to_number.startswith('whatsapp:'):
                to_number = f"whatsapp:{to_number}"
                
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            data = {
                "From": from_number,
                "To": to_number,
                "Body": body
            }
            response = requests.post(url, data=data, auth=(account_sid, auth_token))
            if response.status_code in [200, 201]:
                print(f"[Notifications] Actual WhatsApp message successfully sent to {recipient_phone}")
                return True
            else:
                print(f"[Notifications] Twilio API error sending to {recipient_phone}: {response.text}")
                return False
        except Exception as e:
            print(f"[Notifications] Twilio exception: {e}")
            return False
    else:
        print(f"[Notifications] Simulation mode: WhatsApp message to {recipient_phone} saved to logs. (Configure Twilio in .env to activate actual WhatsApp notifications)")
        return True
