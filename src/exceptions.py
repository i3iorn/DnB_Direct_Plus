from requests import HTTPError


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


class EntitlementAccessException(Exception):
    pass


class SearchException(Exception):
    pass


class SearchParameterException(SearchException):
    pass


class RetryException(Exception):
    pass


class EmptySearchException(Exception):
    pass


class RequestPayloadException(HTTPError):
    pass


class AuthorizationError(HTTPError):
    pass


class DataException(Exception):
    pass


class DunsException(DataException):
    pass


class CSVExportError(Exception):
    pass


class FlattenerError(Exception):
    pass


class CSVExporterError(RuntimeError):
    pass


class MatchException(DirectPlusException):
    pass


class XLSXExportError(RuntimeError):
    pass