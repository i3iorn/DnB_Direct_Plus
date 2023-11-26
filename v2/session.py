import json
import logging
from time import time

import requests


class DirectPlusSession(requests.Session):
    """
    Establish a session with the Direct+ API.
    """
    def __init__(self, key_64: str):
        super().__init__()
        self.log = logging.getLogger(__name__)
        self.log.debug("Initializing Direct+ session.")

        self.access_token, self.access_token_expires = self._get_access_token(key_64)
        self.log.debug(f"Access token expires in {self.access_token_expires - time()} seconds.")

        self.log.debug("Setting session headers.")
        self.headers.update({
            'accept': "application/json;charset=utf-8",
            'authorization': f"Bearer {self.access_token}",
        })

    def _get_access_token(self, key_64):
        auth_address = 'https://plus.dnb.com/v2/token'

        self.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Basic {key_64}',
            'Cache-Control': 'no-cache'
        })
        self.log.debug("Requesting access token.")
        self.log.debug(f"Headers: {self.headers}")
        self.log.debug(f"Address: {auth_address}")
        response = self.post(auth_address, json.dumps({
            "grant_type": "client_credentials"
        }))

        self.log.debug(f"Response: {response}")
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self.handle_error(e)
        token = json.loads(response.text)['access_token']
        self.log.debug(f"Access token aquired")
        expires = time() + json.loads(response.text)['expiresIn']
        return token, expires

    def handle_error(self, e):
        self.log.error(f"Request failed with status code {e.response.status_code}")
        self.log.error(e.response.request.body)
        self.log.error(e.response.text)
        raise requests.exceptions.HTTPError from e
