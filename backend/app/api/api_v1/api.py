from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, users, plans, subscriptions, usage, dashboard, billing

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(usage.router, prefix="/usage", tags=["usage"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
