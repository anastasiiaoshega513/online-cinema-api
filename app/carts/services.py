from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.carts.models import Cart, CartItem
from db.dependencies import get_db


async def get_cart_with_items(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> Cart | None:
    result = await db.execute(
        select(Cart)
        .options(
            selectinload(Cart.items).selectinload(CartItem.movie)
        )
        .where(Cart.user_id == current_user.id)
    )

    return result.scalar_one_or_none()


async def get_or_create_cart(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Cart)
        .options(
            selectinload(Cart.items).selectinload(CartItem.movie)
        )
        .where(Cart.user_id == current_user.id)
    )

    cart = result.scalar_one_or_none()

    if cart is None:
        cart = Cart(user_id=current_user.id)
        db.add(cart)
        await db.commit()

        cart = await get_cart_with_items(db=db, user_id=current_user.id)

    return cart