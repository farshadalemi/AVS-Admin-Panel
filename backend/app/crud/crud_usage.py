from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, extract

from app.crud.base import CRUDBase
from app.models.usage import Usage
from app.models.user import User
from app.schemas.usage import UsageCreate, UsageUpdate


class CRUDUsage(CRUDBase[Usage, UsageCreate, UsageUpdate]):
    def create(self, db: Session, *, obj_in: UsageCreate) -> Usage:
        db_obj = Usage(
            user_id=obj_in.user_id,
            call_id=obj_in.call_id,
            start_time=obj_in.start_time,
            end_time=obj_in.end_time,
            duration=obj_in.duration,
            status=obj_in.status,
            caller_number=obj_in.caller_number,
            destination_number=obj_in.destination_number,
            call_type=obj_in.call_type,
            call_summary=obj_in.call_summary,
            recording_url=obj_in.recording_url,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Usage, obj_in: Union[UsageUpdate, Dict[str, Any]]
    ) -> Usage:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        update_data["updated_at"] = datetime.utcnow()
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def get_user_usage(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Usage]:
        """Get usage records for a specific user"""
        query = db.query(Usage).filter(Usage.user_id == user_id)
        
        if start_date:
            query = query.filter(Usage.start_time >= start_date)
        if end_date:
            query = query.filter(Usage.start_time <= end_date)
        
        return (
            query.order_by(desc(Usage.start_time))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_usage_with_user_details(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        user_email: Optional[str] = None,
        call_status: Optional[str] = None,
        call_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get usage records with user details"""
        query = (
            db.query(Usage)
            .join(User, Usage.user_id == User.id)
        )
        
        # Apply filters
        if user_email:
            query = query.filter(User.email.ilike(f"%{user_email}%"))
        
        if call_status:
            query = query.filter(Usage.status == call_status)
        
        if call_type:
            query = query.filter(Usage.call_type == call_type)
        
        if start_date:
            query = query.filter(Usage.start_time >= start_date)
        
        if end_date:
            query = query.filter(Usage.start_time <= end_date)
        
        usage_records = (
            query.order_by(desc(Usage.start_time))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        result = []
        for usage in usage_records:
            result.append({
                "id": usage.id,
                "call_id": usage.call_id,
                "start_time": usage.start_time,
                "end_time": usage.end_time,
                "duration": usage.duration,
                "status": usage.status,
                "caller_number": usage.caller_number,
                "destination_number": usage.destination_number,
                "call_type": usage.call_type,
                "call_summary": usage.call_summary,
                "recording_url": usage.recording_url,
                "created_at": usage.created_at,
                "user": {
                    "id": usage.user.id,
                    "email": usage.user.email,
                    "full_name": usage.user.full_name,
                },
                "duration_minutes": round(usage.duration / 60, 2) if usage.duration else 0,
            })
        
        return result

    def get_user_monthly_usage(self, db: Session, *, user_id: int, year: int, month: int) -> Dict[str, Any]:
        """Get user's usage statistics for a specific month"""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        usage_stats = (
            db.query(
                func.count(Usage.id).label('total_calls'),
                func.sum(Usage.duration).label('total_duration'),
                func.avg(Usage.duration).label('avg_duration'),
                func.count(func.distinct(Usage.caller_number)).label('unique_callers')
            )
            .filter(
                and_(
                    Usage.user_id == user_id,
                    Usage.start_time >= start_date,
                    Usage.start_time < end_date
                )
            )
            .first()
        )
        
        # Get call type breakdown
        call_type_stats = (
            db.query(
                Usage.call_type,
                func.count(Usage.id).label('count'),
                func.sum(Usage.duration).label('duration')
            )
            .filter(
                and_(
                    Usage.user_id == user_id,
                    Usage.start_time >= start_date,
                    Usage.start_time < end_date
                )
            )
            .group_by(Usage.call_type)
            .all()
        )
        
        # Get status breakdown
        status_stats = (
            db.query(
                Usage.status,
                func.count(Usage.id).label('count')
            )
            .filter(
                and_(
                    Usage.user_id == user_id,
                    Usage.start_time >= start_date,
                    Usage.start_time < end_date
                )
            )
            .group_by(Usage.status)
            .all()
        )
        
        return {
            "year": year,
            "month": month,
            "total_calls": usage_stats.total_calls or 0,
            "total_duration": float(usage_stats.total_duration or 0),
            "total_duration_minutes": round(float(usage_stats.total_duration or 0) / 60, 2),
            "avg_duration": float(usage_stats.avg_duration or 0),
            "avg_duration_minutes": round(float(usage_stats.avg_duration or 0) / 60, 2),
            "unique_callers": usage_stats.unique_callers or 0,
            "call_type_breakdown": {
                stat.call_type: {
                    "count": stat.count,
                    "duration": float(stat.duration or 0),
                    "duration_minutes": round(float(stat.duration or 0) / 60, 2)
                }
                for stat in call_type_stats
            },
            "status_breakdown": {
                stat.status: stat.count
                for stat in status_stats
            }
        }

    def get_system_usage_analytics(
        self, 
        db: Session, 
        *, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get system-wide usage analytics"""
        query = db.query(Usage)
        
        if start_date:
            query = query.filter(Usage.start_time >= start_date)
        if end_date:
            query = query.filter(Usage.start_time <= end_date)
        
        # Overall stats
        overall_stats = (
            query.with_entities(
                func.count(Usage.id).label('total_calls'),
                func.sum(Usage.duration).label('total_duration'),
                func.avg(Usage.duration).label('avg_duration'),
                func.count(func.distinct(Usage.user_id)).label('active_users')
            )
            .first()
        )
        
        # Daily call volume (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_stats = (
            db.query(
                func.date(Usage.start_time).label('date'),
                func.count(Usage.id).label('calls'),
                func.sum(Usage.duration).label('duration')
            )
            .filter(Usage.start_time >= thirty_days_ago)
            .group_by(func.date(Usage.start_time))
            .order_by(func.date(Usage.start_time))
            .all()
        )
        
        # Hourly distribution
        hourly_stats = (
            db.query(
                extract('hour', Usage.start_time).label('hour'),
                func.count(Usage.id).label('calls')
            )
            .group_by(extract('hour', Usage.start_time))
            .order_by(extract('hour', Usage.start_time))
            .all()
        )
        
        # Top users by call volume
        top_users = (
            db.query(
                User.email,
                User.full_name,
                func.count(Usage.id).label('total_calls'),
                func.sum(Usage.duration).label('total_duration')
            )
            .join(User, Usage.user_id == User.id)
            .group_by(User.id, User.email, User.full_name)
            .order_by(func.count(Usage.id).desc())
            .limit(10)
            .all()
        )
        
        return {
            "overall": {
                "total_calls": overall_stats.total_calls or 0,
                "total_duration": float(overall_stats.total_duration or 0),
                "total_duration_hours": round(float(overall_stats.total_duration or 0) / 3600, 2),
                "avg_duration": float(overall_stats.avg_duration or 0),
                "avg_duration_minutes": round(float(overall_stats.avg_duration or 0) / 60, 2),
                "active_users": overall_stats.active_users or 0,
            },
            "daily_volume": [
                {
                    "date": stat.date.isoformat(),
                    "calls": stat.calls,
                    "duration": float(stat.duration or 0),
                    "duration_hours": round(float(stat.duration or 0) / 3600, 2)
                }
                for stat in daily_stats
            ],
            "hourly_distribution": [
                {
                    "hour": int(stat.hour),
                    "calls": stat.calls
                }
                for stat in hourly_stats
            ],
            "top_users": [
                {
                    "email": user.email,
                    "full_name": user.full_name,
                    "total_calls": user.total_calls,
                    "total_duration": float(user.total_duration or 0),
                    "total_duration_hours": round(float(user.total_duration or 0) / 3600, 2)
                }
                for user in top_users
            ]
        }

    def get_by_call_id(self, db: Session, *, call_id: str) -> Optional[Usage]:
        """Get usage record by call ID"""
        return db.query(Usage).filter(Usage.call_id == call_id).first()

    def update_call_end(
        self, db: Session, *, call_id: str, end_time: datetime, duration: float, status: str
    ) -> Optional[Usage]:
        """Update call end details"""
        usage = self.get_by_call_id(db, call_id=call_id)
        if usage:
            usage.end_time = end_time
            usage.duration = duration
            usage.status = status
            usage.updated_at = datetime.utcnow()
            db.add(usage)
            db.commit()
            db.refresh(usage)
        return usage

    def get_active_calls(self, db: Session) -> List[Usage]:
        """Get currently active calls (no end_time)"""
        return (
            db.query(Usage)
            .filter(
                and_(
                    Usage.end_time.is_(None),
                    Usage.status.in_(["initiated", "connected"])
                )
            )
            .order_by(desc(Usage.start_time))
            .all()
        )


usage = CRUDUsage(Usage)
