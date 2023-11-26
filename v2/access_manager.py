from v2.exceptions import SubscriberTypeException, TrialAccessException, InactiveAccountException, \
    DevelopmentKeyException
from v2.request import DirectPlusRequest
from v2.session import DirectPlusSession


class AccessManager:
    def __init__(self, session: DirectPlusSession, **flags):
        self.session = session
        self.flags = flags
        self._validate_connection()

    def _validate_connection(self):
        """
        Validates the connection to the Direct+ API.

        :return:
        """
        request = DirectPlusRequest(self.session, ENDPOINTS.get('entitlements'))
        response = request.send()

        res_obj = response.json()

        subscriber_type = res_obj.get('subscriber').get('subscriberType')
        if subscriber_type != 'External' and not self.flags.get('ALLOW_INTERNAL'):
            raise SubscriberTypeException(f"Subscriber type must be 'External', not {subscriber_type}")

        contract_type = res_obj.get('product').get('contractType')
        if contract_type.startswith('Trial') and not self.flags.get('ALLOW_TRIAL'):
            raise TrialAccessException(f"Contract type must not be 'Trial', is {contract_type}.")

        is_active = res_obj.get('product').get('status')
        if not is_active and not self.flags.get('ALLOW_INACTIVE'):
            raise InactiveAccountException(f"Product must be active, not {is_active}")

        key_type = res_obj.get('apiKey').get('keyType')
        if key_type != 'Production':
            raise DevelopmentKeyException(f"Key type must be 'Production', not {key_type}")

        self.connection_is_valid = True

    def get_entitlements(self):
        """
        Returns the entitlements of the current user.

        :return:
        """
        request = DirectPlusRequest(self.session, ENDPOINTS.get('entitlements'))
        response = request.send()

        return response.json()
