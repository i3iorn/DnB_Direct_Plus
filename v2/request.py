import logging

import requests
from typing import TYPE_CHECKING

from exceptions import EntitlementAccessException
from v2.endpoints import Endpoint
from v2.session import DirectPlusSession

if TYPE_CHECKING:
    from v2.access_manager import AccessManager

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
        self.log.debug(f"Endpoint: {endpoint.url()}")

        for key, value in kwargs.items():
            self.endpoint.add_parameter(key, value)

    def send(self):
        self.log.debug(f"Sending {self.endpoint.method} request to {self.endpoint.url}")
        method_function = getattr(self.session, self.endpoint.method.lower())
        medthod_parameters = {'url': self.endpoint.url()}
        if self.endpoint.method == 'POST':
            medthod_parameters['json'] = self.endpoint.query_params()
        elif self.endpoint.method == 'GET':
            medthod_parameters['params'] = self.endpoint.query_params()

        response = method_function(**medthod_parameters)
        self.store_response(response)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self.handle_error(response, e)

        return response

    def store_response(self, response):
        pass

    def handle_error(self, response, e):
        self.log.debug(f"Handling error: {response.text}")
        if response.status_code == 400:
            if response.json().get('error').get('errorCode') == '11001':
                raise requests.exceptions.HTTPError(f"Unauthorized: {response.json().get('error').get('errorDetails')}") from e
        elif response.status_code == 401:
            if response.json().get('error').get('errorCode') == '00040':
                pass
            if response.json().get('error').get('errorCode') == '00004':
                raise EntitlementAccessException(f"Unauthorized: {response.json().get('error').get('errorMessage')}") from e

        raise requests.exceptions.HTTPError(f"Unknown error: {response.json().get('error').get('errorDetails')}") from e
