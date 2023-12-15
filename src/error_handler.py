import logging
from typing import TYPE_CHECKING

from src.exceptions import RequestPayloadException, AuthorizationError, DunsException

if TYPE_CHECKING:
    from requests import Response


class ErrorHandler:
    def __init__(self, response: 'Response') -> None:
        self._reason = None
        self._status_code = None
        self.log = logging.getLogger(__name__)
        self._response = response

    @property
    def response(self) -> 'Response':
        return self._response

    @property
    def status_code(self) -> int:
        if self._status_code is not None:
            return self._status_code
        return self.response.status_code

    @status_code.setter
    def status_code(self, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError(f"Status code must be an integer, not {type(value)}")
        if not 100 <= value <= 599:
            raise ValueError(f"Status code must be between 100 and 599, not {value}")
        self._status_code = value

    @property
    def reason(self) -> str:
        if self._reason is not None:
            return self._reason
        return self.response.reason

    @reason.setter
    def reason(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError(f"Reason must be a string, not {type(value)}")
        self._reason = value

    @property
    def dnb_error_code(self) -> str:
        return self.response.json().get('error', {}).get('errorCode', '')

    @property
    def dnb_error_message(self) -> str:
        return self.response.json().get('error', {}).get('errorMessage', '')

    def has_error(self) -> bool:
        return self.status_code >= 400 or self.response.json().get('error', False)

    def handle_error(self) -> None:
        try:
            func_ = getattr(self, f"handle_{self.status_code}")
        except AttributeError:
            func_ = self.handle_
        func_()

    def handle_(self) -> None:
        raise ValueError(f"{self.reason}: {self.response.json().get('error', {})}")

    def handle_400(self) -> None:
        raise RequestPayloadException(f"{self.reason}")

    def handle_401(self) -> None:
        raise AuthorizationError(f"{self.reason}")

    def handle_404(self) -> None:
        if self.dnb_error_code == '10001':
            raise DunsException(self.dnb_error_message)
        raise ValueError(f"{self.reason}: {self.response.json().get('error', {})}")

    def handle_410(self) -> None:
        if self.response.json().get('error', {}).get('errorCode') == '40002':
            raise DunsException(self.dnb_error_message)
        raise ValueError(f"{self.reason}: {self.response.json().get('error', {})}")

    def handle_500(self) -> None:
        fault = self.response.json().get('error', {}).get('fault', {})
        if fault.get('faultstring', '').startswith('Error parsing request payload'):
            self.status_code = 400
            self.reason = f'Request payload is malformed or empty.'
            self.handle_400()
        raise ValueError(f"Internal server error: {self.response.json().get('error', {}).get('fault', {})}")
