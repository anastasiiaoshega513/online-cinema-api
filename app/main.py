from fastapi import FastAPI
from app.accounts.routes import router as accounts_router
from app.movies.routes import router as movies_router
from app.carts.routes import router as carts_router
from app.orders.routes import router as orders_router

app = FastAPI()

app.include_router(accounts_router)
app.include_router(movies_router)
app.include_router(carts_router)
app.include_router(orders_router)
