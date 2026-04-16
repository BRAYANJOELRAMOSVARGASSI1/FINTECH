"""
api/v1/auth_routes.py -- Endpoints de Autenticación.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth import verify_password, create_access_token, create_refresh_token
from app.database import get_db
from app.models.user import User
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Autenticación"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Autentica al usuario y devuelve un token JWT.
    
    Es requerido para invocar cualquier endpoint que guarde o lea
    información corporativa desde la base de datos PostgreSQL.
    """
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(user_id=user.id, role=user.role, company_id=user.company_id)
    refresh_token = create_refresh_token(user_id=user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }
