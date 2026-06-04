import time
import threading
from datetime import datetime, timedelta
from database import db
from models.task import Task
from models.reminder import Reminder
from models.user import User
from helpers.notifications import send_email, send_whatsapp

def recreate_reminders_for_task(task):
    """
    Recalculates and populates the reminders table for a given task.
    Deletes existing unsent reminders first to handle deadline changes cleanly.
    """
    # Delete existing reminders first to overwrite
    Reminder.query.filter_by(task_id=task.id).delete()
    
    now = datetime.utcnow()
    deadline = task.deadline
    
    # 4 stages of alerts: 7 days before, 3 days before, 1 day before, and deadline day
    alert_times = [
        ('7_days', deadline - timedelta(days=7)),
        ('3_days', deadline - timedelta(days=3)),
        ('1_day', deadline - timedelta(days=1)),
        ('on_deadline', deadline)
    ]
    
    for alert_type, alert_date in alert_times:
        # Schedule the reminder only if its trigger date is in the future
        if alert_date > now:
            reminder = Reminder(
                task_id=task.id,
                reminder_type=alert_type,
                reminder_date=alert_date,
                notification_type='Both', # Sends both Email & WhatsApp by default if configured
                sent=False
            )
            db.session.add(reminder)
            
    db.session.commit()

def check_reminders(app):
    """
    Query database for due reminders and process them.
    Runs inside Flask app context.
    """
    with app.app_context():
        now = datetime.utcnow()
        # Fetch unsent reminders that are past their scheduled date
        due_reminders = Reminder.query.filter(
            Reminder.sent == False,
            Reminder.reminder_date <= now
        ).all()
        
        if not due_reminders:
            return
            
        print(f"[Scheduler] Processing {len(due_reminders)} due reminders at {now}")
        
        for reminder in due_reminders:
            task = Task.query.get(reminder.task_id)
            if not task:
                # Task has been deleted; skip
                reminder.sent = True
                continue
                
            if task.status == 'Completed':
                # Task already complete; no reminder needed
                reminder.sent = True
                continue
                
            user = User.query.get(task.user_id)
            if not user:
                reminder.sent = True
                continue
                
            # Format friendly alert details
            time_str = task.deadline.strftime("%Y-%m-%d %I:%M %p UTC")
            
            # Map type to friendly readable description
            type_descriptions = {
                '7_days': 'in 7 days',
                '3_days': 'in 3 days',
                '1_day': 'tomorrow',
                'on_deadline': 'today'
            }
            alert_label = type_descriptions.get(reminder.reminder_type, 'soon')
            
            # Compose HTML Email Body
            subject = f"N-Assist Alert: '{task.title}' is due {alert_label}!"
            email_body = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: auto; padding: 24px; background: #0f172a; color: #f8fafc; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08);">
                <div style="text-align: center; margin-bottom: 24px;">
                    <span style="font-size: 28px; font-weight: bold; background: linear-gradient(135deg, #a855f7, #6366f1); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">N-Assist</span>
                    <p style="color: #94a3b8; font-size: 14px; margin-top: 4px;">Your Personal Productivity & Deadline Assistant</p>
                </div>
                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; color: #f1f5f9; font-size: 18px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">{task.title}</h3>
                    <p style="margin: 10px 0; font-size: 14px;"><strong style="color: #94a3b8;">Category:</strong> {task.category}</p>
                    <p style="margin: 10px 0; font-size: 14px;"><strong style="color: #94a3b8;">Deadline:</strong> {time_str}</p>
                    <p style="margin: 10px 0; font-size: 14px;">
                        <strong style="color: #94a3b8;">Priority:</strong> 
                        <span style="padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; background-color: {'#fee2e2' if task.priority == 'High' else '#fef3c7' if task.priority == 'Medium' else '#d1fae5'}; color: {'#991b1b' if task.priority == 'High' else '#92400e' if task.priority == 'Medium' else '#065f46'};">{task.priority}</span>
                    </p>
                    <p style="margin: 10px 0; font-size: 14px;"><strong style="color: #94a3b8;">Alert Trigger:</strong> Task is due {alert_label}!</p>
                </div>
                {f'<p style="font-size: 14px; color: #cbd5e1; line-height: 1.6; margin-bottom: 20px;"><strong>Task Details:</strong> {task.description}</p>' if task.description else ''}
                <div style="text-align: center; margin-top: 28px;">
                    <a href="#" style="background: linear-gradient(135deg, #a855f7, #6366f1); color: #ffffff; text-decoration: none; padding: 10px 24px; border-radius: 8px; font-size: 14px; font-weight: 600; display: inline-block;">Open Dashboard</a>
                </div>
                <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.08); margin: 24px 0;">
                <p style="font-size: 12px; color: #64748b; text-align: center; margin: 0;">This is an automated notification. To disable notifications, adjust your settings in N-Assist.</p>
            </div>
            """
            
            # Compose WhatsApp Markdown Body
            whatsapp_body = (
                f"🚨 *N-Assist Deadline Alert* 🚨\n\n"
                f"Hi {user.name},\n"
                f"Your task *{task.title}* ({task.category}) is due soon!\n\n"
                f"📅 *Deadline:* {time_str}\n"
                f"⚡ *Priority:* {task.priority}\n"
                f"🔔 *Alert Status:* Due {alert_label}\n\n"
                f"Open N-Assist to update your task list!"
            )
            
            # Dispatch based on settings
            if reminder.notification_type in ['Email', 'Both']:
                send_email(user, subject, email_body, app)
                
            if reminder.notification_type in ['WhatsApp', 'Both'] and user.phone:
                send_whatsapp(user, whatsapp_body, app)
                
            # Flag reminder as sent
            reminder.sent = True
            reminder.sent_at = datetime.utcnow()
            
        db.session.commit()

def run_scheduler(app):
    """Loop runner for background reminders."""
    print("[Scheduler] Background reminder scheduler started.")
    while True:
        try:
            check_reminders(app)
        except Exception as e:
            print(f"[Scheduler] System Error inside checker loop: {e}")
        time.sleep(30) # Poll every 30 seconds

def start_scheduler_thread(app):
    """Launches the scheduler thread as a daemon."""
    scheduler_thread = threading.Thread(target=run_scheduler, args=(app,), daemon=True)
    scheduler_thread.start()
