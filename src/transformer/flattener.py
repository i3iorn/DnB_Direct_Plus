import logging
import re
from typing import List

from src.decorators import log_args
from src.exceptions import FlattenerError


class Flattener:
    """
    Flattens a JSON object. If the object is a dictionary, the parent key will be prepended to the key of each item
    in the dictionary. If the object is a list, the parent key will be prepended to the key of each item in the
    list. If include_list_index is True, the key will be the index of the item in the list. Otherwise, the key will
    be the parent key.

    :param delimiter: delimiter to use between keys. Defaults to '.'.
    :param include_list_index: If True, the key will be the index of the item in the list. Otherwise, the key will
    be the parent key.
    :param max_array_length: Maximum length of arrays. If the length of an array exceeds this value, the array will
    be truncated. Defaults to None.
    :param max_depth: Maximum depth of flattening. Defaults to None.
    :param stop_keys: List of keys, wildcard patterns, or regex patterns to stop flattening and disregard child values.
    Defaults to an empty list.
    :param callback: Callback function to apply to the value of a key. Defaults to None.
    :param callback_keys: List of keys, wildcard patterns, or regex patterns to apply the callback function to.
    Defaults to an empty list.
    """
    def __init__(self,
                 delimiter: str = '.',
                 include_list_index: bool = False,
                 max_array_length: int = None,
                 max_depth: int = None,
                 stop_keys: List[str] = None,
                 callback: callable = None,
                 callback_keys: List[str] = None,
                 ):
        self.log = logging.getLogger(__name__)

        try:
            self._validate_parameters(delimiter=delimiter, include_list_index=include_list_index,
                                      max_array_length=max_array_length, max_depth=max_depth, stop_keys=stop_keys)
        except (ValueError, TypeError) as e:
            self._exception_handling(FlattenerError, f"Error while flattening", error=e)

        self.delimiter = delimiter
        self.include_list_index = include_list_index
        self.max_array_length = max_array_length
        self.max_depth = max_depth
        self.stop_keys = stop_keys or []

        # Allowing a callback function to be passed to the flattener is a security risk. This is disabled by default.
        # If you want to enable this, set callback_is_allowed to True. This is a workaround to avoid having to
        # implement a whitelist of allowed functions. MAKE SURE YOU KNOW WHAT YOU ARE DOING.
        callback_is_allowed: bool = False
        if callback_is_allowed:
            self.callback = callback
            self.callback_keys = callback_keys or []
        else:
            self.callback = None

    @log_args
    def flatten(self, json_data: dict) -> dict:
        """
        Flattens a JSON object.

        :param json_data: JSON object to flatten.
        :return: Flattened JSON object.
        """
        flattened_data = {}
        self._flatten(json_data, '', flattened_data, depth=0)
        return flattened_data

    @log_args
    def _validate_parameters(self, **parameters):
        """
        Validates the parameters passed to the different functions. Raises a ValueError if the parameters are invalid.

        :param parameters:
        :return:
        """
        for key, value in parameters.items():
            if key == 'include_list_index':
                if not isinstance(value, bool):
                    raise TypeError(f"{key} must be a boolean")
            elif key in ('parent_key', 'current_key', 'key', 'pattern', 'delimiter'):
                if not isinstance(value, str):
                    raise TypeError(f"{key} must be a string")
            elif key in ('max_array_length', 'max_depth', 'index', 'depth'):
                if not isinstance(value, int) and value is not None:
                    raise TypeError(f"{key} must be an integer")
                if value is not None and value < 0:
                    raise ValueError(f"{key} must be greater than or equal to 0")
            elif key in ('stop_keys', 'json_list'):
                if not isinstance(value, list) and value is not None:
                    raise TypeError(f"{key} must be a list")
                if key in ('stop_keys'):
                    if value is not None and not all(isinstance(k, str) for k in value):
                        raise TypeError(f"{key} must be a list of strings")
            elif key in ('flattened_data', 'json_dict'):
                if not isinstance(value, dict):
                    raise TypeError(f"{key} must be a dictionary")
            else:
                raise ValueError(f"Invalid parameter {key}")

    @log_args
    def _flatten(self, json_data: dict, parent_key: str, flattened_data: dict, depth: int) -> None:
        """
        Flattens a JSON object. If the object is a dictionary, the parent key will be prepended to the key of each item
        in the dictionary. If the object is a list, the parent key will be prepended to the key of each item in the
        list. If include_list_index is True, the key will be the index of the item in the list. Otherwise, the key will
        be the parent key.

        :param json_data: JSON object to flatten.
        :param parent_key: Name of the parent key.
        :param flattened_data: the flattened data
        :param depth: Current depth of flattening.
        :return: None
        """
        if not json_data:
            return

        try:
            # json_data is not validated as it can be anything
            self._validate_parameters(parent_key=parent_key, flattened_data=flattened_data,
                                      depth=depth)
        except (ValueError, TypeError) as e:
            self._exception_handling(FlattenerError, f"Error while flattening", error=e)

        if self.max_depth is not None and depth >= self.max_depth:
            flattened_data[parent_key] = json_data
            return

        if self._should_stop_flattening(parent_key):
            flattened_data[parent_key] = json_data
            return

        if self.callback is not None and parent_key in self.callback_keys:
            json_data = self.callback(json_data)

        if isinstance(json_data, dict):
            self._flatten_dict(json_data, parent_key, flattened_data, depth)
        elif isinstance(json_data, list):
            self._flatten_list(json_data, parent_key, flattened_data, depth)
        else:
            flattened_data[parent_key] = json_data

    @log_args
    def _should_stop_flattening(self, current_key: str) -> bool:
        """
        Checks if the flattening process should stop for the current key based on the stop_keys option.

        :param current_key: Current key being processed.
        :return: True if flattening should stop, False otherwise.
        """
        try:
            self._validate_parameters(current_key=current_key)
        except (ValueError, TypeError) as e:
            self._exception_handling(FlattenerError, f"Error while flattening", error=e)

        for stop_key in self.stop_keys:
            if self._matches_pattern(current_key, stop_key):
                return True

        return False

    @log_args
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """
        Checks if the key matches the specified pattern. The pattern can be an exact match, a wildcard pattern using
        asterisks, or a regex pattern.

        :param key: Key to check.
        :param pattern: Pattern to match.
        :return: True if the key matches the pattern, False otherwise.
        """
        try:
            self._validate_parameters(key=key, pattern=pattern)
        except (ValueError, TypeError) as e:
            self._exception_handling(FlattenerError, f"Error while flattening", error=e)

        if key == pattern or pattern == '*':
            return True

        # Wildcard pattern using asterisks
        wildcard_pattern = pattern.replace('*', '.*')
        if re.fullmatch(wildcard_pattern, key):
            return True

        # Regex pattern
        if re.fullmatch(pattern, key):
            return True

        return False

    @log_args
    def _flatten_dict(self, json_dict: dict, parent_key: str, flattened_data: dict, depth: int) -> None:
        """
        Flattens a dictionary. If the dictionary is nested, the parent key will be prepended to the key of each item in
        the dictionary.

        :param json_dict: Dictionary to flatten.
        :param parent_key: Name of the parent key.
        :param flattened_data: the flattened data
        :param depth: Current depth of flattening.
        :return: None
        """
        if json_dict is None:
            json_dict = ""
            return

        try:
            self._validate_parameters(json_dict=json_dict, parent_key=parent_key, flattened_data=flattened_data,
                                      depth=depth)
        except (ValueError, TypeError) as e:
            self._exception_handling(FlattenerError, f"Error while flattening", error=e)

        for key, value in json_dict.items():
            new_key = f"{parent_key}{self.delimiter}{key}" if parent_key else key
            self._flatten(value, new_key, flattened_data, depth + 1)

    @log_args
    def _flatten_list(self, json_list: list, parent_key: str, flattened_data: dict, depth: int) -> None:
        """
        Flattens a list of dictionaries. If the list is nested, the parent key will be prepended to the key of each
        item in the list. If include_list_index is True, the key will be the index of the item in the list. Otherwise,
        the key will be the parent key.

        :param json_list: list of dictionaries
        :param parent_key: Name of the parent key.
        :param flattened_data: the flattened data
        :param depth: Current depth of flattening.
        :return: None
        """
        if not json_list:
            return

        try:
            self._validate_parameters(json_list=json_list, parent_key=parent_key, flattened_data=flattened_data,
                                      depth=depth)
        except (ValueError, TypeError) as e:
            self._exception_handling(FlattenerError, f"Error while flattening", error=e)

        array_length = len(json_list)
        if self.max_array_length is not None:
            array_length = min(array_length, self.max_array_length)

        for i in range(array_length):
            key = self._get_list_key(parent_key, i)
            self._flatten(json_list[i], key, flattened_data, depth + 1)

    @log_args
    def _get_list_key(self, parent_key: str, index: int) -> str:
        """
        Returns the key for a list item. If include_list_index is True, the key will be the index of the item in the
        list. Otherwise, the key will be the parent key.

        :param parent_key: Name of the parent key.
        :param index: Index of the item in the list.
        :return:
        """
        try:
            self._validate_parameters(parent_key=parent_key, index=index)
        except (ValueError, TypeError) as e:
            self._exception_handling(FlattenerError, f"Error while flattening", error=e)

        if parent_key:
            return f"{parent_key}{self.delimiter}{index}" if self.include_list_index else f"{parent_key}{self.delimiter}{index}"
        else:
            return str(index) if self.include_list_index else str(index)

    @log_args
    def _exception_handling(self, exception_class, message, error=None):
        """
        Handles exceptions raised by the Flattener for uniformity.

        :param exception_class: Exception class to raise.
        :param message: Error message.
        :return: None
        """
        self.log.exception(message)
        if error:
            raise exception_class(message) from error
        else:
            raise exception_class(message)
