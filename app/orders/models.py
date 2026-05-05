from enum import StrEnum, auto

from sqlalchemy import Column, Integer, ForeignKey, DateTime, func, Enum, Numeric, UniqueConstraint
from sqlalchemy.orm import Relationship

from db.engine import Base


class OrderStatusEnum(StrEnum):
    PENDING = auto()
    PAID = auto()
    CANCELED = auto()


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(
        Enum(OrderStatusEnum),
        default=OrderStatusEnum.PENDING,
        nullable=False,
    )
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)

    user = Relationship(
        "User",
        back_populates="orders",
    )
    items = Relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Order(user_id={self.user_id}, status={self.status})>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    price_at_order = Column(Numeric(10, 2), nullable=False)

    order = Relationship(
        "Order",
        back_populates="items",
    )

    movie = Relationship(
        "Movie",
        back_populates="order_items",
    )

    __table_args__ = (
        UniqueConstraint("order_id", "movie_id", name="unique_order_item_constraint"),
    )

    def __repr__(self):
        return f"<Order Item(order_id={self.order_id}, movie_id={self.movie_id})>"
