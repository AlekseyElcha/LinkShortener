class ShortenerBaseException(BaseException):
    pass


class SlugAlreadyExistsError(ShortenerBaseException):
    pass


class LongUrlNotFoundError(ShortenerBaseException):
    pass


class CriticalDatabaseError(ShortenerBaseException):
    pass


class RedirectsHistoryNull(ShortenerBaseException):
    pass


class AddRedirectHistoryToDatabaseError(ShortenerBaseException):
    pass
