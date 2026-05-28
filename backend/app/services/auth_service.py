import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.session import Session
from app.models.user import User
from app.security.password import hash_password, verify_password
from app.security.session_tokens import create_raw_session_token, hash_session_token


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, login: str, password: str, display_name: str) -> User:
        self._validate_login(login)
        self._validate_password(password)

        normalized_login = login.strip()
        existing_user = await self.db.scalar(select(User).where(User.login == normalized_login))
        if existing_user is not None:
            raise ValueError("Login already exists")

        user = User(
            login=normalized_login,
            password_hash=hash_password(password),
            display_name=display_name.strip(),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def login(
        self,
        login: str,
        password: str,
        user_agent: str | None,
        ip_address: str | None,
    ) -> tuple[User, str]:
        self._validate_login(login)
        self._validate_password(password)

        normalized_login = login.strip()
        user = await self.db.scalar(select(User).where(User.login == normalized_login))
        if user is None or not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")

        raw_token = create_raw_session_token()
        now = datetime.now(timezone.utc)
        session = Session(
            user_id=user.id,
            token_hash=hash_session_token(raw_token),
            user_agent=(user_agent or "")[:255] or None,
            ip_address=(ip_address or "")[:64] or None,
            last_activity_at=now,
            expires_at=now + timedelta(days=settings.session_max_days),
        )
        self.db.add(session)
        await self.db.commit()
        return user, raw_token

    async def logout(self, raw_token: str | None) -> None:
        if not raw_token:
            return
        token_hash = hash_session_token(raw_token)
        await self.db.execute(delete(Session).where(Session.token_hash == token_hash))
        await self.db.commit()

    async def get_current_user(self, raw_token: str | None) -> User | None:
        if not raw_token:
            return None

        token_hash = hash_session_token(raw_token)
        session = await self.db.scalar(select(Session).where(Session.token_hash == token_hash))
        if session is None:
            return None

        now = datetime.now(timezone.utc)
        idle_ttl = timedelta(minutes=settings.session_idle_minutes)
        if now > session.expires_at or now - session.last_activity_at > idle_ttl:
            await self.db.execute(delete(Session).where(Session.id == session.id))
            await self.db.commit()
            return None

        session.last_activity_at = now
        await self.db.commit()
        user = await self.db.scalar(select(User).where(User.id == session.user_id))
        return user

    @staticmethod
    def _validate_login(login: str) -> None:
        login_pattern = settings.login_regex.replace("\\\\", "\\")
        if not re.fullmatch(login_pattern, login.strip()):
            raise ValueError("Login format is invalid")

    @staticmethod
    def _validate_password(password: str) -> None:
        password_pattern = settings.password_regex.replace("\\\\", "\\")
        if not re.fullmatch(password_pattern, password):
            raise ValueError("Password format is invalid")
