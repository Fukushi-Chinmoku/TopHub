from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.config import settings
from app.db.base import Base
from app.db.bootstrap import seed_subjects
from app.db.session import engine
from app.db.session import SessionLocal
import app.models
from app.ws.routes import router as ws_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await seed_subjects(session)
    yield


app = FastAPI(title=settings.app_name, debug=settings.app_debug, lifespan=lifespan)
app.include_router(api_router)
app.include_router(ws_router)
