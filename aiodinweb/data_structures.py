from typing import Union, Sequence

from . import constants


class Parameter:
    """
    Describes a single operation parameter.

    A unique parameter is defined by a combination of a name and location.
    """
    def __init__(self, name: str, in_: constants.In, *,
                 description: str=None,
                 required: bool=None,
                 allow_empty: bool=None):
        """
        :param name: The name of the parameter
        :param in_: The location of the parameter
        :param description: A brief description of the parameter.
        :param required: Determines whether this parameter is mandatory.
        :param allow_empty: Sets the ability to pass empty-valued parameters.
        """
        self.name = name
        self.in_ = in_
        self.description = description
        self.required = required
        self.allow_empty = allow_empty


class UrlPath(list):
    """
    URL Path object.
    """
    __slots__ = ()

    @classmethod
    def from_object(cls, obj: Union['UrlPath', str, Sequence]) -> 'UrlPath':
        if isinstance(obj, UrlPath):
            return obj
        if isinstance(obj, str):
            return UrlPath.parse(obj)
        raise ValueError(f"Unable to convert object to UrlPath: {obj!r}")

    @classmethod
    def parse(cls, url_path: str) -> 'UrlPath':
        """
        Parse a string into a URL path
        """
        if not url_path:
            return cls()
