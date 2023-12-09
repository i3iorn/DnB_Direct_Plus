import hashlib
import json
import logging
import math

from v2.request import EmptySearchException


class SearchException(Exception):
    pass


class SearchHash:
    def __init__(self, **kwargs):
        self.log = logging.getLogger(__name__)
        self.parameters = kwargs
        self.hash = self.get_hash()

    def get_hash(self):
        hash_function = hashlib.sha256()
        hash_function.update(json.dumps(self.parameters).encode('utf-8'))
        return hash_function.hexdigest()

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        return self.hash == other.hash

    def __repr__(self):
        return self.hash

    def __str__(self):
        return self.hash


class ParameterSet:
    def __init__(self, dp, **parameters):
        self._log = logging.getLogger(__name__)
        self._dp = dp
        self._log.debug(f"Created parameter set {self.hash}")

        for key, value in parameters.items():
            self._add_parameter(key, value)

    @property
    def hash(self):
        return SearchHash(**self.as_dict()).hash

    def _add_parameter(self, key, value):
        # TODO: Validate parameters
        self._log.debug(f"Adding parameter '{key}' with value '{str(value)[:50]}...'.")
        setattr(self, key, value)

    def as_dict(self):
        return {key: value for key, value in self.__dict__.items() if not key.startswith('_') and value is not None}

    def __eq__(self, other):
        return self.hash == other.hash

    def __repr__(self):
        return self.hash


class SearchCriteriaManager:
    def __init__(self, dp, **criteria):
        self.log = logging.getLogger(__name__)

        self.dp = dp
        self.start_criteria = ParameterSet(self.dp, **criteria)
        self.active_criteria = ParameterSet(self.dp, **criteria)
        self._searches = {}

        self._initial_search = self.search(self.start_criteria)


    @property
    def initial_search(self):
        return self._initial_search

    @property
    def active_search(self):
        return self.active_criteria

    @active_search.setter
    def active_search(self, value):
        self.active_criteria = value

    @property
    def searches(self):
        return self._searches

    def add_criteria(self, **criteria):
        """
        Adds criteria to the active criteria set.

        :param criteria:
        :return:
        """
        self.active_criteria = ParameterSet(self.dp, **criteria)

    def remove_criteria(self, *criteria):
        """
        Removes criteria from the active criteria set.

        :param criteria:
        :return:
        """
        for criterion in criteria:
            self.active_criteria.__delattr__(criterion)

    def get_criteria(self):
        """
        Returns the active criteria set.

        :return:
        """
        return self.active_criteria.as_dict()

    def get_count(self, parameters=None) -> int:
        """
        Returns the number of duns numbers matching the given criteria.

        :param parameters: If not provided, the active criteria will be used.
        :return:
        """
        if parameters is None:
            parameters = self.active_criteria.as_dict()
        criteria = ParameterSet(self.dp, **parameters)

        result = self.search(criteria)
        if result.get('error', False):
            if result.get('error').get('errorCode') == '21501':
                return 0
            raise SearchException(result)
        return result.get('candidatesMatchedQuantity')

    def get_hits(self, parameters=None) -> list:
        """
        Returns a list of duns numbers matching the given criteria.

        :param parameters: If not provided, the active criteria will be used.
        :return:
        """
        if parameters is None:
            parameters = self.active_criteria
        result = self.search(parameters)
        if result.get('error', False):
            if result.get('error').get('errorCode') == '21501':
                raise EmptySearchException(result)
            raise SearchException(result)

        count = result.get('candidatesMatchedQuantity')
        if count <= 50:
            return [self.get_hits_simple(result)]
        elif 50 < count <= 1000:
            return self.get_hits_paged(result)
        else:
            if self.dp.access_manager.is_entitled('multiProcessJobSubmissionv2'):
                return self.get_hits_multiprocess(result)
            else:
                return self.get_hits_complex_paged(result)

    def get_hits_complex_paged(self, response) -> list:
        sort_items = [
            'numberOfEmployees'
            'countryISOAlpha2Code',
            'primaryName',
            'isOutOfBusiness',
            'isBranch',
            'yearlyRevenue',
        ]
        sort_directions = [
            'ascending',
            'descending'
        ]
        if response.get('candidatesMatchedQuantity') < 5000:
            for item in sort_items:
                for direction in sort_directions:
                    self.active_criteria.sort = [{'item': item, 'order': direction}]
                    try:
                        yield self.get_hits_paged(response)
                    except EmptySearchException:
                        break

    def get_hits_multiprocess(self, result):
        return []

    def get_hits_paged(self, response) -> list:
        for i in range(math.ceil(response.get('candidatesMatchedQuantity') / 50)):
            self.active_criteria.pageNumber = i + 1
            if i > 0:
                response = self.search(**self.active_criteria.as_dict())
            yield self.get_hits_simple(response)

    def get_hits_simple(self, response) -> list:
        """
        Returns a list of duns numbers matching the given criteria.
        
        :param response: 
        :return: 
        """
        for hit in response.get('searchCandidates'):
            yield hit.get('organization').get('duns')

    def search(self, criteria: ParameterSet) -> dict:
        """
        Returns a list of duns numbers matching the given criteria.

        :param duns:
        :return:
        """
        self.log.debug(f"Searching for {criteria}")
        self._searches[criteria.hash] = self.dp.call('searchCriteria', **criteria.as_dict()).json()

        return self.searches[criteria.hash]
