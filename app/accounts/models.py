from enum import StrEnum, auto
from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Enum, ForeignKey, Date, Text, UniqueConstraint
from sqlalchemy.orm import Relationship, validates

from db.engine import Base
from security.passwords import hash_password, verify_password
from validators.accounts import validate_password_strength, validate_email


class UserGroupEnum(StrEnum):
    USER = auto()
    MODERATOR = auto()
    ADMIN = auto()


class GenderEnum(StrEnum):
    MAN = auto()
    WOMAN = auto()


class UserGroup(Base):
    __tablename__ = "user_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(UserGroupEnum), nullable=False)

    users = Relationship("User", back_populates="group")

    def __repr__(self):
        return f"<UserGroupModel(id={self.id}, name={self.name})>"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    _hashed_password = Column("hashed_password", String, nullable=False)
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
    group_id = Column(Integer, ForeignKey("user_groups.id"), nullable=False)
    group = Relationship(UserGroup, back_populates="users")
    profile = Relationship(
        "UserProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    activation_token = Relationship(
        "ActivationToken",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    password_reset_token = Relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    refresh_tokens = Relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<UserModel(id={self.id}, email={self.email}, is_active={self.is_active})>"

    @property
    def password(self) -> None:
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, raw_password: str) -> None:
        validate_password_strength(raw_password)
        self._hashed_password = hash_password(raw_password)

    def verify_password(self, raw_password: str) -> bool:
        return verify_password(raw_password, self._hashed_password)

    @validates("email")
    def validate_email(self, key, value):
        return validate_email(value.lower())


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    avatar = Column(String, nullable=True)
    gender = Column(Enum(GenderEnum), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    info = Column(Text, nullable=True)

    user = Relationship("User", back_populates="profile")

    def __repr__(self):
        return (
            f"<UserProfileModel(id={self.id}, first_name={self.first_name}, last_name={self.last_name}, "
            f"gender={self.gender}, date_of_birth={self.date_of_birth})>"
        )


class Token(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=1),
    )


class ActivationToken(Token):
    __tablename__ = "activation_tokens"

    user = Relationship("User", back_populates="activation_token")
    __table_args__ = (UniqueConstraint("user_id"),)

    def __repr__(self):
        return f"<ActivationTokenModel(id={self.id}, token={self.token}, expires_at={self.expires_at})>"


class PasswordResetToken(Token):
    __tablename__ = "password_reset_tokens"

    user = Relationship("User", back_populates="password_reset_token")
    __table_args__ = (UniqueConstraint("user_id"),)

    def __repr__(self):
        return f"<PasswordResetTokenModel(id={self.id}, token={self.token}, expires_at={self.expires_at})>"


class RefreshToken(Token):
    __tablename__ = "refresh_tokens"

    user = Relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshTokenModel(id={self.id}, token={self.token}, expires_at={self.expires_at})>"
