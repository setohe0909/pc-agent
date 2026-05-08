from fastapi import Header, HTTPException, status

from app.adapters.config.settings import settings


async def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    if not settings.admin_api_token or settings.admin_api_token == "change-me-admin-token":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_API_TOKEN debe configurarse antes de habilitar acciones administrativas.",
        )
    if x_admin_token != settings.admin_api_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token administrativo invalido.")
