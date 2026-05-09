from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.accounts.models import GenderEnum
from app.validators.accounts import validate_password_strength


class UserBase(BaseModel):
    email: EmailStr


class UserRegistrationRequestSchema(UserBase):
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        validate_password_strength(value)
        return value


class UserLoginRequestSchema(UserBase):
    password: str


class UserActivationRequestSchema(UserBase):
    token: str


class UserRegistrationResponseSchema(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    activation_token: str | None = None


class PasswordResetRequestSchema(UserBase):
    pass


class PasswordResetResponseSchema(BaseModel):
    message: str
    reset_token: str | None = None


class PasswordResetCompleteRequestSchema(UserBase):
    token: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        validate_password_strength(value)
        return value


class TokenRefreshRequestSchema(BaseModel):
    refresh_token: str


class TokenRefreshResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserLoginResponseSchema(TokenRefreshResponseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MessageResponseSchema(BaseModel):
    message: str


class ProfileBase(BaseModel):

    first_name: str | None = None
    last_name: str | None = None
    gender: GenderEnum | None = None
    date_of_birth: date | None = None
    info: str | None = None
    avatar: str | None = None


class ProfileRequestSchema(ProfileBase):
    pass


class ProfileResponseSchema(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
