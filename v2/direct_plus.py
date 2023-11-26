import base64
import json
import logging
import random
from enum import Enum
from pathlib import Path

from v2.exceptions import SubscriberTypeException, NoEndpointException, ContractTypeException, ProductStatusException, \
    KeyTypeException

from v2.endpoints import EndpointFactory, Endpoint
from v2.request import DirectPlusRequest
from v2.session import DirectPlusSession


DataBlocksVerions = {
    'hierarchyconnections': 1,
    'principalscontacts': 1,
    'companyinfo': 1,
    'companyentityresolution': 1,
    'globalfinancials': 1,
}

class DirectPlus:
    """
    This class is used to access the Direct+ API.
    """
    def __init__(self, api_key: str, api_secret: str, *flags):
        self.log = logging.getLogger(__name__)
        self.endpoints = {}
        self.rate = '0.3'
        self.base_endpoint = 'https://plus.dnb.com/'

        self._load_endpoints()

        self._validate_credentials(api_secret, api_key)
        self.log.debug("secret validated.")
        self.key = api_key
        self.secret = api_secret

        self.key_64 = base64.b64encode(bytes(f"{self.key}:{self.secret}", 'utf-8')).decode('utf-8')
        self.session = DirectPlusSession(self.key_64)
        self.flags = {flag: True for flag in flags if isinstance(flag, str)}
        self._validate_session()

    def _load_endpoints(self):
        def add_endpoint(endpoint: Endpoint):
            if endpoint is None:
                return
            key = f'{endpoint.method} {endpoint.name}'
            if key in self.endpoints.keys():
                raise ValueError(f"Endpoint {endpoint.url()} already exists.")
            self.endpoints[key] = endpoint
            self.log.debug(f"Added endpoint {endpoint.name}.")

        endpoint_spec_files = [file for file in Path(f"{Path(__file__).parent}/specs").iterdir() if file.is_file()]

        for file in endpoint_spec_files:
            specs = json.load(open(file, 'r', encoding='UTF8'))

            for endpoint_class in EndpointFactory(specs):
                add_endpoint(endpoint_class)

    @staticmethod
    def _validate_hex_64(string):
        """
        Validates a string to be 64 characters long and hexadecimal.

        :param string:
        :return:
        """
        if not isinstance(string, str):
            raise TypeError(f"String must be of type str, not {type(string)}")
        if len(string) != 64:
            raise ValueError(f"String must be 64 characters long, not {len(string)}")
        if not all(c in '0123456789abcdef' for c in string):
            raise ValueError(f"String must be hexadecimal, not {string}")

    def _validate_secret(self, secret):
        """
        Validates the api secret.

        :param secret:
        :return:
        """
        self._validate_hex_64(secret)

    def _validate_key(self, key):
        """
        Validates the api key.

        :param key:
        :return:
        """
        self._validate_hex_64(key)

    def _validate_credentials(self, secret, key):
        """
        Validates the api credentials.

        :param secret:
        :param key:
        :return:
        """
        self._validate_secret(secret)
        self._validate_key(key)

    def _validate_session(self):
        """
        Validates the session.

        :return:
        """
        if not isinstance(self.session, DirectPlusSession):
            raise TypeError(f"Session must be of type DirectPlusSession, not {type(self.session)}")

        if not self.flags.get('SKIP_ENTITLEMENT_CHECK', False):
            entitlements = self.entitlements
            if not entitlements:
                raise NoEndpointException(f"Session is not entitled to any endpoints.")

            if entitlements.get('subscriber', {}).get('subscriberType') == 'Internal' and not self.flags.get('ALLOW_INTERNAL', False):
                raise SubscriberTypeException(f"Internal subscribers are not allowed. Add the flag ALLOW_INTERNAL to allow internal subscribers.")

            if entitlements.get('subscriber', {}).get('subscriberType') == 'External' and not self.flags.get('DISALLOW_EXTERNAL', False):
                raise SubscriberTypeException(f"External subscribers are not allowed. Remove the flag DISALLOW_EXTERNAL to allow external subscribers.")

            if entitlements.get('product', {}).get('contractType') == 'Trial' and not self.flags.get('ALLOW_TRIAL', False):
                raise ContractTypeException(f"Trial contracts are not allowed. Add the flag ALLOW_TRIAL to allow trial contracts.")

            if entitlements.get('product', {}).get('status') != 'Active':
                raise ProductStatusException(f"Product status is not active.")

            key_type = entitlements.get('apiKey', {}).get('keyType', False)
            if not self.flags.get(key_type.upper(), False):
                raise KeyTypeException(f"Key type has to have a matching flag. Set the flag {key_type.upper()} to allow the key type '{key_type}'.")

    @property
    def entitlements(self):
        """
        Returns the entitlements of the session.

        :return:
        """
        if not hasattr(self, '_entitlements'):
            self._entitlements = self.call_endpoint('entitlements').json()
        return self._entitlements

    @property
    def accesible_data_blocks_and_products(self):
        """
        Returns the accessible data blocks of the session.

        :return:
        """
        if not hasattr(self, '_accesible_data_blocks'):
            self._accesible_data_blocks = [ent.get('entitlementID') for ent in self.entitlements.get('entitlements', []) if len(ent.get('levels')) > 0]
        return self._accesible_data_blocks

    @property
    def get_all_data_block_ids(self):
        """
        Returns all data block ids.

        :return:
        """
        if not hasattr(self, '_all_data_block_ids'):
            block_ids = []
            entitlement_ids = self.accesible_data_blocks_and_products
            for ent_id in entitlement_ids:
                try:
                    version = f'_v{DataBlocksVerions.get(ent_id)}'
                except ValueError:
                    version = ''
                self.log.debug(f'Version is: {version}')
                for level in self.entitlements.get('entitlements', []):
                    for block in level.get('levels', []):
                        block_ids.append(f'{ent_id}_{block}{version}')
            self._all_data_block_ids = block_ids
        return self._all_data_block_ids

    def get_all_avaiable_data_for_duns(self, duns):
        """
        Returns all data available for a duns number.

        :param duns:
        :return:
        """
        return self.call_endpoint(
            'dataBlocks',
            dunsNumber=duns,
            blockIDs=','.join([
                item for item in self.get_all_data_block_ids if '_v' in item
            ])
        ).json()


    def call_endpoint(self, endpoint_id, method='GET', **kwargs):
        """
        Calls an endpoint by id.

        :param endpoint_id:
        :param kwargs:
        :return:
        """
        self.log.debug(f"Calling endpoint {endpoint_id} with kwargs {kwargs}")
        if endpoint_id not in self.endpoints.keys():
            end_key = [end for end in self.endpoints.keys() if end.split(' ')[1] == endpoint_id]
            if len(end_key) != 1:
                raise ValueError(f"Endpoint {endpoint_id} does not exist.")
            end_key = end_key[0]
        else:
            end_key = endpoint_id

        self.check_endpoint_access(end_key.split(' ')[1])
        endpoint = self.endpoints[end_key]

        return DirectPlusRequest(self.session, endpoint, **kwargs).send()

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

        return self.call_endpoint('POST multiProcessJobSubmissionv2', 'POST', **parameters)

    def check_endpoint_access(self, endpoint):
        """
        Checks if the session is entitled to an endpoint.

        :param endpoint:
        :return:
        """
        if endpoint in ['entitlements', 'dataBlocks']:
            return
        if endpoint not in self.accesible_data_blocks_and_products:
            raise NoEndpointException(f"Session is not entitled to endpoint {endpoint}.")