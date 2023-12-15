import json
import logging
from dataclasses import dataclass
from typing import List, Any


class ParameterValidator:
    """
    Validates parameters against a specification.
    """
    log = logging.getLogger(__name__)

    @classmethod
    def _validate_parameter(cls, name: str, value: Any, spec: dict):
        """
        Validates a single parameter against a specification. Raises a ValueError if the parameter is invalid.

        :param name:
        :param value:
        :param spec:
        :return:
        """
        if spec is None:
            raise ValueError(f"Specification for parameter '{name}' is None.")
        if name is None:
            raise ValueError(f"Name for parameter is None.")
        if not spec.get('nullable', True) and value is None:
            raise ValueError(f"{name} must not be null.")

        if spec.get('enum') is not None and value not in spec.get('enum'):
            raise ValueError(f"Parameter '{name}' must be one of {spec.get('enum')}, not {value}.")

        if not spec.get('nullable', True) and value is None:
            raise ValueError(f"Parameter '{name}' must not be null.")

        spec_types = {
            'integer': int,
            'string': str,
            'array': list,
            'boolean': bool,
            'object': dict,
            'number': float
        }

        if not isinstance(value, spec_types.get(spec.get('type', 'string'), str)):
            raise ValueError(f"Parameter '{name}' must be of type '{spec.get('type', 'string')}', not {type(value)}.")

        spec_type = spec.get('type') or spec.get('schema', {}).get('type')
        if spec_type in ('integer', 'number'):
            if spec.get('minimum') is not None and value < spec.get('minimum'):
                raise ValueError(f"Parameter '{name}' must be greater than or equal to {spec.get('minimum')}.")
            if spec.get('maximum') is not None and value > spec.get('maximum'):
                raise ValueError(f"Parameter '{name}' must be less than or equal to {spec.get('maximum')}.")
        elif spec_type == 'string':
            if spec.get('minLength') is not None and len(value) < spec.get('minLength'):
                raise ValueError(f"Parameter '{name}' must be at least {spec.get('minLength')} characters long. Was {value}.")
            if spec.get('maxLength') is not None and len(value) > spec.get('maxLength'):
                raise ValueError(f"Parameter '{name}' must be at most {spec.get('maxLength')} characters long. Was {value}.")
        elif spec_type == 'array':
            if spec.get('minItems') is not None and len(value) < spec.get('minItems'):
                raise ValueError(f"Parameter '{name}' must have at least {spec.get('minItems')} items. Was {value}.")
            for item in value:
                cls._validate_parameter(name, item, spec.get('items', {}))
        elif spec_type == 'object':
            for k, v in value.items():
                if k not in spec.get('properties', {}):
                    raise ValueError(f"Parameter '{name}' has an invalid property: {k}.")
                cls._validate_parameter(k, v, spec.get('properties', {}).get(k, {}))
        elif spec_type == 'boolean':
            pass
        else:
            cls.log.error(f"Parameter '{name}' has an invalid type: {spec_type}.")
            cls.log.error(f"Specification: {json.dumps(spec)}")
            raise ValueError(f"Parameter '{name}' has an invalid type: {spec_type}.")

        cls.log.log(1, f"Validated parameter '{name}' with value of type '{type(value)}' against spec {json.dumps(spec)}.")


@dataclass
class Endpoint(ParameterValidator):
    """
    Represents an endpoint. Can be used to create a request.
    """

    base = ''
    path = ''
    method = ''
    parameters = {}
    expected_parameters = {}

    @classmethod
    def path_params(cls) -> dict:
        """
        Returns a dictionary of path parameters.

        :return:
        """
        return {k: v['value'] for k, v in cls.parameters.items() if v['in'] == 'path'}

    @classmethod
    def query_params(cls) -> dict:
        """
        Returns a dictionary of query parameters.

        :return:
        """
        return {k: v['value'] for k, v in cls.parameters.items() if v['in'] == 'query'}

    @classmethod
    def header_params(cls) -> dict:
        """
        Returns a dictionary of header parameters.

        :return:
        """
        return {k: v['value'] for k, v in cls.parameters.items() if v['in'] == 'header'}

    @classmethod
    def url(cls) -> str:
        """
        Returns the full url of the endpoint.

        :return:
        """
        if '{' in cls.path:
            url = f'{cls.base}{cls.path}'.format(**cls.path_params())
        else:
            url = f'{cls.base}{cls.path}'
        return url

    @classmethod
    def _validate_get_parameters(cls, name: str, value: Any, spec: dict) -> dict:
        """
        Validates a single GET parameter against a specification. Raises a ValueError if the parameter is invalid.

        :param name:
        :param value:
        :param spec:
        :return:
        """
        for param in spec:
            if param.get('name') == name:
                cls._validate_parameter(name, value, param)
                return {
                    'name': name,
                    'in': param.get('in', 'query'),
                    'value': value,
                    'required': param.get('required', False),
                }
        raise ValueError(f"Parameter '{name}' not found in specification.")

    @classmethod
    def _validate_post_parameters(cls, name: str, value: Any, spec: dict) -> dict:
        """
        Validates a single POST parameter against a specification. Raises a ValueError if the parameter is invalid.

        :param name:
        :param value:
        :param spec:
        :return:
        """
        for param_name, param_spec in spec.items():
            if param_name == name:
                cls._validate_parameter(name, value, param_spec)
                return {
                    'name': name,
                    'in': param_spec.get('in', 'query'),
                    'value': value,
                    'required': param_spec.get('required', False),
                }
        raise ValueError(f"Parameter '{name}' not found in specification.")

    @classmethod
    def add_parameter(cls, name: str, value: Any) -> None:
        """
        Adds a parameter to the endpoint. Raises a ValueError if the parameter is invalid.

        :param name:
        :param value:
        :return:
        """
        spec = cls.expected_parameters
        if cls.method == 'GET':
            cls.parameters[name] = cls._validate_get_parameters(name, value, spec)
        elif cls.method == 'POST':
            cls.parameters[name] = cls._validate_post_parameters(name, value, spec)


