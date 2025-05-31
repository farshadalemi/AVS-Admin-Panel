from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Subscription(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plan.id"), nullable=False)
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    payment_status = Column(String, default="pending")  # pending, completed, failed, refunded
    payment_amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=True)
    payment_id = Column(String, nullable=True)  # External payment ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    
    def __repr__(self) -> str:
        return f"<Subscription {self.id} - User: {self.user_id}, Plan: {self.plan_id}>"
