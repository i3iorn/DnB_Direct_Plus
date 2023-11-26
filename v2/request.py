import logging

import requests

from v2.endpoints import Endpoint
from v2.session import DirectPlusSession


class DirectPlusRequest:
    """
    Creates a request object and validates input
    """
    def __init__(self, session: DirectPlusSession, endpoint: Endpoint, **kwargs):
        self.log = logging.getLogger(__name__)
        self.log.debug("Initializing Direct+ request.")

        self.session = session
        self.endpoint = endpoint
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

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self.log.error(f"Request failed with status code {response.status_code}")
            self.log.error(response.request.__dict__)
            self.log.error(self.endpoint.query_params())
            self.log.error(response.text)
            raise requests.exceptions.HTTPError from e

        self.store_response(response)
        return response

    def store_response(self, response):
        pass
