from database import db
from datetime import datetime, timedelta

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    priority = db.Column(db.String(20), nullable=False) # High, Medium, Low
    status = db.Column(db.String(20), nullable=False, default='Pending') # Pending, Completed
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='tasks')
    reminders = db.relationship('Reminder', back_populates='task', cascade="all, delete-orphan")

    def update_priority(self):
        """
        Smart Priority System:
        - High Priority -> Deadline within 2 days (or overdue)
        - Medium Priority -> Deadline within 7 days
        - Low Priority -> More than 7 days
        """
        now = datetime.utcnow()
        delta = self.deadline - now
        
        if delta.days < 2:
            self.priority = 'High'
        elif delta.days < 7:
            self.priority = 'Medium'
        else:
            self.priority = 'Low'

    @property
    def is_overdue(self):
        """Checks if the task is overdue based on current UTC time."""
        return self.status == 'Pending' and self.deadline < datetime.utcnow()

    def to_dict(self):
        # Trigger priority check on fetch
        self.update_priority()
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'deadline': self.deadline.isoformat(),
            'priority': self.priority,
            'status': self.status,
            'is_overdue': self.is_overdue,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f"<Task {self.title} - {self.priority}>"
