from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    current_balance: float = Field(default=20000.0, ge=0)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    current_balance: float

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    current_balance: float | None = Field(default=None, ge=0)
