from fastapi import APIRouter, Request
from typing import Optional, Tuple
import requests

from src.exeptions import NoLocationData

router = APIRouter(prefix="/location")

def get_client_ip(request: Request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip


def get_location_by_ip(ip: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city", timeout=3)
        data = response.json()

        if data.get("status") == "success":
            city = data.get("city")
            country = data.get("country")
            return city, country
    except Exception as e:
        print(f"Error getting location: {e}")

    return None, None


@router.get("/user_location")
async def get_location(request: Request):
    try:
        client_ip = get_client_ip(request)
    except:
        raise NoLocationData

    city, country = get_location_by_ip(client_ip)
    location_str = f"{city}, {country}" if city and country else "Unknown"

    return {
        "ip": client_ip,
        "city": city,
        "country": country,
        "location": location_str,
        "user_agent": request.headers.get("user-agent")
    }

