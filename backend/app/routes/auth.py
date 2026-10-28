from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserOut
from backend.app.services.categories import seed_categories
from backend.app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    seed_categories(db)
    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        current_balance=payload.current_balance,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None and payload.email.lower() == "demo@finpulse.ai" and payload.password == "demo":
        seed_categories(db)
        user = User(
            email="demo@finpulse.ai",
            hashed_password=hash_password("demo"),
            full_name="FinPulse Demo User",
            current_balance=25000.0,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if user and user.email == "demo@finpulse.ai" and user.hashed_password == "demo" and payload.password == "demo":
        user.hashed_password = hash_password("demo")
        db.commit()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id, user.email))
