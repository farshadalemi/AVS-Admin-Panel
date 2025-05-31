from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Usage(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    call_id = Column(String, nullable=False, index=True)  # External call ID
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)  # Null if call is ongoing
    duration = Column(Float, nullable=True)  # Duration in seconds
    status = Column(String, nullable=False)  # initiated, connected, completed, failed
    caller_number = Column(String, nullable=False)
    destination_number = Column(String, nullable=False)
    call_type = Column(String, nullable=False)  # inbound, outbound
    call_summary = Column(Text, nullable=True)  # Summary of the call (AI generated)
    recording_url = Column(String, nullable=True)  # URL to call recording if available
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="usages")
    
    def __repr__(self) -> str:
        return f"<Usage {self.id} - User: {self.user_id}, Call: {self.call_id}>"
