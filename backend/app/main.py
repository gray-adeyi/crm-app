import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.v1.router import api_router
from app.core.config import settings


def _start_scheduler(app: FastAPI):
    try:
        from app.services.reminder_scheduler import start_reminder_scheduler

        app.state.reminder_scheduler = start_reminder_scheduler()
    except Exception:
        # Never crash API because scheduler failed
        logging.getLogger(__name__).exception("Failed to start reminder scheduler")


def _stop_scheduler(app: FastAPI):
    sched = getattr(app.state, "reminder_scheduler", None)
    if sched:
        try:
            sched.shutdown(wait=False)
        except Exception:
            logging.getLogger(__name__).exception("Failed to stop reminder scheduler")


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_exception_handlers(app)
    _start_scheduler(app)
    yield
    _stop_scheduler(app)


app = FastAPI(title="CRM SaaS API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
