from fastapi import FastAPI, HTTPException, Response, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.link_service import LinkService
from logger import logger
import time

def create_app() -> FastAPI:
    app = FastAPI()
    short_link_service = LinkService()

    class PutLink(BaseModel):
        link: str

    def _service_link_to_real(short_link: str) -> str:
        return f"http://localhost:8000/{short_link}"

    @app.post("/link")
    def create_link(put_link_request: PutLink) -> PutLink:
        logger.info(f"Creating short link for: {put_link_request.link}")

        if "https://" not in put_link_request.link:
            put_link_request.link = "https://" + put_link_request.link

        if "." not in put_link_request.link:
            logger.warning(f"Incorrect url: {put_link_request.link}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Valid URL format")

        short_link = short_link_service.create_link(put_link_request.link)
        logger.info(f"Short link created: {short_link}")

        return PutLink(link=_service_link_to_real(short_link))

    @app.get("/{link}")
    def get_link(link: str) -> Response:
        real_link = short_link_service.get_real_link(link)

        if real_link is None:
            logger.warning(f"Short link not found: {link}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short link not found:(")

        logger.info(f"Redirect: {link} → {real_link}")
        return Response(status_code=status.HTTP_301_MOVED_PERMANENTLY, headers={"Location": real_link})

    @app.middleware("http")
    async def process_time(request, call_next) -> Response:
        start_time = time.time()
        response = await call_next(request)
        end_time = time.time()
        process_time_ = round((end_time - start_time) * 1000, 3)

        response.headers["X-Latency"] = f"{process_time_} ms"
        logger.info(f"{request.method} {request.url.path} - {process_time_} ms")
        return response

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled exception at {request.url}: {exc}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,content={"detail": "Internal Server Error"})

    return app
