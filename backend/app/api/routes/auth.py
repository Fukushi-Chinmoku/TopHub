from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status

from app.api.deps import get_auth_service, get_current_user
from app.config import settings
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserOut
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        user = await auth_service.register(
            login=payload.login,
            password=payload.password,
            display_name=payload.display_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return AuthResponse(user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        user, raw_token = await auth_service.login(
            login=payload.login,
            password=payload.password,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials") from exc

    response.set_cookie(
        key=settings.session_cookie_name,
        value=raw_token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        max_age=settings.session_max_days * 24 * 60 * 60,
    )
    return AuthResponse(user=UserOut.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    session_id: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    await auth_service.logout(session_id)
    response.delete_cookie(settings.session_cookie_name)


@router.get("/me", response_model=AuthResponse)
async def me(current_user: User = Depends(get_current_user)) -> AuthResponse:
    return AuthResponse(user=UserOut.model_validate(current_user))
