from database import db
from datetime import datetime

class Reminder(db.Model):
    __tablename__ = 'reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    reminder_type = db.Column(db.String(20), nullable=False) # '7_days', '3_days', '1_day', 'on_deadline'
    reminder_date = db.Column(db.DateTime, nullable=False)
    notification_type = db.Column(db.String(20), nullable=False, default='Email') # 'Email', 'WhatsApp', 'Both'
    sent = db.Column(db.Boolean, nullable=False, default=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    task = db.relationship('Task', back_populates='reminders')

    def __repr__(self):
        return f"<Reminder TaskId:{self.task_id} Type:{self.reminder_type} Sent:{self.sent}>"


class NotificationLog(db.Model):
    __tablename__ = 'notification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    recipient = db.Column(db.String(150), nullable=False) # Email address or Phone number
    channel = db.Column(db.String(20), nullable=False) # 'Email', 'WhatsApp'
    subject = db.Column(db.String(200), nullable=True) # Subject line for emails
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='notifications')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'recipient': self.recipient,
            'channel': self.channel,
            'subject': self.subject,
            'message': self.message,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f"<NotificationLog To:{self.recipient} Channel:{self.channel}>"
