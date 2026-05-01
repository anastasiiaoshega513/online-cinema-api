from fastapi import FastAPI
from app.accounts.routes import router as accounts_router

app = FastAPI()

app.include_router(accounts_router)
