class ShortenerBaseException(BaseException):
    pass


class SlugAlreadyExistsError(ShortenerBaseException):
    pass


class LongUrlNotFoundError(ShortenerBaseException):
    pass