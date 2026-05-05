from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.movies.schemas import MovieBaseSchema
from orders.models import OrderStatusEnum


class OrderItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie: MovieBaseSchema
    price_at_order: Decimal


class OrderResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatusEnum
    total_amount: Decimal
    created_at: datetime
    items: list[OrderItemSchema]
