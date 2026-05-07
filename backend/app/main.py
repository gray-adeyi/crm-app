from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models.entities  # noqa: F401 — register ORM tables on Base.metadata

from app.api.errors import register_exception_handlers
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import Base, engine
from app.db.migrate import run_sqlite_migrations


def create_app() -> FastAPI:
    settings = get_settings()
    run_sqlite_migrations(engine)
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title="CRM SaaS API", version="2.0.0")
    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.FRONTEND_ORIGINS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.on_event("startup")
    def _start_scheduler():  # noqa: ANN001
        try:
            from app.services.reminder_scheduler import start_reminder_scheduler

            app.state.reminder_scheduler = start_reminder_scheduler()
        except Exception:
            # Never crash API because scheduler failed
            import logging

            logging.getLogger(__name__).exception("Failed to start reminder scheduler")

    @app.on_event("shutdown")
    def _stop_scheduler():  # noqa: ANN001
        sched = getattr(app.state, "reminder_scheduler", None)
        if sched:
            try:
                sched.shutdown(wait=False)
            except Exception:
                import logging

                logging.getLogger(__name__).exception("Failed to stop reminder scheduler")
    return app


app = create_app()
