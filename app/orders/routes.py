from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.accounts.models import User
from app.accounts.dependencies import get_current_user
from app.orders.models import Order, OrderItem
from app.orders.schemas import OrderResponseSchema
from db.dependencies import get_db

router = APIRouter()

# POST /orders
# GET /orders
# GET /orders/{order_id}
# PATCH /orders/{order_id}/cancel
#

@router.get("/orders/", response_model=list[OrderResponseSchema])
async def get_all_orders(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.movie)
        )
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    )

    result_orders = await db.execute(stmt)
    orders = result_orders.scalars().all()

    if not orders:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No orders found.")

    return orders


