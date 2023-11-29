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
    def add_parameter(cls, name, value):
        print(f"Adding parameter '{name}' with value of type '{type(value)}'")
        try:
            param = [param for param in cls.expected_parameters if param['name'] == name]
        except TypeError:
            raise ValueError(f"Parameter '{name}' not found in expected parameters. Expected parameters: {cls.expected_parameters}")

        if len(param) == 0:
            raise ValueError(f"Parameter '{name}' not found in expected parameters. Expected parameters: {cls.expected_parameters}")
        elif len(param) > 1:
            raise ValueError(f"Parameter '{name}' found multiple times in expected parameters.")
        else:
            param = param[0]
            cls.parameters[name] = {
                'name': name,
                'value': value,
                'in': param['in'],
                'required': param['required'],
            }
            if param.get('type') == 'integer':
                try:
                    int(value)
                except ValueError:
                    raise ValueError(f"Parameter '{name}' must be an integer.")
            if param.get('type') == 'string':
                if not isinstance(value, str):
                    raise ValueError(f"Parameter '{name}' must be a string.")
            if param.get('type') == 'array':
                if not isinstance(value, list):
                    raise ValueError(f"Parameter '{name}' must be a list.")
            if param.get('type') == 'boolean':
                if not isinstance(value, bool):
                    raise ValueError(f"Parameter '{name}' must be a boolean.")
            if param.get('type') == 'object':
                if not isinstance(value, dict):
                    raise ValueError(f"Parameter '{name}' must be a dictionary.")
            if param.get('type') == 'number':
                try:
                    float(value)
                except ValueError:
                    raise ValueError(f"Parameter '{name}' must be a number.")

            if isinstance(value, list):
                if param.get('minItems', 0) > len(value):
                    raise ValueError(f"Parameter '{name}' must have at least {param['minItems']} items.")
            if isinstance(value, str):
                if param.get('minLength', 0) > len(value):
                    raise ValueError(f"Parameter '{name}' must be at least {param['minLength']} characters long.")
                if param.get('maxLength', 4092) < len(value):
                    raise ValueError(f"Parameter '{name}' must be at most {param['maxLength']} characters long.")
            if not param.get('nullable', True) and value is None:
                raise ValueError(f"Parameter '{name}' must not be null.")
            if param.get('items', False):
                for v in value:
                    if param.get('items').get('minLength', 0) > len(v):
                        raise ValueError(f"Parameter '{name}' must be at least {param['items']['minLength']} characters long.")
                    if param.get('items').get('maxLength', 0) < len(v):
                        raise ValueError(f"Parameter '{name}' must be at most {param['items']['maxLength']} characters long.")



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
