import logging
from fastapi import FastAPI, HTTPException, Response, status, Request
from pydantic import BaseModel
from services.link_service import LinkService
import time

def create_app() -> FastAPI:
    app = FastAPI()
    print(1)

    @app.middleware("http")
    async def add_process_time_handler(request: Request, call_next) -> Response:
        t0 = time.time()

        response = await call_next(request)

        elapsed_ms = round((time.time() - t0) * 1000, 2)
        response.headers["X-Process-Time"] = str(elapsed_ms)
        logging.debug("{} {} done in {}ms", request.method, request.url, elapsed_ms)

        return response

    short_link_service = LinkService()

    class PutLink(BaseModel):
        link: str

    def _service_link_to_real(short_link: str) -> str:
        return f"http://localhost:8000/{short_link}"

    @app.post("/link")
    def create_link(put_link_request: PutLink) -> PutLink:
        short_link = short_link_service.create_link(put_link_request.link)
        return PutLink(link=_service_link_to_real(short_link))

    @app.get("/{link}")
    def get_link(link: str) -> Response:
        real_link = short_link_service.get_real_link(link)

        if real_link is None:
            logging.debug(f"Long link {link} entered, 404 short link not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short link not found:(")

        return Response(status_code=status.HTTP_301_MOVED_PERMANENTLY, headers={"Location": real_link})

    return app