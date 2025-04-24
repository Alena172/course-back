from fastapi import Depends, HTTPException, status
from auth.auth_bearer import JWTBearer

def RoleChecker(allowed_roles: list[str]):
    def checker(payload: dict = Depends(JWTBearer())):
        role = payload.get("role")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission for this action"
            )
        return payload
    return checker
