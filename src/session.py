import json
import logging
from time import time

import requests

from src.decorators import timeit


class DirectPlusSession(requests.Session):
    """
    Establish a session with the Direct+ API.
    """
    def __init__(self, key_64: str, flags) -> None:
        """
        Initialize the session. Get an access token and set the session headers.

        :param key_64:
        :param flags:
        """
        super().__init__()
        self.log = logging.getLogger(__name__)
        self.key_64 = key_64
        self.log.debug("Initializing Direct+ session.")

        self.access_token, self.access_token_expires = self._get_access_token(key_64)
        self.log.debug(f"Access token expires in {self.access_token_expires - time()} seconds.")

    @property
    def access_token(self) -> str:
        """
        Get the access token.

        :return:
        """
        return self._access_token

    @access_token.setter
    def access_token(self, value: str) -> None:
        """
        Set the access token.

        :param value:
        :return:
        """
        self._access_token = value

    def refresh_access_token_if_necessary(self) -> None:
        """
        Refresh the access token if it has expired.

        :return:
        """
        if time() > self.access_token_expires:
            self.access_token, self.access_token_expires = self._get_access_token(self.key_64)
            self.log.debug(f"Access token expires in {self.access_token_expires - time()} seconds.")

    def _get_access_token(self, key_64: str) -> (str, int):
        """
        Get an access token from the API.

        :param key_64:
        :return:
        """
        auth_address = 'https://plus.dnb.com/v2/token'

        self.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Basic {key_64}',
            'Cache-Control': 'no-cache'
        })
        self.log.debug("Requesting access token.")
        self.log.debug(f"Address: {auth_address}")
        response = super().post(auth_address, json={
            "grant_type": "client_credentials"
        })

        self.log.debug(f"Response: {response}")
        token = json.loads(response.text)['access_token']
        self.log.debug(f"Access token aquired")
        expires = time() + json.loads(response.text)['expiresIn']

        self.log.debug("Setting session headers.")
        self.headers.update({
            'accept': "application/json;charset=utf-8",
            'authorization': f"Bearer {token}",
        })

        return token, expires

    @timeit
    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Get a response from the API. If the access token has expired, get a new one.

        :param url:
        :param kwargs:
        :return:
        """
        self.refresh_access_token_if_necessary()

        return super().get(url, **kwargs)

    @timeit
    def post(self, url: str, data='', **kwargs) -> requests.Response:
        """
        Post data to the API. If the access token has expired, get a new one.

        :param url:
        :param data:
        :param kwargs: Additional parameters
        :return: A response object
        """
        self.refresh_access_token_if_necessary()

        return super().post(url, timeout=10, **kwargs)
