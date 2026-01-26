from string import ascii_letters
from validators import url as url_validator, ValidationError

letters = ascii_letters + "цукенгшщзхъфывапролджэячсмитьбюёЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮЁ"
numbers = "0123456789"
symbols = ["-", "_"]

def validate_custom_slug(slug: str):
    if all((i in letters) or (i in symbols) or (i in numbers) for i in slug):
        return True
    else:
        return False



def validate_url(url: str):
    if ("http://" not in url[:7]) and ("https://" not in url[:8]):
        url = "https://" + url
    try:
        res = url_validator(url)
        if res is True:
            return url
        else:
            return False
    except:
        return False

