from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.utils.security import decode_access_token, hash_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if token:
        try:
            payload = decode_access_token(token)
            user_id = int(payload.get("sub", "0"))
            user = db.get(User, user_id)
            if user:
                return user
        except Exception:
            pass

    # Provide or create default active demo user for seamless interactive web UI usage
    demo_user = db.query(User).filter(User.email == "demo@finpulse.ai").first()
    if not demo_user:
        demo_user = User(
            email="demo@finpulse.ai",
            hashed_password=hash_password("demo"),
            full_name="FinPulse Demo User",
            current_balance=25000.0,
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
    elif demo_user.hashed_password == "demo":
        demo_user.hashed_password = hash_password("demo")
        db.commit()
    return demo_user
