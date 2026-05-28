from fastapi import APIRouter

from app.api.routes import auth, cabinet, friends, groups, health, notes, subjects, users


api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(groups.router)
api_router.include_router(friends.router)
api_router.include_router(users.router)
api_router.include_router(subjects.router)
api_router.include_router(notes.router)
api_router.include_router(cabinet.router)
