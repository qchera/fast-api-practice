from datetime import datetime
from typing import Optional, Any

from fastapi import HTTPException, FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from .errors import ErrorCode


class AppException(HTTPException):
    def __init__(
            self,
            message: str = None,
            status_code: int = 500,
            code: ErrorCode = ErrorCode.UNKNOWN,
            meta: dict[str, Any] = None,
    ):
        self.meta = meta or {}
        self.meta["timestamp"] = str(datetime.now())

        error_detail = {
            "message": message,
            "code": code,
            "meta": self.meta,
        }

        super().__init__(status_code=status_code, detail=error_detail)


def _get_exception_handler(
        message: str = None,
        status_code: int = 500,
        code: ErrorCode = ErrorCode.UNKNOWN,
        meta: Optional[dict[str, Any]] = None
):
    def handler(request: Request, exception: Exception) -> Response:
        from rich import print, panel
        print(panel.Panel(f"Handle {exception.__class__.__name__}"))
        if isinstance(exception, HTTPException):
            raise exception
        raise AppException(
            message=message,
            status_code=status_code,
            code=code,
            meta=meta or {},
        )
    return handler


def add_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(Exception, _get_exception_handler(
        'Something went wrong, please try again later',
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.INTERNAL_SERVER_ERROR,
        {},
    ))