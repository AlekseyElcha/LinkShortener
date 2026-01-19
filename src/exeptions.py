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


class NoLocationData(ShortenerBaseException):
    pass


class ShortURLToDeleteNotFound(ShortenerBaseException):
    pass


class ShortURLToDeleteNotFoundHistoryClear(ShortURLToDeleteNotFound):
    pass


class SendEmailError(ShortenerBaseException):
    pass


class CreateResetPasswordLinkError(ShortenerBaseException):
    pass


class CreateEmailValidationLinkError(ShortenerBaseException):
    pass


class UserNotFoundError(ShortURLToDeleteNotFound):
    pass


class UserIdByLoginNotFoundError(ShortURLToDeleteNotFound):
    pass


class SetSlugExpirationDate(ShortenerBaseException):
    pass


class ShortLinkExpired(ShortenerBaseException):
    pass
