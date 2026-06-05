"""
API v1 Router
==============
Aggregates all route modules into a single router.
All routes are prefixed with /api/v1 (applied in main.py).
"""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    patients,
    donors,
    coordinators,
    hospitals,
    transfusions,
    confirmations,
    notifications,
    rewards,
    wallets,
    expenses,
    emergency,
    incidents,
    admin,
)

api_router = APIRouter()

api_router.include_router(auth.router,          prefix="/auth",          tags=["Authentication"])
api_router.include_router(patients.router,      prefix="/patients",      tags=["Patients"])
api_router.include_router(donors.router,        prefix="/donors",        tags=["Donors"])
api_router.include_router(coordinators.router,  prefix="/coordinators",  tags=["Coordinators"])
api_router.include_router(hospitals.router,     prefix="/hospitals",     tags=["Hospitals"])
api_router.include_router(transfusions.router,  prefix="/transfusions",  tags=["Transfusions"])
api_router.include_router(confirmations.router, prefix="/confirmations", tags=["Confirmations"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(rewards.router,       prefix="/rewards",       tags=["Rewards"])
api_router.include_router(wallets.router,       prefix="/wallets",       tags=["Wallets"])
api_router.include_router(expenses.router,      prefix="/expenses",      tags=["Expenses"])
api_router.include_router(emergency.router,     prefix="/emergency",     tags=["Emergency"])
api_router.include_router(incidents.router,     prefix="/incidents",     tags=["Incidents"])
api_router.include_router(admin.router,         prefix="/admin",         tags=["Admin"])
