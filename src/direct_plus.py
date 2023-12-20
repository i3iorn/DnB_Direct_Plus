import base64
import json
import logging
import math
import time
from pathlib import Path

import requests
from requests import HTTPError

# Import only the necessary exceptions from exceptions module
from src.access_manager import AccessManager
from src.endpoints import EndpointFactory, Endpoint
from src.decorators import log_args
from src.request import DirectPlusRequest
from src.exceptions import EmptySearchException
from src.session import DirectPlusSession


class SearchCandidateCountException(Exception):
    pass


class DirectPlus:
    API_SPECS_DIR = Path(Path(__file__).parent / 'specs')

    def __init__(self, api_credentials, *flags):
        """
        Initializes the DirectPlus object. Raises a ValueError if the credentials are invalid.
        :param api_credentials:
        :param flags:
        """
        self.log = logging.getLogger(__name__)
        self.endpoints = {}
        self.rate = '0.3'

        self._load_endpoints()
        self._validate_credentials(api_credentials)
        self.key = api_credentials.get('key', '')
        self.secret = api_credentials.get('secret', '')

        self.key_64 = base64.b64encode(bytes(f"{self.key}:{self.secret}", 'utf-8')).decode('utf-8')
        self.flags = {flag: True for flag in flags if isinstance(flag, str)}
        self.session = DirectPlusSession(self.key_64, self.flags)

        self.access_manager = AccessManager(self.session, self.endpoints, **self.flags)

    @log_args
    def _add_endpoint(self, endpoint: Endpoint):
        """
        Adds an endpoint to the endpoints dictionary. Raises a ValueError if the endpoint already exists.

        :param endpoint:
        :return:
        """
        if endpoint is None:
            return
        key = f'{endpoint.method} {endpoint.name}'
        if key in self.endpoints:
            raise ValueError(f"Endpoint {endpoint.url()} already exists.")
        self.endpoints[key] = endpoint
        self.log.debug(f"Added endpoint {endpoint.name}.")

    @log_args
    def _load_endpoints(self):
        """
        Loads all endpoints from the API_SPECS_DIR directory. Raises a ValueError if an endpoint already exists.

        :return:
        """
        endpoint_spec_files = [file for file in self.API_SPECS_DIR.iterdir() if file.is_file()]

        for file in endpoint_spec_files:
            specs = self._load_endpoint_specs(file)

            for endpoint_class in EndpointFactory(specs):
                self._add_endpoint(endpoint_class)

    @staticmethod
    def _load_endpoint_specs(file_path):
        """
        Reads and returns the specifications from a given file path.

        :param file_path:
        :return:
        """
        with open(file_path, 'r', encoding='UTF8') as f:
            return json.load(f)

    @log_args
    def _validate_hex_64(self, string):
        """
        Validates a string as a 64 character hex string. Raises a ValueError if the string is invalid.

        :param string:
        :return:
        """
        if any(c not in 'abcdef0123456789' for c in string.lower()):
            raise ValueError(f"String {string} is not a valid hex string.")
        if len(string) != 64:
            raise ValueError(f"String {string} is not 64 characters long.")

    @log_args
    def _validate_secret_key(self, secret: str, key: str) -> None:
        """
        Validates the secret and key passed to the constructor. Raises a ValueError if the secret or key are invalid.

        :param secret:
        :param key:
        :return:
        """
        self._validate_hex_64(secret)
        self._validate_hex_64(key)

    @log_args
    def _validate_credentials(self, api_credentials: dict) -> None:
        """
        Validates the credentials passed to the constructor. Raises a ValueError if the credentials are invalid.

        :param api_credentials:
        :return:
        """
        self._validate_secret_key(api_credentials.get('secret', ''), api_credentials.get('key', ''))

    @log_args
    def enrich_duns(self, duns: str, blockIDs: str) -> requests.Response:
        """
        Returns all data available for a duns number.

        :param duns:
        :return:
        """
        return self.call(
            'dataBlocks',
            dunsNumber=duns,
            blockIDs=blockIDs
        ).json()

    @log_args
    def call(self, endpoint_id: str, **kwargs) -> requests.Response:
        """
        Calls an endpoint by id.

        :param endpoint_id:
        :param kwargs:
        :return:
        """
        # self.log.debug(f"Calling endpoint {endpoint_id} with kwargs {kwargs.keys()}")
        if endpoint_id not in self.endpoints.keys():
            end_key = [end for end in self.endpoints.keys() if end.split(' ')[1] == endpoint_id]
            if len(end_key) != 1:
                raise ValueError(f"Endpoint {endpoint_id} does not exist.")
            end_key = end_key[0]
        else:
            end_key = endpoint_id

        self.check_endpoint_access(end_key.split(' ')[1])
        endpoint = self.endpoints[end_key]

        return DirectPlusRequest(self.session, endpoint, self.access_manager, **kwargs).send()

    @log_args
    def multiprocess_submit(self) -> requests.Response:
        """
        Multi-Process Company Entity Resolution identifies the most likely match for the given criteria. The response content for each record, if a match is found, is same as for transactional Company Entity Resolution API.

        Data Coverage: Global
        Note: This API is available as part of "Company Entity Resolution" Non Standard Data Blocks.

        :return:
        """
        parameters = {
            'body': {
                # 'customerKey': ''.join(random.choices('abcdef012346789', k=64))
                'customerKey': 'c1f49b200b011be73ebdcdafa83d8f36240bd889e4cea80c28d6a978a2b77420',
                'processId': 'match',
                'processVersion': 'v1',
                'inputFileName': 'my_test_file.csv',
                'blockIDs': 'companyinfo_L1_v1',
                'jobParameters': {
                    'confidenceLowerLevelThresholdValue': 8
                }
            }}

        return self.call('POST multiProcessJobSubmissionv2', **parameters)

    @log_args
    def check_endpoint_access(self, endpoint: str) -> None:
        """
        Checks if the session is entitled to an endpoint.

        :param endpoint:
        :return:
        """
        # TODO: Implement
        pass

    @log_args
    def upward_family_tree(self, duns: str) -> requests.Response:
        """
        Returns the upward family tree for a duns number.

        :param duns:
        :return:
        """
        return self.call('familyTreeUpward', duns=duns).json()

    @log_args
    def full_family_tree(self, duns: str) -> requests.Response:
        """
        Returns the full family tree for a duns number.

        :param duns:
        :return:
        """
        return self.call('familyTreeFull', duns=duns).json()

    @log_args
    def get_category_codes(self, code: int) -> list:
        """
        Returns a list of industry codes for a given code.

        :param code: Industry code type id.
        :return:
        """
        return self.call('refdataCodes', id=code).json()

    @log_args
    def match(self, **kwargs) -> requests.Response:
        """
        Returns the best match for a given set of criteria.

        :param kwargs:
        :return:
        """
        score_cutoff = kwargs.pop('confidenceLowerLevelThresholdValue', 8)
        return self.call('IDRCleanseMatch', **kwargs)

    @log_args
    def get_company_info(self, **parameters) -> requests.Response:
        """
        Returns company information for a given duns number.

        :param duns:
        :return:
        """
        pass

