from database import db
from datetime import datetime

class UserOpportunity(db.Model):
    __tablename__ = 'user_opportunities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Saved') # 'Saved', 'Applied', 'Ignored'
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='user_opportunities')
    opportunity = db.relationship('Opportunity', back_populates='user_actions')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'opportunity_id': self.opportunity_id,
            'status': self.status,
            'updated_at': self.updated_at.isoformat(),
            'opportunity': self.opportunity.to_dict() if self.opportunity else None
        }
