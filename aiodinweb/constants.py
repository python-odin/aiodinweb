import enum

from typing import Union


class Method(enum.Enum):
    """
    HTTP Request Method
    """
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
    PATCH = 'PATCH'

    def __eq__(self, value: Union[str, 'Method']) -> bool:
        if isinstance(value, str):
            return value == self.value
        else:
            return super().__eq__(value)

    def __hash__(self):
        return hash(self.value)

