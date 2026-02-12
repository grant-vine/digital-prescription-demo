"""FastAPI authentication dependencies for protected routes."""

from typing import List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.auth import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db():
    """Placeholder database session dependency.

    Tests will override this with test_session fixture.
    Production will use proper database connection pool.
    """
    raise NotImplementedError("Database session not configured for production yet")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token.

    Args:
        token: JWT access token from Authorization header
        db: Database session

    Returns:
        User object for authenticated user

    Raises:
        HTTPException: 401 if token invalid or user not found

    Example:
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"username": current_user.username}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    user_id_str: str = payload.get("sub")

    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    # Attach tenant_id from JWT for downstream use
    user._jwt_tenant_id = payload.get("tenant_id", "default")

    return user


def require_role(allowed_roles: List[str]) -> Callable:
    """Create a dependency that checks if user has required role.

    Args:
        allowed_roles: List of allowed roles (e.g., ["doctor", "pharmacist"])

    Returns:
        Dependency function that validates user role

    Raises:
        HTTPException: 403 if user role not in allowed_roles

    Example:
        @app.post("/prescriptions")
        async def create_prescription(
            current_user: User = Depends(require_role(["doctor"]))
        ):
            return {"message": "Only doctors can create prescriptions"}
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = str(current_user.role)

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required roles: {', '.join(allowed_roles)}",
            )

        return current_user

    return role_checker
