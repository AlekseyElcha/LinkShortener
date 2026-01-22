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


class ShortURLToDeleteNotFoundHistoryClear(ShortenerBaseException):
    pass


class SendEmailError(ShortenerBaseException):
    pass


class CreateResetPasswordLinkError(ShortenerBaseException):
    pass


class CreateEmailValidationLinkError(ShortenerBaseException):
    pass


class UserNotFoundError(ShortenerBaseException):
    pass


class UserIdByLoginNotFoundError(ShortenerBaseException):
    pass


class SetSlugExpirationDateError(ShortenerBaseException):
    pass


class ShortLinkExpired(ShortenerBaseException):
    pass


class RemoveSlugExpirationDateError(ShortenerBaseException):
    pass


class UserIdBySlugNotFoundError(ShortenerBaseException):
    pass


class ShortLinkIsProtected(ShortenerBaseException):
    pass