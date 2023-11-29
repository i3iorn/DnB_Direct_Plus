import logging

from v2.exceptions import (
    SubscriberTypeException,
    NoEndpointException,
    ContractTypeException,
    ProductStatusException,
    KeyTypeException,
    TrialAccessException,
    InactiveAccountException,
    DevelopmentKeyException
)
from v2.request import DirectPlusRequest
from v2.session import DirectPlusSession


class AccessManager:
    def __init__(self, session: DirectPlusSession, endpoints: dict, **flags):
        self.log = logging.getLogger(__name__)
        self.session = session
        self.flags = flags
        self.endpoints = endpoints
        self.connection_is_valid = False
        self._validate_connection()

    def _validate_connection(self):
        entitlements = self.get_entitlements()

        self._validate_subscriber_type(entitlements)
        self._validate_contract_type(entitlements)
        self._validate_product_status(entitlements)
        self._validate_key_type(entitlements)
        self._validate_session_type(entitlements)

        self.connection_is_valid = True

    def _validate_subscriber_type(self, entitlements):
        subscriber_type = entitlements.get('subscriber').get('subscriberType')
        if subscriber_type == 'Internal' and not self.flags.get('ALLOW_INTERNAL', False):
            raise SubscriberTypeException("Internal subscribers are not allowed. Add the flag ALLOW_INTERNAL.")
        elif subscriber_type == 'External' and not self.flags.get('DISALLOW_EXTERNAL', False):
            raise SubscriberTypeException("External subscribers are not allowed. Remove the flag DISALLOW_EXTERNAL.")

    def _validate_contract_type(self, entitlements):
        contract_type = entitlements.get('product').get('contractType')
        if contract_type.startswith('Trial') and not self.flags.get('ALLOW_TRIAL', False):
            raise TrialAccessException("Trial contracts are not allowed. Add the flag ALLOW_TRIAL.")

    def _validate_product_status(self, entitlements):
        is_active = entitlements.get('product').get('status')
        if not is_active and not self.flags.get('ALLOW_INACTIVE', False):
            raise InactiveAccountException("Product must be active. Add the flag ALLOW_INACTIVE.")

    def _validate_key_type(self, entitlements):
        key_type = entitlements.get('apiKey').get('keyType')
        if key_type != 'Production':
            raise DevelopmentKeyException("Key type must be 'Production'.")

    def _validate_session_type(self, entitlements):
        if not isinstance(self.session, DirectPlusSession):
            raise TypeError(f"Session must be of type DirectPlusSession, not {type(self.session)}")

        if not self.flags.get('SKIP_ENTITLEMENT_CHECK', False):
            if not entitlements:
                raise NoEndpointException("Session is not entitled to any endpoints.")

            if entitlements.get('product', {}).get('status') != 'Active':
                raise ProductStatusException("Product status is not active.")

            key_type = entitlements.get('apiKey', {}).get('keyType', False)
            if not self.flags.get(key_type.upper(), False):
                raise KeyTypeException(f"Key type has to have a matching flag. Set the flag {key_type.upper()} to allow the key type '{key_type}'.")

    def get_entitlements(self):
        self.log.debug(self.endpoints)
        request = DirectPlusRequest(self.session, self.endpoints.get('GET entitlements'), self)
        response = request.send()
        return response.json()
