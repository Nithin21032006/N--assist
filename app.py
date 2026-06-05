import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS

from database import db
from config import Config
from models import User, Task, Reminder, NotificationLog, AcademicTracker, Goal, Opportunity, UserOpportunity
from helpers import recreate_reminders_for_task, start_scheduler_thread, send_email
from helpers.opportunities_fetcher import OpportunityCrawler

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

@app.route('/academic-tracker')
@login_required
def academic_tracker():
    return render_template('academic_tracker.html')

@app.route('/goals')
@login_required
def goals():
    return render_template('goals.html')


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

    # Recommended Focus: Top 3 urgent tasks (Pending, sorted by deadline asc)
    focus_tasks = Task.query.filter_by(
        user_id=user_id,
        status='Pending'
    ).order_by(Task.deadline.asc()).limit(3).all()

    # Academic Tracker stats
    achievements = AcademicTracker.query.filter_by(user_id=user_id).all()
    academic_stats = {
        'Workshops': sum(1 for a in achievements if a.category == 'Workshop'),
        'Hackathons': sum(1 for a in achievements if a.category == 'Hackathon'),
        'Certifications': sum(1 for a in achievements if a.category == 'Certification'),
        'Seminars': sum(1 for a in achievements if a.category == 'Seminar')
    }

    # Active goals progress
    active_goals = Goal.query.filter_by(user_id=user_id, completed=False).order_by(Goal.deadline.asc()).limit(3).all()

    return jsonify({
        'total': total_tasks,
        'pending': pending_tasks,
        'completed': completed_tasks,
        'overdue': overdue_tasks,
        'due_today': tasks_due_today,
        'upcoming': upcoming_deadlines,
        'upcoming_list': [t.to_dict() for t in upcoming_list],
        'focus_list': [t.to_dict() for t in focus_tasks],
        'academic_stats': academic_stats,
        'active_goals': [g.to_dict() for g in active_goals],
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

# --- ACADEMIC TRACKER API ---

@app.route('/api/academic-tracker', methods=['GET', 'POST'])
@login_required
def api_academic_tracker():
    user_id = session['user_id']
    if request.method == 'GET':
        achievements = AcademicTracker.query.filter_by(user_id=user_id).order_by(AcademicTracker.date.desc()).all()
        return jsonify([a.to_dict() for a in achievements])
    elif request.method == 'POST':
        data = request.json or {}
        title = data.get('title', '').strip()
        category = data.get('category', '').strip()
        date_str = data.get('date', '')
        description = data.get('description', '').strip()
        
        if not title or not category or not date_str:
            return jsonify({'error': 'Title, category, and date are required'}), 400
            
        try:
            date_val = datetime.fromisoformat(date_str.replace('Z', ''))
        except ValueError:
            try:
                date_val = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
            
        achievement = AcademicTracker(
            user_id=user_id,
            title=title,
            category=category,
            date=date_val,
            description=description
        )
        db.session.add(achievement)
        db.session.commit()
        return jsonify(achievement.to_dict()), 201

@app.route('/api/academic-tracker/<int:achievement_id>', methods=['DELETE'])
@login_required
def api_academic_tracker_delete(achievement_id):
    user_id = session['user_id']
    achievement = AcademicTracker.query.filter_by(id=achievement_id, user_id=user_id).first_or_404()
    db.session.delete(achievement)
    db.session.commit()
    return jsonify({'message': 'Achievement deleted successfully'})

@app.route('/api/academic-tracker/stats', methods=['GET'])
@login_required
def api_academic_tracker_stats():
    user_id = session['user_id']
    achievements = AcademicTracker.query.filter_by(user_id=user_id).all()
    categories = ['Workshop', 'Certification', 'Hackathon', 'Seminar', 'Technical Event']
    stats = {cat: 0 for cat in categories}
    for a in achievements:
        if a.category in stats:
            stats[a.category] += 1
        else:
            stats[a.category] = stats.get(a.category, 0) + 1
    return jsonify(stats)


# --- GOAL TRACKING API ---

@app.route('/api/goals', methods=['GET', 'POST'])
@login_required
def api_goals():
    user_id = session['user_id']
    if request.method == 'GET':
        goals = Goal.query.filter_by(user_id=user_id).order_by(Goal.deadline.asc()).all()
        return jsonify([g.to_dict() for g in goals])
    elif request.method == 'POST':
        data = request.json or {}
        title = data.get('title', '').strip()
        target_value = data.get('target_value', 1)
        current_value = data.get('current_value', 0)
        deadline_str = data.get('deadline', '')
        
        if not title or not deadline_str:
            return jsonify({'error': 'Title and deadline are required'}), 400
            
        try:
            target_value = int(target_value)
            current_value = int(current_value)
        except ValueError:
            return jsonify({'error': 'Target and current values must be integers'}), 400
            
        if target_value <= 0:
            return jsonify({'error': 'Target value must be greater than zero'}), 400
            
        try:
            deadline = datetime.fromisoformat(deadline_str.replace('Z', ''))
        except ValueError:
            try:
                deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
            except ValueError:
                return jsonify({'error': 'Invalid deadline format'}), 400
            
        goal = Goal(
            user_id=user_id,
            title=title,
            target_value=target_value,
            current_value=current_value,
            deadline=deadline
        )
        if goal.current_value >= goal.target_value:
            goal.completed = True
            
        db.session.add(goal)
        db.session.commit()
        
        if goal.completed:
            user = User.query.get(user_id)
            log = NotificationLog(
                user_id=user_id,
                recipient=user.email,
                channel='Email',
                subject=f"🏆 Goal Achieved: {goal.title}!",
                message=f"Congratulations, {user.name}! You have achieved your goal: '{goal.title}' ({goal.current_value}/{goal.target_value})!",
                created_at=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
            
        return jsonify(goal.to_dict()), 201

@app.route('/api/goals/<int:goal_id>', methods=['PUT', 'DELETE'])
@login_required
def api_goal_detail(goal_id):
    user_id = session['user_id']
    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first_or_404()
    
    if request.method == 'PUT':
        data = request.json or {}
        goal.title = data.get('title', goal.title).strip()
        
        target_val = data.get('target_value', goal.target_value)
        current_val = data.get('current_value', goal.current_value)
        
        try:
            goal.target_value = int(target_val)
            goal.current_value = int(current_val)
        except ValueError:
            return jsonify({'error': 'Target and current values must be integers'}), 400
            
        deadline_str = data.get('deadline')
        if deadline_str:
            try:
                goal.deadline = datetime.fromisoformat(deadline_str.replace('Z', ''))
            except ValueError:
                try:
                    goal.deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
                except ValueError:
                    return jsonify({'error': 'Invalid date format'}), 400
                    
        was_completed = goal.completed
        if goal.current_value >= goal.target_value:
            goal.completed = True
        else:
            goal.completed = False
            
        db.session.commit()
        
        if goal.completed and not was_completed:
            user = User.query.get(user_id)
            log = NotificationLog(
                user_id=user_id,
                recipient=user.email,
                channel='Email',
                subject=f"🏆 Goal Achieved: {goal.title}!",
                message=f"Congratulations, {user.name}! You have achieved your goal: '{goal.title}' ({goal.current_value}/{goal.target_value})!",
                created_at=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
            
        return jsonify(goal.to_dict())
        
    elif request.method == 'DELETE':
        db.session.delete(goal)
        db.session.commit()
        return jsonify({'message': 'Goal deleted successfully'})

@app.route('/api/goals/<int:goal_id>/progress', methods=['POST'])
@login_required
def api_goal_progress(goal_id):
    user_id = session['user_id']
    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first_or_404()
    
    data = request.json or {}
    delta = data.get('delta', 1)
    
    try:
        delta = int(delta)
    except ValueError:
        return jsonify({'error': 'Delta must be an integer'}), 400
        
    goal.current_value += delta
    if goal.current_value < 0:
        goal.current_value = 0
        
    was_completed = goal.completed
    if goal.current_value >= goal.target_value:
        goal.completed = True
    else:
        goal.completed = False
        
    db.session.commit()
    
    just_completed = goal.completed and not was_completed
    if just_completed:
        user = User.query.get(user_id)
        log = NotificationLog(
            user_id=user_id,
            recipient=user.email,
            channel='Email',
            subject=f"🏆 Goal Achieved: {goal.title}!",
            message=f"Congratulations, {user.name}! You have achieved your goal: '{goal.title}' ({goal.current_value}/{goal.target_value})!",
            created_at=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
    return jsonify({
        'goal': goal.to_dict(),
        'just_completed': just_completed
    })


# --- SMART SCHEDULE GENERATOR API ---

@app.route('/api/ai/schedule-generator', methods=['POST'])
@login_required
def api_schedule_generator():
    data = request.json or {}
    start_time_str = data.get('start_time', '').strip() # e.g. "18:00"
    end_time_str = data.get('end_time', '').strip() # e.g. "22:00"
    task_ids = data.get('task_ids', []) # e.g. [1, 2, 3]
    custom_tasks = data.get('custom_tasks', []) # list of strings
    
    if not start_time_str or not end_time_str:
        return jsonify({'error': 'Start time and end time are required'}), 400
        
    try:
        start_t = datetime.strptime(start_time_str, "%H:%M")
        end_t = datetime.strptime(end_time_str, "%H:%M")
    except ValueError:
        try:
            start_t = datetime.strptime(start_time_str, "%I:%M %p")
            end_t = datetime.strptime(end_time_str, "%I:%M %p")
        except ValueError:
            return jsonify({'error': 'Invalid time format. Use HH:MM or HH:MM AM/PM.'}), 400
            
    if end_t <= start_t:
        end_t += timedelta(days=1)
        
    total_minutes = int((end_t - start_t).total_seconds() / 60)
    if total_minutes < 15:
        return jsonify({'error': 'Available time block must be at least 15 minutes'}), 400
        
    titles = []
    user_id = session['user_id']
    if task_ids:
        tasks = Task.query.filter(Task.id.in_(task_ids), Task.user_id == user_id).all()
        titles.extend([t.title for t in tasks])
    if custom_tasks:
        titles.extend([t.strip() for t in custom_tasks if t.strip()])
        
    if not titles:
        return jsonify({'error': 'No tasks provided for scheduling'}), 400
        
    schedule = []
    current_t = start_t
    
    num_tasks = len(titles)
    
    if total_minutes <= 60:
        task_dur = total_minutes // num_tasks
        break_dur = 0
        num_breaks = 0
    else:
        num_breaks = num_tasks - 1
        if num_breaks > 0:
            suggested_break_total = min(num_breaks * 15, int(total_minutes * 0.15))
            break_dur = suggested_break_total // num_breaks
            if break_dur < 5:
                break_dur = 0
                num_breaks = 0
        else:
            break_dur = 0
            
        remaining_work_mins = total_minutes - (num_breaks * break_dur)
        task_dur = remaining_work_mins // num_tasks
        
    for i, title in enumerate(titles):
        block_start = current_t
        block_end = current_t + timedelta(minutes=task_dur)
        
        schedule.append({
            'type': 'Work',
            'task': title,
            'start': block_start.strftime("%I:%M %p"),
            'end': block_end.strftime("%I:%M %p")
        })
        current_t = block_end
        
        if i < len(titles) - 1 and break_dur > 0:
            break_start = current_t
            break_end = current_t + timedelta(minutes=break_dur)
            schedule.append({
                'type': 'Break',
                'task': 'Rest / Stretch',
                'start': break_start.strftime("%I:%M %p"),
                'end': break_end.strftime("%I:%M %p")
            })
            current_t = break_end
            
    if schedule:
        schedule[-1]['end'] = end_t.strftime("%I:%M %p")
        
    return jsonify({
        'start_time': start_time_str,
        'end_time': end_time_str,
        'schedule': schedule
    })


# --- OPPORTUNITY HUB API ---

@app.route('/opportunities')
@login_required
def opportunities():
    return render_template('opportunities.html')

@app.route('/api/profile', methods=['GET', 'POST'])
@login_required
def api_profile():
    user_id = session['user_id']
    user = User.query.get(user_id)
    if request.method == 'GET':
        return jsonify({
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'branch': user.branch or '',
            'year': user.year or '',
            'skills': user.skills or ''
        })
    elif request.method == 'POST':
        data = request.json or {}
        user.branch = data.get('branch', '').strip()
        user.year = data.get('year', '').strip()
        user.skills = data.get('skills', '').strip()
        db.session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'branch': user.branch,
            'year': user.year,
            'skills': user.skills
        })

@app.route('/api/opportunities', methods=['GET'])
@login_required
def api_opportunities():
    user_id = session['user_id']
    user = User.query.get(user_id)
    now = datetime.utcnow()
    
    if Opportunity.query.count() == 0:
        try:
            OpportunityCrawler.run_aggregator()
        except Exception as e:
            print(f"[Aggregator] Auto-run error: {e}")
            
    recommend = request.args.get('recommend', '').lower() == 'true'
    category = request.args.get('category')
    search = request.args.get('search')
    
    if recommend:
        query = Opportunity.query.filter(Opportunity.deadline >= now)
        opportunities = query.all()
        
        user_skills = [s.strip().lower() for s in (user.skills or '').split(',') if s.strip()]
        user_branch = (user.branch or '').strip().lower()
        user_year = (user.year or '').strip().lower()
        
        recommended = []
        for opp in opportunities:
            opp_skills = [s.strip().lower() for s in (opp.skills or '').split(',') if s.strip()]
            opp_eligibility = (opp.eligibility or '').strip().lower()
            
            skill_match = any(s in opp_skills for s in user_skills)
            
            branch_match = False
            if user_branch:
                if user_branch in opp_eligibility or "all" in opp_eligibility or "open" in opp_eligibility:
                    branch_match = True
            else:
                branch_match = True
                
            year_match = False
            if user_year:
                if user_year in opp_eligibility or "all" in opp_eligibility or "open" in opp_eligibility:
                    year_match = True
            else:
                year_match = True
                
            if skill_match or (branch_match and year_match and not user_skills):
                dict_opp = opp.to_dict()
                dict_opp['match_reason'] = []
                if skill_match:
                    dict_opp['match_reason'].append("Matches your skills")
                if branch_match and user_branch:
                    dict_opp['match_reason'].append("Matches your branch")
                recommended.append(dict_opp)
                
        recommended.sort(key=lambda x: (-x['score'], x['deadline']))
        
        user_opps = UserOpportunity.query.filter_by(user_id=user_id).all()
        status_map = {uo.opportunity_id: uo.status for uo in user_opps}
        for ro in recommended:
            ro['user_status'] = status_map.get(ro['id'], None)
            
        return jsonify(recommended)
        
    else:
        query = Opportunity.query.filter(Opportunity.deadline >= now)
        if category:
            query = query.filter_by(category=category)
        if search:
            query = query.filter(Opportunity.name.like(f"%{search}%") | Opportunity.details.like(f"%{search}%"))
            
        opportunities = query.order_by(Opportunity.deadline.asc()).all()
        user_opps = UserOpportunity.query.filter_by(user_id=user_id).all()
        status_map = {uo.opportunity_id: uo.status for uo in user_opps}
        
        res_list = []
        for opp in opportunities:
            d = opp.to_dict()
            d['user_status'] = status_map.get(opp.id, None)
            res_list.append(d)
            
        return jsonify(res_list)

@app.route('/api/opportunities/<int:opp_id>/action', methods=['POST'])
@login_required
def api_opportunity_action(opp_id):
    user_id = session['user_id']
    opp = Opportunity.query.get_or_404(opp_id)
    
    data = request.json or {}
    status = data.get('status', '').strip()
    
    if status not in ['Saved', 'Applied', 'Ignored']:
        return jsonify({'error': 'Invalid status'}), 400
        
    user_opp = UserOpportunity.query.filter_by(user_id=user_id, opportunity_id=opp_id).first()
    if not user_opp:
        user_opp = UserOpportunity(
            user_id=user_id,
            opportunity_id=opp_id,
            status=status,
            updated_at=datetime.utcnow()
        )
        db.session.add(user_opp)
    else:
        user_opp.status = status
        user_opp.updated_at = datetime.utcnow()
        
    db.session.commit()
    return jsonify(user_opp.to_dict())

@app.route('/api/opportunities/saved-applied', methods=['GET'])
@login_required
def api_opportunities_saved_applied():
    user_id = session['user_id']
    user_opps = UserOpportunity.query.filter_by(user_id=user_id).all()
    filtered = [uo for uo in user_opps if uo.status in ['Saved', 'Applied']]
    
    res = []
    for uo in filtered:
        d = uo.to_dict()
        d['opportunity']['user_status'] = uo.status
        res.append(d['opportunity'])
        
    return jsonify(res)

@app.route('/api/opportunities/missed', methods=['GET'])
@login_required
def api_opportunities_missed():
    user_id = session['user_id']
    now = datetime.utcnow()
    
    if Opportunity.query.count() == 0:
        OpportunityCrawler.run_aggregator()
        
    past_opps = Opportunity.query.filter(Opportunity.deadline < now).all()
    applied_opp_ids = [uo.opportunity_id for uo in UserOpportunity.query.filter_by(user_id=user_id, status='Applied').all()]
    
    missed = []
    for opp in past_opps:
        if opp.id not in applied_opp_ids:
            missed.append(opp.to_dict())
            
    hackathons_missed = sum(1 for o in missed if o['category'] == 'Hackathon')
    competitions_missed = sum(1 for o in missed if o['category'] == 'Coding Competition')
    total_missed = len(missed)
    
    pattern_summary = ""
    if total_missed > 0:
        pattern_summary = f"You missed {total_missed} opportunities this semester (including {hackathons_missed} hackathons and {competitions_missed} coding competitions) because registration closed before you registered. N-Assist has scheduled automatic earlier alerts (3 days and 1 day in advance) for your Saved items to prevent this."
    else:
        pattern_summary = "Excellent! You have not missed any technical opportunities this semester. Keep tracking your goals and deadlines!"
        
    return jsonify({
        'missed': missed,
        'count': total_missed,
        'hackathons_count': hackathons_missed,
        'competitions_count': competitions_missed,
        'pattern_summary': pattern_summary
    })

@app.route('/api/opportunities/trigger-crawl', methods=['POST'])
@login_required
def api_opportunities_trigger_crawl():
    try:
        new_count = OpportunityCrawler.run_aggregator()
        return jsonify({'message': f'Aggregation completed successfully. Added {new_count} new items.', 'new_count': new_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calendar/events', methods=['GET'])
@login_required
def api_calendar_events():
    user_id = session['user_id']
    now = datetime.utcnow()
    
    tasks = Task.query.filter_by(user_id=user_id).all()
    events = []
    for t in tasks:
        t.update_priority()
        events.append({
            'id': t.id,
            'title': t.title,
            'deadline': t.deadline.isoformat(),
            'priority': t.priority,
            'status': t.status,
            'type': 'task',
            'category': t.category,
            'link': None,
            'is_overdue': t.is_overdue
        })
        
    user_opps = UserOpportunity.query.filter_by(user_id=user_id).all()
    for uo in user_opps:
        opp = uo.opportunity
        if opp and uo.status in ['Saved', 'Applied']:
            is_opp_overdue = uo.status != 'Applied' and opp.deadline < now
            events.append({
                'id': opp.id,
                'title': f"🔔 {opp.name}",
                'deadline': opp.deadline.isoformat(),
                'priority': 'Medium',
                'status': uo.status,
                'type': 'opportunity',
                'category': opp.category,
                'link': opp.link,
                'is_overdue': is_opp_overdue
            })
            
    return jsonify(events)


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
