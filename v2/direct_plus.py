import base64
import json
import logging
import math
import time
from pathlib import Path

from requests import HTTPError

# Import only the necessary exceptions from exceptions module
from v2.access_manager import AccessManager
from v2.endpoints import EndpointFactory, Endpoint
from v2.request import DirectPlusRequest, EmptySearchException
from v2.session import DirectPlusSession


class SearchCandidateCountException(Exception):
    pass


class DirectPlus:
    API_SPECS_DIR = Path(Path(__file__).parent / 'specs')

    # Extracted the credentials validation logic into a separate method
    def __init__(self, api_credentials, *flags):
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

    # Load endpoints method is now private, no need for staticmethod decorator
    def _load_endpoints(self):
        def add_endpoint(endpoint: Endpoint):
            if endpoint is None:
                return
            key = f'{endpoint.method} {endpoint.name}'
            if key in self.endpoints:
                raise ValueError(f"Endpoint {endpoint.url()} already exists.")
            self.endpoints[key] = endpoint
            self.log.debug(f"Added endpoint {endpoint.name}.")

        endpoint_spec_files = [file for file in self.API_SPECS_DIR.iterdir() if file.is_file()]

        for file in endpoint_spec_files:
            with open(file, 'r', encoding='UTF8') as f:
                specs = json.load(f)

            for endpoint_class in EndpointFactory(specs):
                add_endpoint(endpoint_class)

    # Removed the staticmethod decorator, as it's no longer static
    def _validate_hex_64(self, string):
        if any(c not in 'abcdef0123456789' for c in string.lower()):
            raise ValueError(f"String {string} is not a valid hex string.")
        if len(string) != 64:
            raise ValueError(f"String {string} is not 64 characters long.")

    # Combined validate_secret and validate_key into a single method
    def _validate_secret_key(self, secret, key):
        self._validate_hex_64(secret)
        self._validate_hex_64(key)

    def _validate_credentials(self, api_credentials):
        self._validate_secret_key(api_credentials.get('secret', ''), api_credentials.get('key', ''))

    def enrich_duns(self, duns, blockIDs):
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

    def call(self, endpoint_id, **kwargs):
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

    def multiprocess_submit(self) -> bool:
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

    def check_endpoint_access(self, endpoint):
        """
        Checks if the session is entitled to an endpoint.

        :param endpoint:
        :return:
        """
        # TODO: Implement
        pass

    def upward_family_tree(self, duns):
        """
        Returns the upward family tree for a duns number.

        :param duns:
        :return:
        """
        return self.call('familyTreeUpward', duns=duns).json()

    def full_family_tree(self, duns):
        """
        Returns the full family tree for a duns number.

        :param duns:
        :return:
        """
        return self.call('familyTreeFull', duns=duns).json()

    def get_industry_codes(self, code):
        """
        Returns a list of industry codes for a given code.

        :param code:
        :return:
        """
        return self.call('refdataCodes', id=code).json()