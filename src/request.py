import datetime
import hashlib
import json
import logging
import pickle
from pathlib import Path

import requests
from typing import TYPE_CHECKING

from requests import HTTPError

from src.endpoints import Endpoint
from src.error_handler import ErrorHandler
from src.session import DirectPlusSession

if TYPE_CHECKING:
    from src.access_manager import AccessManager


class RequestHash:
    def __init__(self, method: str, **kwargs):
        self.log = logging.getLogger(__name__)
        self.method = method
        self.kwargs = kwargs
        self.log.trace(f"Request hash path: {self.path.absolute()}")

    def _generate_hash(self):
        m = hashlib.sha256()
        m.update(bytes(self.method, 'utf-8'))
        for key, value in self.kwargs.items():
            m.update(bytes(key, 'utf-8'))
            m.update(bytes(str(value), 'utf-8'))
        return m.hexdigest()

    def cached_response(self) -> requests.Response:
        with open(self.path, 'rb') as f:
            return pickle.load(f)

    @property
    def path(self) -> Path:
        return Path(f"{Path(__file__).parent}/cache/{self._generate_hash()}{datetime.datetime.today().day}.json")

    @property
    def is_cached(self) -> bool:
        return self.path.exists()

    def cache(self, response: requests.Response) -> None:
        if not self.path.parent.exists():
            self.path.parent.mkdir()
        with open(self.path, 'wb') as f:
            pickle.dump(response, f)


class DirectPlusRequest:
    """
    Creates a request object and validates input
    """
    def __init__(self, session: DirectPlusSession, endpoint: Endpoint, access_manager: 'AccessManager', **kwargs):
        self._cached = None
        self.log = logging.getLogger(__name__)
        self.log.debug("Initializing Direct+ request.")

        self.session = session
        self.access_manager = access_manager
        self.endpoint = endpoint

        for key, value in kwargs.items():
            self.endpoint.add_parameter(key, value)

    @property
    def cached(self):
        return self._cached

    def send(self) -> requests.Response:
        self.log.debug(f"Sending {self.endpoint.method} request to {self.endpoint.url}")
        method_function = getattr(self.session, self.endpoint.method.lower())
        method_parameters = {'url': self.endpoint.url()}
        if self.endpoint.method == 'POST':
            method_parameters['json'] = self.endpoint.query_params()
        elif self.endpoint.method == 'GET':
            method_parameters['params'] = self.endpoint.query_params()

        self.log.debug(f"Request parameters: {method_parameters.keys()}")

        hash = RequestHash(method=self.endpoint.method, **method_parameters)
        self.log.trace(f"Request hash: {hash}")
        if hash.is_cached:
            self.log.debug(f"Request is cached. Returning cached response.")
            return hash.cached_response()
        else:
            self.log.debug(f"Request is not cached. Sending request.")
        response = method_function(**method_parameters)
        eh = ErrorHandler(response)
        if eh.has_error():
            eh.handle_error()

        hash.cache(response)
        return response

