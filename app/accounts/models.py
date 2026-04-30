from enum import StrEnum, auto

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Enum, ForeignKey
from sqlalchemy.orm import Relationship

from db.engine import Base


class UserGroupEnum(StrEnum):
    USER = auto()
    MODERATOR = auto()
    ADMIN = auto()


class GenderEnum(StrEnum):
    MAN = auto()
    WOMAN = auto()


class UserGroup(Base):
    __tablename__ = "user_group"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(UserGroupEnum), nullable=False)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    group_id = Column(Integer, ForeignKey("user_group.id"), nullable=False)
    group = Relationship(UserGroup, back_populates="users")


