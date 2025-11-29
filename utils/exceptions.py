from typing import Optional, Any

from fastapi import HTTPException

from .errors import ErrorCode


class AppException(HTTPException):
    def __init__(
            self,
            message: str = None,
            status_code: int = 500,
            code: ErrorCode = ErrorCode.UNKNOWN,
            meta: Optional[dict[str, Any]] = None
    ):
        detail: dict[str, Any] = {
            "message": message,
            "code": code,
            "meta": meta or {},
        }
        super().__init__(status_code=status_code, detail=detail)