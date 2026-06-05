from database import db
from datetime import datetime

class Goal(db.Model):
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    target_value = db.Column(db.Integer, nullable=False)
    current_value = db.Column(db.Integer, nullable=False, default=0)
    deadline = db.Column(db.DateTime, nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', back_populates='goals')

    @property
    def progress_percentage(self):
        if self.target_value <= 0:
            return 0
        percentage = int((self.current_value / self.target_value) * 100)
        return min(percentage, 100)

    @property
    def is_overdue(self):
        return not self.completed and self.deadline < datetime.utcnow()

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'progress_percentage': self.progress_percentage,
            'deadline': self.deadline.isoformat(),
            'completed': self.completed,
            'is_overdue': self.is_overdue,
            'created_at': self.created_at.isoformat()
        }
