from fastapi import APIRouter
from api.v1.endpoints import health, auth, journals, memory, users

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(journals.router, prefix="/journals", tags=["journals"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
