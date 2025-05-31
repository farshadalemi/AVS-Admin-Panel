from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings
from app.db import base  # noqa: F401

# Make sure all SQL Alchemy models are imported (app.db.base) before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly


def init_db(db: Session) -> None:
    """
    Initialize database with default data
    """
    # Create superuser
    user = crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER_EMAIL)
    if not user:
        user_in = schemas.UserCreate(
            email=settings.FIRST_SUPERUSER_EMAIL,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            full_name="System Administrator",
            is_superuser=True,
        )
        user = crud.user.create(db, obj_in=user_in)
        print(f"Created superuser: {user.email}")
    else:
        print(f"Superuser already exists: {user.email}")

    # Create default plans
    default_plans = [
        {
            "name": "Basic",
            "description": "Perfect for small businesses getting started with AI voice assistance",
            "price": 29.99,
            "duration_days": 30,
            "max_calls": 100,
            "max_minutes": 500,
            "features": {
                "ai_voice_assistant": True,
                "call_recording": True,
                "basic_analytics": True,
                "email_support": True,
                "business_hours_support": "9AM-5PM",
                "concurrent_calls": 1,
                "custom_greetings": False,
                "advanced_routing": False,
                "api_access": False,
            }
        },
        {
            "name": "Professional",
            "description": "Ideal for growing businesses with higher call volumes",
            "price": 79.99,
            "duration_days": 30,
            "max_calls": 500,
            "max_minutes": 2000,
            "features": {
                "ai_voice_assistant": True,
                "call_recording": True,
                "basic_analytics": True,
                "advanced_analytics": True,
                "email_support": True,
                "priority_support": True,
                "business_hours_support": "24/7",
                "concurrent_calls": 3,
                "custom_greetings": True,
                "advanced_routing": True,
                "api_access": True,
                "webhook_integration": True,
            }
        },
        {
            "name": "Enterprise",
            "description": "Comprehensive solution for large organizations",
            "price": 199.99,
            "duration_days": 30,
            "max_calls": 2000,
            "max_minutes": 10000,
            "features": {
                "ai_voice_assistant": True,
                "call_recording": True,
                "basic_analytics": True,
                "advanced_analytics": True,
                "custom_reporting": True,
                "email_support": True,
                "priority_support": True,
                "dedicated_support": True,
                "business_hours_support": "24/7",
                "concurrent_calls": 10,
                "custom_greetings": True,
                "advanced_routing": True,
                "api_access": True,
                "webhook_integration": True,
                "white_label": True,
                "sla_guarantee": "99.9%",
            }
        },
        {
            "name": "Starter",
            "description": "Try our service with limited features",
            "price": 9.99,
            "duration_days": 30,
            "max_calls": 25,
            "max_minutes": 100,
            "features": {
                "ai_voice_assistant": True,
                "call_recording": False,
                "basic_analytics": True,
                "email_support": True,
                "business_hours_support": "9AM-5PM",
                "concurrent_calls": 1,
                "custom_greetings": False,
                "advanced_routing": False,
                "api_access": False,
            }
        }
    ]

    for plan_data in default_plans:
        existing_plan = crud.plan.get_by_name(db, name=plan_data["name"])
        if not existing_plan:
            plan_in = schemas.PlanCreate(**plan_data)
            plan = crud.plan.create(db, obj_in=plan_in)
            print(f"Created plan: {plan.name}")
        else:
            print(f"Plan already exists: {existing_plan.name}")

    print("Database initialization completed!")


def create_sample_data(db: Session) -> None:
    """
    Create sample data for testing (optional)
    """
    import random
    from datetime import datetime, timedelta

    # Create sample users
    sample_users = [
        {
            "email": "john.doe@example.com",
            "password": "password123",
            "full_name": "John Doe",
        },
        {
            "email": "jane.smith@example.com",
            "password": "password123",
            "full_name": "Jane Smith",
        },
        {
            "email": "bob.wilson@example.com",
            "password": "password123",
            "full_name": "Bob Wilson",
        },
    ]

    created_users = []
    for user_data in sample_users:
        existing_user = crud.user.get_by_email(db, email=user_data["email"])
        if not existing_user:
            user_in = schemas.UserCreate(**user_data)
            user = crud.user.create(db, obj_in=user_in)
            created_users.append(user)
            print(f"Created sample user: {user.email}")
        else:
            created_users.append(existing_user)

    # Get plans
    plans = crud.plan.get_multi(db, limit=10)
    
    # Create sample subscriptions
    for user in created_users:
        # Check if user already has a subscription
        existing_subscription = crud.subscription.get_user_active_subscription(
            db, user_id=user.id
        )
        if not existing_subscription:
            # Create a subscription with a random plan
            plan = random.choice(plans)
            subscription_in = schemas.SubscriptionCreate(
                user_id=user.id,
                plan_id=plan.id,
                payment_amount=plan.price,
                payment_method="credit_card",
                payment_status="completed",
                is_active=True,
            )
            subscription = crud.subscription.create(db, obj_in=subscription_in)
            print(f"Created subscription for {user.email} with plan {plan.name}")

            # Create sample usage data
            for i in range(random.randint(5, 20)):
                start_time = datetime.utcnow() - timedelta(
                    days=random.randint(1, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                duration = random.randint(30, 600)  # 30 seconds to 10 minutes
                end_time = start_time + timedelta(seconds=duration)
                
                usage_in = schemas.UsageCreate(
                    user_id=user.id,
                    call_id=f"call_{user.id}_{i}_{int(start_time.timestamp())}",
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    status=random.choice(["completed", "failed", "busy"]),
                    caller_number=f"+1555{random.randint(1000000, 9999999)}",
                    destination_number=f"+1800{random.randint(1000000, 9999999)}",
                    call_type=random.choice(["inbound", "outbound"]),
                    call_summary=f"Sample call {i+1} for user {user.full_name}",
                )
                usage = crud.usage.create(db, obj_in=usage_in)

    print("Sample data creation completed!")
