import json
import logging
from time import time

import requests


class DirectPlusSession(requests.Session):
    """
    Establish a session with the Direct+ API.
    """
    def __init__(self, key_64: str, flags):
        super().__init__()
        self.log = logging.getLogger(__name__)
        self.key_64 = key_64
        self.log.debug("Initializing Direct+ session.")

        self.access_token, self.access_token_expires = self._get_access_token(key_64)
        self.log.debug(f"Access token expires in {self.access_token_expires - time()} seconds.")

    def _get_access_token(self, key_64):
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

    def get(self, url, **kwargs):
        if time() > self.access_token_expires:
            self.access_token, self.access_token_expires = self._get_access_token(self.key_64)
            self.log.debug(f"Access token expires in {self.access_token_expires - time()} seconds.")

        self.log.debug(f"Requesting {url}")
        self.log.debug(f"Headers: {self.headers}")
        self.log.debug(f"Parameters: {kwargs.keys()}")

        return super().get(url, **kwargs)

    def post(self, url, data='', **kwargs):
        if time() > self.access_token_expires:
            self.access_token, self.access_token_expires = self._get_access_token(self.key_64)
            self.log.debug(f"Access token expires in {self.access_token_expires - time()} seconds.")

        return super().post(url, timeout=10, **kwargs)

    def refresh(self):
        self.access_token, self.access_token_expires = self._get_access_token(self.key_64)
        self.log.debug(f"Access token expires in {self.access_token_expires - time()} seconds.")