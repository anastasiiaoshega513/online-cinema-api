from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.orders.schemas import OrderResponseSchema
from orders.models import Order, OrderItem


async def get_order(db: AsyncSession, order_id: int, user_id: int) -> OrderResponseSchema:
    stmt = (
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.movie)
        )
        .where(Order.id == order_id, Order.user_id == user_id)
    )

    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No order found.")

    return order