import string
from secrets import choice

alphabet = string.ascii_letters + "0123456789"

def generate_random_short_url() -> str:
    slug = ""
    for _ in range(6):
        slug += choice(alphabet)
    return slug
