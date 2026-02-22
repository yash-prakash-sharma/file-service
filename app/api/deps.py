import httpx
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Validates token against the login-service verify endpoint.
    If valid, returns the user ID.
    Raises 401 Unauthorized if the token is invalid or missing.
    """
    token = None
    if credentials:
        token = credentials.credentials
    elif "token" in request.query_params:
        token = request.query_params.get("token")
        
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # Send GET to /api/auth/verify endpoint of login-service
    verify_url = f"{settings.LOGIN_SERVICE_URL.rstrip('/')}/api/auth/verify"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(verify_url, headers=headers)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Login service is unavailable: {exc}"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials with login service",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # login-service returns {"status": "authenticated", "user_id": current_user.id}
    data = response.json()
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid response format from login service",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user_id
