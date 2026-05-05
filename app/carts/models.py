from sqlalchemy import Column, Integer, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Relationship

from db.engine import Base


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = Relationship(
        "User",
        back_populates="cart",
        uselist=False
    )
    items = Relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("user_id"),)

    def __repr__(self):
        return f"<Cart(user_id={self.user_id})>"


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"))
    movie_id = Column(Integer, ForeignKey("movies.id"))
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cart = Relationship(
        "Cart",
        back_populates="items",
    )

    movie = Relationship(
        "Movie",
        back_populates="cart_items",
    )

    __table_args__ = (
        UniqueConstraint("cart_id", "movie_id", name="unique_cart_item_constraint"),
    )

    def __repr__(self):
        return f"<Cart Item(cart_id={self.cart_id}, movie_id={self.movie_id})>"
