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
    Dispatches a WhatsApp message. If Meta WhatsApp Cloud API is configured, sends via Graph API.
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

    api_token = os.getenv('WHATSAPP_API_TOKEN')
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    api_version = os.getenv('WHATSAPP_API_VERSION', 'v20.0')

    if api_token and phone_number_id:
        try:
            # Clean recipient phone: strip '+' and spaces, and 'whatsapp:' prefix if present
            to_number = recipient_phone.replace('whatsapp:', '').replace('+', '').replace(' ', '').replace('-', '')
            
            url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_number,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": body
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            if response.status_code in [200, 201]:
                print(f"[Notifications] Actual WhatsApp message successfully sent to {to_number}")
                return True
            else:
                print(f"[Notifications] Meta API error sending to {to_number}: {response.text}")
                return False
        except Exception as e:
            print(f"[Notifications] Meta WhatsApp exception: {e}")
            return False
    else:
        print(f"[Notifications] Simulation mode: WhatsApp message to {recipient_phone} saved to logs. (Configure Meta WhatsApp settings in .env to activate actual WhatsApp notifications)")
        return True

