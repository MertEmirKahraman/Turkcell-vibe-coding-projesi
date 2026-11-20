from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"])
def health_check() -> dict[str, object]:
    return {"success": True, "data": {"status": "ok"}, "error": None}