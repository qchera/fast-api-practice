from typing import Annotated

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, HTTPBearer

from ..utils import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/token",
)
'''
class AccessTokenBearer(HTTPBearer):
    async def __call__(self, request):
        auth_creds = await super.__call__(request)
        token = auth_creds.credentials
        token_data = decode_access_token(token)
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        return token_data

access_token_bearer = AccessTokenBearer()
AccessTokenBearerDep = Annotated[dict, Depends(access_token_bearer)]
'''