class SpecificationHostError(Exception):
    """
    Raised when the host could not be determined from the specification.
    """
    pass


class SpecificationError(Exception):
    """
    Raised when the specification is invalid.
    """
    pass


def EndpointFactory(spec: dict):
    """
    Creates an Endpoint object from a specification dictionary.

    :param spec: The specification dictionary.
    :return:
    """
    if spec.get('swagger', '') != '':
        return SwaggerFactory.create_endpoint(spec, spec.get('swagger', ''))
    elif spec.get('openapi', '') != '':
        return OpenApiFactory.create_endpoint(spec, spec.get('openapi', ''))
    else:
        raise SpecificationError(f"Could not determine specification type from specification: {spec}")


class BaseEndpointFactory(ParameterValidator):
    """
    Base class for EndpointFactory classes.
    """
    @classmethod
    def create_endpoint(cls, spec: dict, version: str) -> List:
        """
        Creates an Endpoint object from a specification dictionary.

        :param spec:
        :param version:
        :return:
        """
        try:
            method = getattr(cls, f"version{version[0]}")
        except AttributeError:
            raise SpecificationError(f"{cls} version {version} is not supported.")
        if method:
            return method(spec)

    @classmethod
    def make_custom_endpoint(cls, **data):
        return type(
                    data.get('id'),
                    (Endpoint,),
                    {
                        'name': data.get('id'),
                        'path': data.get('path'),
                        'method': data.get('method').upper(),
                        'base': data.get('base'),
                        'expected_parameters': data.get('expected_parameters'),
                    }
                )

    def __repr__(self):
        return f"{self.__class__.__name__.replace('Factory', '')}"


class OpenApiFactory(BaseEndpointFactory):
    @classmethod
    def version3(cls, spec: dict) -> List:
        """
        Creates a list of Endpoint objects from a specification dictionary.
        :param spec:
        :return:
        """
        endpoints = []

        base = spec.get('servers', [{'url': ''}])[0].get('url', '')
        if base == '':
            raise SpecificationHostError(f"Could not set host for endpoint from specification: {spec}")

        for path, properties in spec.get('paths', {}).items():
            id = properties.get('x-DNB-ID')
            for method, method_values in {method: props for method, props in properties.items() if method in ['post', 'get']}.items():
                expected_parameters = {}
                if method == 'post':
                    expected_parameters = method_values.get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema', {}).get('properties', {})
                elif method == 'get':
                    expected_parameters = method_values.get('parameters', [])

                endpoints.append(cls.make_custom_endpoint(
                    id=id,
                    path=path,
                    method=method,
                    base=base,
                    expected_parameters=expected_parameters,
                ))
        return endpoints


class SwaggerFactory(BaseEndpointFactory):
    @classmethod
    def version2(cls, spec: dict) -> List:
        """
        Creates a list of Endpoint objects from a specification dictionary.

        :param spec:
        :return:
        """
        endpoints = []

        host = spec.get('host', '')
        scheme = spec.get('schemes', [''])[0]
        if scheme != '' and host != '':
            base = f"{scheme}://{host}"
        else:
            raise SpecificationHostError(f"Could not set host for endpoint from specification: {spec}")
        for path, properties in spec.get('paths', {}).items():
            id = properties.get('x-DNB-ID')
            for method, method_values in {method: props for method, props in properties.items() if method in ['post', 'get']}.items():
                endpoints.append(cls.make_custom_endpoint(
                    id=id,
                    path=path,
                    method=method,
                    base=base,
                    expected_parameters=method_values.get('parameters', []),
                ))
        return endpoints
