from database import db
from datetime import datetime

class AcademicTracker(db.Model):
    __tablename__ = 'academic_tracker'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False) # 'Workshop', 'Certification', 'Hackathon', 'Seminar', 'Technical Event'
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', back_populates='achievements')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'category': self.category,
            'date': self.date.isoformat(),
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }
