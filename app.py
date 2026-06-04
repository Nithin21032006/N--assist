import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS

from database import db
from config import Config
from models import User, Task, Reminder, NotificationLog
from helpers import recreate_reminders_for_task, start_scheduler_thread, send_email

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Bind database
db.init_app(app)

# Decorator to enforce authentication
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- WEB VIEWS CONTROLLER ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not name or not email or not password:
            flash('Please fill in all required fields.', 'error')
        elif password != confirm_password:
            flash('Passwords do not match.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'error')
        else:
            new_user = User(name=name, email=email, phone=phone)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Successfully logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # Send simulated email
            reset_link = url_for('reset_password_token', token=token, _external=True)
            subject = "N-Assist Password Reset Request"
            body = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: auto; background-color: #0f172a; color: #f8fafc; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08);">
                <h2 style="color: #a855f7; text-align: center;">N-Assist Password Reset</h2>
                <p>Hello {user.name},</p>
                <p>You requested a password reset for your N-Assist account. Click the button below to set a new password. This link is valid for 1 hour.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background: linear-gradient(135deg, #a855f7, #6366f1); color: #fff; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; display: inline-block;">Reset Password</a>
                </div>
                <p style="font-size: 0.9em; color: #94a3b8;">If you didn't request this, you can safely ignore this email.</p>
                <p style="font-size: 0.8em; color: #64748b; margin-top: 20px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px;">Link URL: {reset_link}</p>
            </div>
            """
            send_email(user, subject, body)
            flash('Password reset link has been sent to your email. Check system logs if SMTP is offline.', 'success')
        else:
            flash('Email address not found.', 'error')
            
    return render_template('reset_password.html', token=None)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash('Invalid or expired password reset link.', 'error')
        return redirect(url_for('reset_password_request'))
        
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
        elif password != confirm_password:
            flash('Passwords do not match.', 'error')
        else:
            user.set_password(password)
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            flash('Your password has been reset successfully! Please log in.', 'success')
            return redirect(url_for('login'))
            
    return render_template('reset_password.html', token=token)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/tasks')
@login_required
def tasks():
    return render_template('tasks.html')

@app.route('/todo')
@login_required
def todo():
    return render_template('todo.html')

@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

@app.route('/system-logs')
@login_required
def system_logs():
    return render_template('system_logs.html')


# --- JSON API ENDPOINTS ---

@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def api_dashboard_stats():
    user_id = session['user_id']
    now = datetime.utcnow()
    
    # Refresh all task priorities dynamically
    all_tasks = Task.query.filter_by(user_id=user_id).all()
    for t in all_tasks:
        t.update_priority()
    db.session.commit()

    total_tasks = len(all_tasks)
    pending_tasks = Task.query.filter_by(user_id=user_id, status='Pending').count()
    completed_tasks = Task.query.filter_by(user_id=user_id, status='Completed').count()
    
    # Overdue tasks: Pending tasks with deadline in the past
    overdue_tasks = Task.query.filter(
        Task.user_id == user_id,
        Task.status == 'Pending',
        Task.deadline < now
    ).count()
    
    # Tasks due today (UTC calendar day)
    start_of_today = datetime(now.year, now.month, now.day, 0, 0, 0)
    end_of_today = datetime(now.year, now.month, now.day, 23, 59, 59)
    tasks_due_today = Task.query.filter(
        Task.user_id == user_id,
        Task.deadline >= start_of_today,
        Task.deadline <= end_of_today
    ).count()
    
    # Upcoming tasks: Pending tasks due after today
    upcoming_deadlines = Task.query.filter(
        Task.user_id == user_id,
        Task.status == 'Pending',
        Task.deadline > end_of_today
    ).count()

    # Get up to 5 upcoming deadlines
    upcoming_list = Task.query.filter(
        Task.user_id == user_id,
        Task.status == 'Pending',
        Task.deadline >= now
    ).order_by(Task.deadline.asc()).limit(5).all()

    return jsonify({
        'total': total_tasks,
        'pending': pending_tasks,
        'completed': completed_tasks,
        'overdue': overdue_tasks,
        'due_today': tasks_due_today,
        'upcoming': upcoming_deadlines,
        'upcoming_list': [t.to_dict() for t in upcoming_list],
        'using_mysql': app.config.get('USING_MYSQL', False),
        'using_postgres': app.config.get('USING_POSTGRES', False)
    })

@app.route('/api/tasks', methods=['GET', 'POST'])
@login_required
def api_tasks():
    user_id = session['user_id']
    
    if request.method == 'GET':
        # Retrieve filters from query parameters
        category = request.args.get('category')
        priority = request.args.get('priority')
        status = request.args.get('status')
        search = request.args.get('search')
        
        query = Task.query.filter_by(user_id=user_id)
        
        if category:
            query = query.filter_by(category=category)
        if priority:
            query = query.filter_by(priority=priority)
        if status:
            if status == 'Overdue':
                query = query.filter(Task.status == 'Pending', Task.deadline < datetime.utcnow())
            else:
                query = query.filter_by(status=status)
        if search:
            query = query.filter(Task.title.like(f"%{search}%") | Task.description.like(f"%{search}%"))
            
        tasks = query.order_by(Task.deadline.asc()).all()
        return jsonify([t.to_dict() for t in tasks])
        
    elif request.method == 'POST':
        data = request.json or {}
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', '').strip()
        deadline_str = data.get('deadline', '')
        
        if not title or not category or not deadline_str:
            return jsonify({'error': 'Title, category, and deadline are required'}), 400
            
        try:
            deadline = datetime.fromisoformat(deadline_str.replace('Z', ''))
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use ISO format.'}), 400
            
        new_task = Task(
            user_id=user_id,
            title=title,
            description=description,
            category=category,
            deadline=deadline
        )
        # Set priority automatically based on deadline
        new_task.update_priority()
        
        db.session.add(new_task)
        db.session.commit()
        
        # Build notification schedule for task
        recreate_reminders_for_task(new_task)
        
        return jsonify(new_task.to_dict()), 201

@app.route('/api/tasks/<int:task_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_task_detail(task_id):
    user_id = session['user_id']
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
    
    if request.method == 'GET':
        return jsonify(task.to_dict())
        
    elif request.method == 'PUT':
        data = request.json or {}
        task.title = data.get('title', task.title).strip()
        task.description = data.get('description', task.description).strip()
        task.category = data.get('category', task.category).strip()
        task.status = data.get('status', task.status)
        
        deadline_str = data.get('deadline')
        if deadline_str:
            try:
                task.deadline = datetime.fromisoformat(deadline_str.replace('Z', ''))
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
                
        # Re-evaluate priority automatically
        task.update_priority()
        db.session.commit()
        
        # Recreate reminders for new deadline
        recreate_reminders_for_task(task)
        
        return jsonify(task.to_dict())
        
    elif request.method == 'DELETE':
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'})

@app.route('/api/tasks/<int:task_id>/toggle', methods=['POST'])
@login_required
def api_task_toggle(task_id):
    user_id = session['user_id']
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
    
    task.status = 'Completed' if task.status == 'Pending' else 'Pending'
    db.session.commit()
    return jsonify(task.to_dict())

@app.route('/api/analytics/data', methods=['GET'])
@login_required
def api_analytics_data():
    user_id = session['user_id']
    tasks = Task.query.filter_by(user_id=user_id).all()
    
    # 1. Completion Rate
    completed_count = sum(1 for t in tasks if t.status == 'Completed')
    total_count = len(tasks)
    completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0
    
    # 2. Tasks by Category
    categories = ['Assignment', 'Hackathon', 'Workshop', 'Exam', 'Project', 'Certification', 'Personal']
    category_data = {cat: 0 for cat in categories}
    for t in tasks:
        if t.category in category_data:
            category_data[t.category] += 1
            
    # 3. Monthly Productivity (Completed tasks over current year's months)
    current_year = datetime.utcnow().year
    monthly_data = [0] * 12 # Index 0 = Jan, 11 = Dec
    for t in tasks:
        if t.status == 'Completed':
            # Fallback to created_at if completed_at doesn't exist
            # For simplicity, we can assume tasks completed were finished near the deadline or created month.
            # Let's count them by their deadline month for current year
            if t.deadline.year == current_year:
                monthly_data[t.deadline.month - 1] += 1

    # 4. Weekly Activity Chart (Tasks completed by weekday)
    # We can simulate/calculate this from tasks completed in the last 7 days
    now = datetime.utcnow()
    last_week = now - timedelta(days=7)
    weekly_activity = [0] * 7 # Mon=0, Tue=1 ... Sun=6
    for t in tasks:
        if t.status == 'Completed' and t.deadline >= last_week:
            # Get weekday integer (0-6)
            weekly_activity[t.deadline.weekday()] += 1

    return jsonify({
        'completion_rate': round(completion_rate, 1),
        'total_tasks': total_count,
        'completed_tasks': completed_count,
        'pending_tasks': total_count - completed_count,
        'category_data': category_data,
        'monthly_data': monthly_data,
        'weekly_activity': weekly_activity
    })

@app.route('/api/logs', methods=['GET'])
@login_required
def api_logs():
    user_id = session['user_id']
    logs = NotificationLog.query.filter_by(user_id=user_id).order_by(NotificationLog.created_at.desc()).all()
    return jsonify([l.to_dict() for l in logs])

@app.route('/api/logs/clear', methods=['POST'])
@login_required
def api_clear_logs():
    user_id = session['user_id']
    NotificationLog.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({'message': 'Logs cleared successfully'})


# --- SIMULATED AI HELPER ROUTE ---

def get_simulated_ai_response(user, message):
    msg = message.lower()
    tasks = Task.query.filter_by(user_id=user.id, status='Pending').all()
    for t in tasks:
        t.update_priority()
    
    high_tasks = [t for t in tasks if t.priority == 'High']
    med_tasks = [t for t in tasks if t.priority == 'Medium']
    
    # 1. Study Planner request
    if 'plan' in msg or 'study' in msg or 'schedule' in msg:
        if not tasks:
            return f"Hi {user.name}! I scanned your dashboard and you currently have no pending tasks. It's a great time to review past notes, set learning goals, or start a new personal project/certification!"
            
        response = f"### 📅 Custom AI Study & Priority Planner for {user.name}\n\n"
        response += "Here is your suggested study plan based on your current deadlines and priorities:\n\n"
        
        step = 1
        if high_tasks:
            response += f"**Phase 1: Urgent Action (High Priority)**\n"
            for t in high_tasks[:3]:
                due_in = (t.deadline - datetime.utcnow()).days
                due_label = f"due in {due_in} days" if due_in > 0 else "DUE TODAY" if due_in == 0 else "OVERDUE!"
                response += f"- **Step {step}:** Allocate 2-3 hours to work on **{t.title}** ({t.category}). It is {due_label}.\n"
                step += 1
            response += "\n"
            
        if med_tasks:
            response += f"**Phase 2: Steady Progress (Medium Priority)**\n"
            for t in med_tasks[:2]:
                response += f"- **Step {step}:** Block 1-2 hours for **{t.title}** ({t.category}). Review draft notes and outlines to avoid last-minute stress.\n"
                step += 1
            response += "\n"
            
        response += "**Pro Study Tip:** Use the *Pomodoro Technique* (50 minutes study, 10 minutes break). Make sure to mark tasks as completed in N-Assist to keep your scheduler updated!"
        return response

    # 2. Prioritization request
    elif 'prioritize' in msg or 'priority' in msg or 'urgent' in msg:
        if not tasks:
            return f"Hi {user.name}, you have 0 pending tasks! No prioritization is required. Enjoy your free time!"
            
        response = f"### ⚡ AI Prioritization Report\n\n"
        response += f"You have **{len(tasks)}** total pending tasks. Here are the items requiring your immediate attention:\n\n"
        
        if high_tasks:
            response += "🔴 **Critical (High Priority) - Do these first:**\n"
            for t in high_tasks:
                response += f"- **{t.title}** (Category: {t.category}) | Due: {t.deadline.strftime('%b %d, %Y')}\n"
        else:
            response += "🟢 No critical (High Priority) tasks due in the next 48 hours. Nice job!\n"
            
        if med_tasks:
            response += "\n🟡 **Important (Medium Priority) - Plan for this week:**\n"
            for t in med_tasks:
                response += f"- **{t.title}** (Category: {t.category}) | Due: {t.deadline.strftime('%b %d, %Y')}\n"
                
        return response
        
    # 3. Workload Prediction request
    elif 'workload' in msg or 'stress' in msg or 'predict' in msg:
        if len(tasks) > 7:
            return f"⚠️ **High Workload Detected!** You have {len(tasks)} pending tasks, with {len(high_tasks)} marked as High Priority. My prediction model flags this week as highly stressful. I suggest pushing personal tasks back and focusing strictly on assignments and exams."
        elif len(tasks) > 3:
            return f"📊 **Moderate Workload.** You have {len(tasks)} pending tasks. Your workload is balanced. Spacing out your project reviews and workshop tasks over 4 days will keep your stress levels low."
        else:
            return f"✅ **Light Workload.** You have only {len(tasks)} tasks. Your workload prediction is green. Excellent job staying ahead of your deadlines!"
            
    # 4. Default Chatbot response
    else:
        return (
            f"Hello {user.name}! I am your N-Assist AI Advisor. 🚀\n\n"
            f"I can help you with:\n"
            f"1. **Study Planner**: Type 'Give me a study plan' to get a structured schedule of your tasks.\n"
            f"2. **Task Prioritization**: Type 'How should I prioritize my tasks?' for an analysis of critical items.\n"
            f"3. **Workload Prediction**: Type 'What is my workload prediction?' to measure this week's task density.\n\n"
            f"How can I assist your productivity today?"
        )

@app.route('/api/ai/chat', methods=['POST'])
@login_required
def api_ai_chat():
    data = request.json or {}
    user_message = data.get('message', '').strip()
    user = User.query.get(session['user_id'])
    
    if not user_message:
        return jsonify({'error': 'Message is empty'}), 400
        
    response = get_simulated_ai_response(user, user_message)
    return jsonify({'response': response})


# --- APPLICATION STARTUP ---

# Run db creation and start background threads
with app.app_context():
    try:
        db.create_all()
        print("[Database] MySQL or SQLite Tables created successfully.")
    except Exception as e:
        print(f"[Database] Connection/creation error: {e}")

# Start background reminder daemon thread (only in the main worker process to avoid SQLite locking in debug mode)
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    start_scheduler_thread(app)


if __name__ == '__main__':
    # Run server locally on default port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
