import hashlib
import json
import logging
import math
from typing import TYPE_CHECKING, Any

from src.exceptions import SearchParameterException, SearchException, RequestPayloadException, EmptySearchException

if TYPE_CHECKING:
    from src.direct_plus import DirectPlus
    from requests import Response


class SearchHash:
    def __init__(self, **kwargs) -> None:
        self.log = logging.getLogger(__name__)
        self.parameters = kwargs
        self.hash = self.get_hash()

    def get_hash(self) -> str:
        hash_function = hashlib.sha256()
        hash_function.update(json.dumps(self.parameters).encode('utf-8'))
        return hash_function.hexdigest()

    def __eq__(self, other: 'SearchHash') -> bool:
        return self.hash == other.hash

    def __repr__(self) -> str:
        return self.hash

    def __str__(self) -> str:
        return self.hash


class ParameterSet:
    def __init__(self, dp: 'DirectPlus', **parameters) -> None:
        self._log = logging.getLogger(__name__)
        self._dp = dp
        self._log.debug(f"Created parameter set {self.hash}")
        self.sort = [{'item': 'primaryName', 'direction': 'ascending'}]

        for key, value in parameters.items():
            self._add_parameter(key, value)

    @property
    def hash(self) -> str:
        return SearchHash(**self.as_dict()).hash

    def _add_parameter(self, key: str, value: Any) -> None:
        # TODO: Validate parameters
        self._log.debug(f"Adding parameter '{key}' with value '{value if len(str(value)) < 50 else str(value)[:50] + '...'}'.")
        setattr(self, key, value)

    def as_dict(self) -> dict:
        return {key: value for key, value in self.__dict__.items() if not key.startswith('_') and value is not None}

    def __eq__(self, other) -> bool:
        return self.hash == other.hash

    def __repr__(self) -> str:
        return self.hash


