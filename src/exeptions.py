class ShortenerBaseException(BaseException):
    pass


class SlugAlreadyExistsError(ShortenerBaseException):
    pass


class LongUrlNotFoundError(ShortenerBaseException):
    pass


class CriticalDatabaseError(ShortenerBaseException):
    pass
