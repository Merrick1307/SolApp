from fastapi import APIRouter

from .tokens import router as token_router
from .wallets import router as wallet_router

api_router = APIRouter()

api_router.include_router(token_router, prefix='/tokens')
api_router.include_router(wallet_router, prefix='/wallets')