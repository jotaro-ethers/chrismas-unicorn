from fastapi import Header, HTTPException

from app.config import get_settings


async def verify_sepay_api_key(
    authorization: str = Header(..., alias="Authorization")
) -> str:
    """Verify Sepay API key from Authorization header.
    
    Expected format: "Apikey <api_key>"
    """
    settings = get_settings()
    expected_key = f"Apikey {settings.SEPAY_API_KEY}"
    
    if authorization != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return authorization