class SearchCriteriaManager:
    def __init__(self, dp: 'DirectPlus', **criteria) -> None:
        self.log = logging.getLogger(__name__)

        self.dp = dp
        self.start_criteria = ParameterSet(self.dp, **criteria)
        self.active_criteria = ParameterSet(self.dp, **criteria)
        self._searches = {}

        self._initial_search = self.search(self.start_criteria)


    @property
    def initial_search(self) -> 'Response':
        return self._initial_search

    @property
    def active_search(self) -> ParameterSet:
        return self.active_criteria

    @active_search.setter
    def active_search(self, value) -> None:
        self.active_criteria = value

    @property
    def searches(self) -> dict:
        return self._searches

    def add_criteria(self, **criteria) -> None:
        """
        Adds criteria to the active criteria set.

        :param criteria:
        :return:
        """
        self.active_criteria = ParameterSet(self.dp, **criteria)

    def remove_criteria(self, *criteria) -> None:
        """
        Removes criteria from the active criteria set.

        :param criteria:
        :return:
        """
        for criterion in criteria:
            self.active_criteria.__delattr__(criterion)

    def get_criteria(self) -> dict:
        """
        Returns the active criteria set.

        :return:
        """
        return self.active_criteria.as_dict()

    def get_duns_from_search(self, response: 'Response') -> set:
        """
        Returns a list of duns numbers from a search hash.

        :param search_hash:
        :return:
        """
        return set([hit.get('organization').get('duns') for hit in response.json().get('searchCandidates')])

    def get_count(self, parameters: dict) -> int:
        """
        Returns the number of duns numbers matching the given criteria.

        :param parameters: If not provided, the active criteria will be used.
        :return:
        """
        criteria = ParameterSet(self.dp, **parameters)

        result = self.search(criteria).json()
        if result.get('error', False):
            if result.get('error').get('errorCode') == '21501':
                return 0
            raise SearchException(result)
        return result.get('candidatesMatchedQuantity')

    def get_hits(self, parameters=None) -> set:
        """
        Returns a list of duns numbers matching the given criteria.

        :param parameters: If not provided, the active criteria will be used.
        :return:
        """
        parameters = self._get_hit_parameter_validation(parameters)
        self.log.debug(f"Getting hits for {str(parameters.as_dict())[:100]}")

        response = self.search(parameters).json()
        return self._handle_search_result(response, parameters)

    def _handle_search_result(self, response, parameters):
        """
        Handles the search result and returns a set of duns numbers.

        :param response:
        :param parameters:
        :return:
        """
        result_duns = set()

        if response.get('candidatesMatchedQuantity') > 3000:
            self.log.warning("More than 3000 hits for search. Trying to split up search.")
            parameters_sets = self._split_search(parameters)

            for i, param_set in enumerate(parameters_sets):

                for key, value in param_set.as_dict().items():
                    if key == 'industryCodes':
                        self.log.debug(f"{key}: {len(value[0].get('code'))}")
                    else:
                        self.log.debug(f"{key}: {value}")

                ds = self.get_hits(param_set)
                self.log.debug(f"Got {len(ds)} hits for set nr:{i} with: {str(param_set.as_dict())[:100]}")
                result_duns.update(ds)
        else:
            result_duns.update(self._get_hit_by_search_count(response, parameters))

        return result_duns
            
    def _get_hit_by_search_count(self, response, parameters) -> set:
        """
        Returns a list of duns numbers matching the given criteria. This method is used to determine which method to use
        to get the hits.

        :param response:
        :param parameters:
        :return:
        """
        count = response.get('candidatesMatchedQuantity')
        if count <= 50:
            self.log.debug(f"Returning simple hits for {parameters}")
            return self._get_hits_simple(response)
        elif 50 < count <= 1000:
            self.log.debug(f"Returning paged hits for {parameters}")
            return self._get_hits_paged(response)
        else:
            if self.dp.access_manager.is_entitled('multiProcessJobSubmissionv2'):
                self.log.debug(f"Returning multiprocess hits for {parameters}")
                return self._get_hits_multiprocess(response)
            else:
                self.log.debug(f"Returning complex hits for {parameters}")
                return self._get_hits_complex_paged(response)

    def _get_hit_parameter_validation(self, parameters) -> ParameterSet:
        """
        Validates the parameters passed to get_hits. Raises a ValueError if the parameters are invalid.
        
        :param parameters: 
        :return: 
        """
        if parameters is None:
            parameters = self.active_criteria
        else:
            if isinstance(parameters, dict):
                parameters = ParameterSet(self.dp, **parameters)
            elif not isinstance(parameters, ParameterSet):
                raise SearchParameterException(f"Parameters must be a dict or ParameterSet, not {type(parameters)}.")
        return parameters

    def _get_hits_complex_paged(self, response) -> set:
        """
        Returns a list of duns numbers matching the given criteria. This method is used for searches with more than 1000 hits.

        :param response:
        :return:
        """
        sort_items = [
            'numberOfEmployees',
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
        self.log.debug(f"Getting hits complex paged for {response.get('candidatesMatchedQuantity')} hits.")
        hits = set()
        for item in sort_items:
            self.log.debug(f"Sorting by {item}")
            for direction in sort_directions:
                self.active_criteria.sort = [{'item': item, 'direction': direction}]
                try:
                    hits.update(self._get_hits_paged(response))
                except EmptySearchException:
                    break
                if len(hits) >= response.get('candidatesMatchedQuantity'):
                    break
                self.log.info(f"Found {len(hits)} hits so far.")
        return hits

    def _get_hits_multiprocess(self, result) -> set:
        """
        Returns a list of duns numbers matching the given criteria. This method is used for searches with more than 1000 hits.

        :param result:
        :return:
        """
        return set()

    def _get_hits_paged(self, response) -> set:
        """
        Returns a list of duns numbers matching the given criteria. This method is used for searches with less than 1000 hits.

        :param response:
        :return:
        """
        result = set()
        criteria = response.get('inquiryDetail')
        active_criteria = ParameterSet(self.dp, **criteria)
        for i in range(1, min(20, math.ceil(response.get('candidatesMatchedQuantity') / 50))):
            active_criteria.pageNumber = i
            self.log.info(f"Getting page {i + 1} of {math.ceil(response.get('candidatesMatchedQuantity') / 50)} from {active_criteria.hash}")

            if i >= 20:
                self.log.warning(f"More than 20 pages of results for {active_criteria}")
                break

            if i > 0:
                response = self.search(active_criteria).json()

            found = response.get('candidatesReturnedQuantity')
            self.log.info(f"Found {found} candidates.")
            result.update(self._get_hits_simple(response))
        return result

    def _get_hits_simple(self, response) -> set:
        """
        Returns a list of duns numbers matching the given criteria. This method is used for searches with less than 50 hits.
        
        :param response: 
        :return: 
        """
        return set([hit.get('organization').get('duns') for hit in response.get('searchCandidates')])

    def search(self, criteria: ParameterSet) -> 'Response':
        """
        Returns a list of duns numbers matching the given criteria.

        :param criteria: A ParameterSet object containing the search criteria.
        :return:
        """
        if not isinstance(criteria, ParameterSet):
            raise SearchParameterException(f"Criteria must be a ParameterSet, not {type(criteria)}")

        if not hasattr(criteria, 'pageSize'):
            criteria.pageSize = 50
        self.log.debug(f"Searching for {criteria}")
        try:
            self._searches[criteria.hash] = self.dp.call('searchCriteria', **criteria.as_dict())
        except RequestPayloadException as e:
            if len(criteria.as_dict()) == 0:
                raise SearchException(f"There are no criteria to search with.") from e
            for key, value in criteria.as_dict().items():
                self.log.error(f"{key}: {value}")
            raise SearchException(f"Search failed with criteria above criteria") from e

        return self.searches[criteria.hash]

    def _search_response_validation(self, response: dict) -> None:
        """
        Validates a search response. Raises a SearchException if the search returns errors.

        :param response:
        :return:
        """
        if response.get('error', False):
            if response.get('error').get('errorCode') == '21501':
                raise EmptySearchException(response)
            raise SearchException(response)

        if response.get('candidatesMatchedQuantity') == 0:
            raise EmptySearchException(response)

    def _split_search(self, parameters):
        sets = []
        if hasattr(parameters, 'industryCodes'):
            code_count = len(parameters.industryCodes[0].get('code'))
            batch_size = max(code_count // 10, 1)
            codes = parameters.industryCodes[0].get('code')
            for i in range(0, code_count, batch_size):
                new_parameters = {
                    'industryCodes': [
                        {
                            'code': codes[i:i + batch_size],
                            'typeDnbCode': 3599
                        }
                    ],
                    **{key: value for key, value in parameters.as_dict().items() if key != 'industryCodes'}
                }
                new_set = ParameterSet(self.dp, **new_parameters)
                sets.append(new_set)
                del new_parameters

        return sets
