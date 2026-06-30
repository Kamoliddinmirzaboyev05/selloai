from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, detail: str, code: str, status_code: int = 400, extra: dict | None = None) -> None:
        self.detail = detail
        self.code = code
        self.status_code = status_code
        self.extra = extra or {}
        super().__init__(detail)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        content = {"detail": exc.detail, "code": exc.code}
        content.update(exc.extra)
        return JSONResponse(
            status_code=exc.status_code,
            content=content,
        )
