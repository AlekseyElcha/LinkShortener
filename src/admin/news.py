from fastapi import APIRouter, HTTPException, status, Body
from fastapi.responses import HTMLResponse
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/admin/news")

@router.post("/create_news")
def render_html_content(
        html_code: Annotated[str, Body(embed=True)],
        # session: AsyncSession
):
    return html_code