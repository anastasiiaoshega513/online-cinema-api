from fastapi import APIRouter, Header, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.carts.models import Cart, CartItem
from app.carts.schemas import CartResponseScheme
from db.dependencies import get_db

router = APIRouter()

# POST /cart/items/{movie_id}
# DELETE /cart/items/{movie_id}
# DELETE /cart/clear

@router.get("/cart/", response_model=CartResponseScheme, response_model_exclude_none=True)
async def get_cart(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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

    if not cart.items:
        return {"detail": "There are no cart items yet."}

    return {"items": cart.items}


@router.post("/cart/items/{movie_id}/", response_model=CartResponseScheme)
async def add_to_cart(movie_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):

