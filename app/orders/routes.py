from decimal import Decimal

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.accounts.models import User
from app.accounts.dependencies import get_current_user
from app.orders.models import Order, OrderItem, OrderStatusEnum
from app.orders.schemas import OrderResponseSchema
from app.carts.models import CartItem
from app.carts.services import get_cart_with_items
from db.dependencies import get_db
from app.orders.services import get_order

router = APIRouter()


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


@router.post("/orders/", response_model=OrderResponseSchema)
async def create_order(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cart = await get_cart_with_items(db=db, user_id=current_user.id)

    if cart is None or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty.",
        )

    order = Order(
        user_id=current_user.id,
        status=OrderStatusEnum.PENDING,
        total_amount=Decimal("0.00"),
    )

    db.add(order)
    await db.flush()

    total_amount = Decimal("0.00")

    for cart_item in cart.items:
        price = cart_item.movie.price

        order_item = OrderItem(
            order_id=order.id,
            movie_id=cart_item.movie_id,
            price_at_order=price,
        )

        db.add(order_item)
        total_amount += price

    order.total_amount = total_amount

    await db.execute(
        delete(CartItem).where(CartItem.cart_id == cart.id)
    )

    await db.commit()

    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.movie)
        )
        .where(Order.id == order.id)
    )

    order = result.scalar_one()

    return order


@router.get("/orders/{order_id}/", response_model=OrderResponseSchema)
async def get_one_order(order_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    order = await get_order(db=db, order_id=order_id, user_id=current_user.id)
    return order


@router.patch("/orders/{order_id}/cancel/", response_model=OrderResponseSchema)
async def cancel_order(order_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    order = await get_order(db=db, order_id=order_id, user_id=current_user.id)

    if not order.status == OrderStatusEnum.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This order cannot be canceled.")

    order.status = OrderStatusEnum.CANCELED
    await db.commit()

    return order


@router.patch("/orders/{order_id}/pay/", response_model=OrderResponseSchema)
async def pay_order(order_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    order = await get_order(db=db, order_id=order_id, user_id=current_user.id)

    if not order.status == OrderStatusEnum.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This order cannot be paid.")

    order.status = OrderStatusEnum.PAID
    await db.commit()

    return order
