from fastapi import FastAPI
from app.accounts.routes import router as accounts_router
from app.movies.routes import router as movies_router

app = FastAPI()

app.include_router(accounts_router)
app.include_router(movies_router)
