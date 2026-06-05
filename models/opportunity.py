from database import db
from datetime import datetime

class Opportunity(db.Model):
    __tablename__ = 'opportunities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False) # Hackathon, Internship, Workshop, Webinar, Scholarship, Certification, Coding Competition, Open Source Program, Campus Ambassador Program, Research Program
    deadline = db.Column(db.DateTime, nullable=False)
    eligibility = db.Column(db.String(200), nullable=True) # e.g. "CSE / IT Students" or "2nd & 3rd Year"
    skills = db.Column(db.String(200), nullable=True) # Comma-separated: "Python, Web Development, AI/ML"
    link = db.Column(db.String(255), nullable=False)
    score = db.Column(db.Integer, nullable=False, default=3) # Ranking rating: 1-5
    details = db.Column(db.Text, nullable=True) # Prize pool, certificate details, stipend details
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user_actions = db.relationship('UserOpportunity', back_populates='opportunity', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'deadline': self.deadline.isoformat(),
            'eligibility': self.eligibility,
            'skills': self.skills,
            'link': self.link,
            'score': self.score,
            'details': self.details,
            'created_at': self.created_at.isoformat()
        }
