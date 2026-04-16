"""
auth.py -- Autenticacion JWT y hashing de passwords.

Implementa:
- Hashing seguro con bcrypt (passlib)
- Generacion y verificacion de JWT tokens (python-jose)
- Funciones utilitarias para el flujo de auth
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# ---------------------------------------------------------------------------
# Password Hashing
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Genera hash bcrypt del password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica password contra su hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT Tokens
# ---------------------------------------------------------------------------

ALGORITHM = settings.jwt_algorithm
SECRET_KEY = settings.jwt_secret_key
ACCESS_TOKEN_EXPIRE = timedelta(minutes=settings.jwt_access_token_expire_minutes)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)


def create_access_token(
    user_id: str,
    role: str,
    company_id: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Genera JWT access token con claims del usuario."""
    expire = datetime.now(timezone.utc) + (expires_delta or ACCESS_TOKEN_EXPIRE)
    payload = {
        "sub": user_id,
        "role": role,
        "company_id": company_id,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Genera JWT refresh token (larga duracion)."""
    expire = datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRE
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decodifica y valida un JWT token. Retorna None si es invalido."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def decode_access_token(token: str) -> dict | None:
    """Decodifica un access token y valida que sea de tipo 'access'."""
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        return None
    return payload
