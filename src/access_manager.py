import logging
from typing import List

from src.exceptions import (
    SubscriberTypeException,
    NoEndpointException,
    ContractTypeException,
    ProductStatusException,
    KeyTypeException,
    TrialAccessException,
    InactiveAccountException,
    DevelopmentKeyException, AuthorizationError
)
from src.request import DirectPlusRequest
from src.session import DirectPlusSession


class AccessManager:
    def __init__(self, session: DirectPlusSession, endpoints: dict, **flags):
        self._entitlements = None
        self.log = logging.getLogger(__name__)
        self.session = session
        self.flags = flags
        self.endpoints = endpoints
        self.connection_is_valid = False

        if not self.flags.get('SKIP_ENTITLEMENT_CHECK', False):
            self._validate_connection()

    def _validate_connection(self) -> None:
        entitlements = self.get_entitlements()
        if entitlements.get('error', False):
            raise NoEndpointException("Session is not entitled to the entitlement endpoint.")

        self._validate_subscriber_type(entitlements)
        self._validate_contract_type(entitlements)
        self._validate_product_status(entitlements)
        self._validate_key_type(entitlements)
        self._validate_session_type(entitlements)

        self.connection_is_valid = True

    def _validate_subscriber_type(self, entitlements: dict) -> None:
        subscriber_type = entitlements.get('subscriber').get('subscriberType')
        if subscriber_type == 'Internal' and not self.flags.get('ALLOW_INTERNAL', False):
            raise SubscriberTypeException("Internal subscribers are not allowed. Add the flag ALLOW_INTERNAL.")
        elif subscriber_type == 'External' and not self.flags.get('DISALLOW_EXTERNAL', False):
            raise SubscriberTypeException("External subscribers are not allowed. Remove the flag DISALLOW_EXTERNAL.")

    def _validate_contract_type(self, entitlements: dict) -> None:
        contract_type = entitlements.get('product').get('contractType')
        if contract_type.startswith('Trial') and not self.flags.get('ALLOW_TRIAL', False):
            raise TrialAccessException("Trial contracts are not allowed. Add the flag ALLOW_TRIAL.")

    def _validate_product_status(self, entitlements: dict) -> None:
        is_active = entitlements.get('product').get('status')
        if not is_active and not self.flags.get('ALLOW_INACTIVE', False):
            raise InactiveAccountException("Product must be active. Add the flag ALLOW_INACTIVE.")

    def _validate_key_type(self, entitlements: dict) -> None:
        key_type = entitlements.get('apiKey').get('keyType')
        if key_type != 'Production':
            raise DevelopmentKeyException("Key type must be 'Production'.")

    def _validate_session_type(self, entitlements: dict) -> None:
        if not isinstance(self.session, DirectPlusSession):
            raise TypeError(f"Session must be of type DirectPlusSession, not {type(self.session)}")

        if not self.flags.get('SKIP_ENTITLEMENT_CHECK', False):
            if not entitlements:
                raise NoEndpointException("Session is not entitled to any endpoints.")

            if entitlements.get('product', {}).get('status') != 'Active':
                raise ProductStatusException("Product status is not active.")

            key_type = entitlements.get('apiKey', {}).get('keyType')
            if not self.flags.get(key_type.upper(), False):
                raise KeyTypeException(f"Key type has to have a matching flag. Set the flag {key_type.upper()} to allow the key type '{key_type}'.")

    @property
    def entitlements(self) -> List[dict]:
        if self._entitlements is None:
            self._entitlements = [ent for ent in self.get_entitlements().get('entitlements') if len(ent.get('levels')) > 0]
            self.log.debug(f"Entitlements: {self._entitlements}")
        return self._entitlements

    def get_entitlements(self) -> dict:
        request = DirectPlusRequest(self.session, self.endpoints.get('GET entitlements'), self)
        try:
            response = request.send()
        except AuthorizationError as e:
            raise AuthorizationError(f"Session is not entitled to the entitlement endpoint. Use the flag SKIP_ENTITLEMENT_CHECK to bypass this check.")
        return response.json()

    def is_entitled(self, endpoint_name: str) -> bool:
        if endpoint_name not in [end.split(' ')[1] for end in self.endpoints.keys()]:
            raise NoEndpointException(f"Endpoint '{endpoint_name}' does not exist.")

        if not self.connection_is_valid:
            self._validate_connection()

        return any(endpoint_name == endpoint.get('entitlementID') for endpoint in self.entitlements)

