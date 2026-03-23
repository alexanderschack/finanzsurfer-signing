from typing import Optional
from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user_from_cookie


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(default=None),
) -> User:
    try:
        return get_current_user_from_cookie(db, access_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login"},
        )
