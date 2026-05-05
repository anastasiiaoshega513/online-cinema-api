from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.carts.models import Cart, CartItem
from app.carts.schemas import CartResponseScheme
from app.carts.services import get_or_create_cart, get_cart_with_items
from db.dependencies import get_db
from app.movies.models import Movie

router = APIRouter()


@router.get("/cart/", response_model=CartResponseScheme, response_model_exclude_none=True)
async def get_cart(cart: Cart = Depends(get_or_create_cart)):
    if not cart.items:
        return {"detail": "There are no movies yet."}

    return {"items": cart.items}


@router.post("/cart/items/{movie_id}/", response_model=CartResponseScheme)
async def add_to_cart(movie_id: int, cart: Cart = Depends(get_or_create_cart), db: AsyncSession = Depends(get_db)):

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

    cart = await get_cart_with_items(db=db, user_id=cart.user_id)

    return {
        "detail": "Movie has been added to the cart.",
        "items": cart.items,
    }


@router.delete("/cart/items/{movie_id}/", response_model=CartResponseScheme, response_model_exclude_none=True)
async def remove_from_cart(movie_id: int, cart: Cart = Depends(get_or_create_cart), db: AsyncSession = Depends(get_db)):
    stmt = await db.execute(select(CartItem).where(CartItem.movie_id == movie_id, CartItem.cart_id == cart.id))
    movie_item = stmt.scalar_one_or_none()

    if not movie_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found in your cart.",
        )

    await db.delete(movie_item)
    await db.commit()

    cart = await get_cart_with_items(db=db, user_id=cart.user_id)

    return {
        "detail": "Movie has been deleted from the cart successfully.",
        "items": cart.items or None,
    }


@router.delete("/cart/clear/", response_model=CartResponseScheme, response_model_exclude_none=True)
async def clear_cart(cart: Cart = Depends(get_or_create_cart), db: AsyncSession = Depends(get_db)):
    await db.execute(
        delete(CartItem).where(CartItem.cart_id == cart.id)
    )
    await db.commit()

    return {"detail": "Cart has been cleared successfully."}
