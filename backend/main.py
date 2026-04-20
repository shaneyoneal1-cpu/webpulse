import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import engine, SessionLocal, Base
from models import User, SystemConfig
from auth import get_password_hash
from config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, CHECK_INTERVAL_SECONDS
from routes_auth import router as auth_router
from routes_websites import router as websites_router
from routes_admin import router as admin_router
from monitor import run_checks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webpulse")

scheduler = AsyncIOScheduler()


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
        if not admin:
            admin = User(
                username=DEFAULT_ADMIN_USERNAME,
                hashed_password=get_password_hash(DEFAULT_ADMIN_PASSWORD),
                is_main_admin=True,
                must_change_password=True,
                permissions={
                    "view_websites": True,
                    "manage_websites": True,
                    "run_checks": True,
                    "view_users": True,
                    "manage_users": True,
                    "view_settings": True,
                    "manage_settings": True,
                },
            )
            db.add(admin)
            db.commit()
            logger.info(f"Default admin created: {DEFAULT_ADMIN_USERNAME} / {DEFAULT_ADMIN_PASSWORD}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.add_job(run_checks, "interval", seconds=CHECK_INTERVAL_SECONDS, id="website_checks")
    scheduler.start()
    logger.info(f"Scheduler started. Checks every {CHECK_INTERVAL_SECONDS}s")
    yield
    scheduler.shutdown()


app = FastAPI(
    title="WebPulse",
    description="Self-hostable website monitoring tool",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(websites_router)
app.include_router(admin_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "WebPulse"}
