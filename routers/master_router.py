from fastapi import APIRouter

from . import users, shipments

master_router = APIRouter()

master_router.include_router(shipments.router)
master_router.include_router(users.router)