from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.carts.models import Cart, CartItem
from app.carts.schemas import CartResponseScheme
from app.carts.services import get_or_create_cart, get_cart_with_items
from db.dependencies import get_db
from app.movies.models import Movie

router = APIRouter()

# DELETE /cart/items/{movie_id}
# DELETE /cart/clear

@router.get("/cart/", response_model=CartResponseScheme, response_model_exclude_none=True)
async def get_cart(cart: Cart = Depends(get_or_create_cart)):
    if not cart.items:
        return {"detail": "There are no cart items yet."}

    return {"items": cart.items}


@router.post("/cart/items/{movie_id}/", response_model=CartResponseScheme)
async def add_to_cart(movie_id: int, cart: Cart = Depends(get_or_create_cart), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):

    movie = await db.scalar(
        select(Movie).where(Movie.id == movie_id)
    )

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found.",
        )

    stmt = await db.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.movie_id == movie_id,
        )
    )
    existing_item = stmt.scalar_one_or_none()

    if existing_item:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Movie is already in the cart.")

    item = CartItem(movie_id=movie_id, cart_id=cart.id)
    db.add(item)
    await db.commit()

    cart = await get_cart_with_items(db=db, user_id=current_user.id)

    return {
        "detail": "Movie has been added to the cart.",
        "items": cart.items,
    }

