from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/")
def home():
    return {"message": "CRM API is running.", "health": "/health"}
