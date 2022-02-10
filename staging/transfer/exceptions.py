
class BaseTransferException(Exception):
    pass


class TransferNotFound(BaseTransferException):
    """ Raised when transfer request not found in db"""
    pass

class TransferError(BaseTransferException):
    """ Raised when transfer fails"""
    pass

class TransferInvalidParameter(BaseTransferException):
    """ Raised when transfer fails"""
    pass

class TransferUnauthorized(BaseTransferException):
    """ Raised when transfer is not authorized"""
    pass