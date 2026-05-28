from hashlib import sha256
from secrets import token_urlsafe


def create_raw_session_token() -> str:
    return token_urlsafe(32)


def hash_session_token(raw_token: str) -> str:
    return sha256(raw_token.encode("utf-8")).hexdigest()
