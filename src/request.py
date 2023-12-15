import logging

import requests
from typing import TYPE_CHECKING

from requests import HTTPError

from src.endpoints import Endpoint
from src.error_handler import ErrorHandler
from src.session import DirectPlusSession

if TYPE_CHECKING:
    from src.access_manager import AccessManager


class DirectPlusRequest:
    """
    Creates a request object and validates input
    """
    def __init__(self, session: DirectPlusSession, endpoint: Endpoint, access_manager: 'AccessManager', **kwargs):
        self.log = logging.getLogger(__name__)
        self.log.debug("Initializing Direct+ request.")

        self.session = session
        self.access_manager = access_manager
        self.endpoint = endpoint

        for key, value in kwargs.items():
            self.endpoint.add_parameter(key, value)

    def send(self) -> requests.Response:
        self.log.debug(f"Sending {self.endpoint.method} request to {self.endpoint.url}")
        method_function = getattr(self.session, self.endpoint.method.lower())
        method_parameters = {'url': self.endpoint.url()}
        if self.endpoint.method == 'POST':
            method_parameters['json'] = self.endpoint.query_params()
        elif self.endpoint.method == 'GET':
            method_parameters['params'] = self.endpoint.query_params()

        self.log.debug(f"Request parameters: {method_parameters.keys()}")

        response = method_function(**method_parameters)
        eh = ErrorHandler(response)
        if eh.has_error():
            eh.handle_error()

        self.store_response(response)
        return response

    def store_response(self, response) -> None:
        pass

