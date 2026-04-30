from fastapi import APIRouter

from biblioteca_virtual.api.v1 import auth, books, loans, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, tags=["Auth"])
api_router.include_router(users.router, tags=["Users"])
api_router.include_router(books.router, tags=["Books"])
api_router.include_router(loans.router, tags=["Loans"])
