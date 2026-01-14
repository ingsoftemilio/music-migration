# core/exceptions.py
class MusicTransferError(Exception):
    pass


class AuthError(MusicTransferError):
    pass


class NotFoundError(MusicTransferError):
    pass


class RateLimitError(MusicTransferError):
    pass


class ServiceError(MusicTransferError):
    pass