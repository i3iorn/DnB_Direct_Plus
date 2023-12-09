import json
import logging
from dataclasses import dataclass
from typing import List


@dataclass
class Endpoint:
    base = ''
    path = ''
    method = ''
    parameters = {}
    expected_parameters = {}

    @classmethod
    def path_params(cls):
        return {k: v['value'] for k, v in cls.parameters.items() if v['in'] == 'path'}

    @classmethod
    def query_params(cls):
        return {k: v['value'] for k, v in cls.parameters.items() if v['in'] == 'query'}

    @classmethod
    def header_params(cls):
        return {k: v['value'] for k, v in cls.parameters.items() if v['in'] == 'header'}

    @classmethod
    def url(cls):
        if '{' in cls.path:
            url = f'{cls.base}{cls.path}'.format(**cls.path_params())
        else:
            url = f'{cls.base}{cls.path}'
        return url
    
    @classmethod
    def _validate_parameter(cls, name, value, spec):
        if spec.get('type') == 'integer':
            try:
                int(value)
            except ValueError:
                raise ValueError(f"speceter '{name}' must be an integer.")
        if spec.get('type') == 'string':
            if not isinstance(value, str):
                raise ValueError(f"speceter '{name}' must be a string.")
        if spec.get('type') == 'array':
            if not isinstance(value, object):
                raise ValueError(f"speceter '{name}' must be a list.")
        if spec.get('type') == 'boolean':
            if not isinstance(value, bool):
                raise ValueError(f"speceter '{name}' must be a boolean.")
        if spec.get('type') == 'object':
            if not isinstance(value, dict):
                raise ValueError(f"speceter '{name}' must be a dictionary.")
        if spec.get('type') == 'number':
            try:
                float(value)
            except ValueError:
                raise ValueError(f"speceter '{name}' must be a number.")
        if isinstance(value, list):
            if spec.get('minItems', 0) > len(value):
                raise ValueError(f"speceter '{name}' must have at least {spec['minItems']} items.")
        if isinstance(value, str):
            if spec.get('minLength', 0) > len(value):
                raise ValueError(f"speceter '{name}' must be at least {spec['minLength']} characters long.")
            if spec.get('maxLength', 4092) < len(value):
                raise ValueError(f"speceter '{name}' must be at most {spec['maxLength']} characters long.")
        if not spec.get('nullable', True) and value is None:
            raise ValueError(f"speceter '{name}' must not be null.")

    @classmethod
    def _validate_get_parameters(cls, name, value, spec):
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
    def add_parameter(cls, name, value):
        spec = cls.expected_parameters
        if cls.method == 'GET':
            cls.parameters[name] = cls._validate_get_parameters(name, value, spec)
        elif cls.method == 'POST':
            cls.parameters[name] = cls._validate_post_parameters(name, value, spec)

    @classmethod
    def _validate_post_parameters(cls, name, value, spec):
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


class SpecificationHostError(Exception):
    pass


class SpecificationError(Exception):
    pass


def EndpointFactory(spec: dict):
    """
    Creates an Endpoint object from a specification dictionary.

    :param spec: The specification dictionary.
    :return:
    """
    if spec.get('swagger', '') != '':
        return SwaggerFactory(spec)
    elif spec.get('openapi', '') != '':
        return OpenApiFactory(spec)
    else:
        raise SpecificationError(f"Could not determine specification type from specification: {spec}")


def OpenApiFactory(spec):
    def version3(spec) -> List:
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

                endpoints.append(type(
                    id,
                    (Endpoint,),
                    {
                        'name': id,
                        'path': path,
                        'method': method.upper(),
                        'base': base,
                        'expected_parameters': expected_parameters,
                    }
                ))
        return endpoints
    version = spec.get('openapi', '')
    if version == '':
        raise ValueError(f"Could not determine OpenAPI version from specification: {spec}")

    if int(version[0]) < 3:
        raise ValueError(f"OpenAPI version {version} not supported.")
    elif int(version[0]) == 3:
        return version3(spec)
    else:
        raise SpecificationError(f"OpenAPI version {version} not supported.")

def SwaggerFactory(spec):
    def version2(spec) -> List:
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
                endpoints.append(type(
                    id,
                    (Endpoint,),
                    {
                        'name': id,
                        'path': path,
                        'method': method.upper(),
                        'base': base,
                        'expected_parameters': method_values.get('parameters', []),
                    }
                ))
        return endpoints

    version = spec.get('swagger', '')
    if version == '':
        raise ValueError(f"Could not determine OpenAPI version from specification: {spec}")
    if int(version[0]) < 2:
        raise ValueError(f"OpenAPI version {version} not supported.")
    elif int(version[0]) == 2:
        return version2(spec)
