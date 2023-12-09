import json
import logging
import time

import requests
from typing import TYPE_CHECKING

from requests import HTTPError

from v2.exceptions import EntitlementAccessException
from v2.endpoints import Endpoint
from v2.session import DirectPlusSession

if TYPE_CHECKING:
    from v2.access_manager import AccessManager


class RetryException(Exception):
    pass


class EmptySearchException(Exception):
    pass


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

    def send(self):
        self.log.debug(f"Sending {self.endpoint.method} request to {self.endpoint.url}")
        method_function = getattr(self.session, self.endpoint.method.lower())
        method_parameters = {'url': self.endpoint.url()}
        if self.endpoint.method == 'POST':
            method_parameters['json'] = self.endpoint.query_params()
        elif self.endpoint.method == 'GET':
            method_parameters['params'] = self.endpoint.query_params()

        response = method_function(**method_parameters)
        self.log.debug(f"Response: {response.status_code}")

        self.store_response(response)
        return response

    def store_response(self, response):
        pass

