class DirectPlusException(Exception):
    pass


class AccessException(DirectPlusException):
    pass


class SubscriberTypeException(AccessException):
    pass


class TrialAccessException(AccessException):
    pass


class MissingQueryParameterException(Exception):
    pass


class InactiveAccountException(AccessException):
    pass


class DevelopmentKeyException(Exception):
    pass


class NoEndpointException(Exception):
    pass


class ContractTypeException(Exception):
    pass


class ProductStatusException(Exception):
    pass


class KeyTypeException(Exception):
    pass
