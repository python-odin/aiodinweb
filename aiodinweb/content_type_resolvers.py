"""
Content Type Resolves
~~~~~~~~~~~~~~~~~~~~~

Collection of methods for resolving the content type of a request.

"""
from typing import Callable, Iterable, Optional

from .web import Request


ContentTypeResolver = Callable[[Request], Optional[str]]


def accepts_header(request: Request) -> str:
    """
    Resolve content type from the accepts header.
    """
    return request.headers.get('ACCEPTS')


def content_type_header(request: Request) -> str:
    """
    Resolve content type from the content-type header.
    """
    return request.content_type


def specific_default(content_type: str) -> ContentTypeResolver:
    """
    Specify a specific default content type.

    :param content_type: The content type to use.

    """
    def resolver(_: Request) -> str:
        return content_type

    return resolver


def parse_content_type(value: str) -> str:
    """
    Parse out the content type from a content type header.

    >>> parse_content_type('application/json; charset=utf8')
    'application/json'

    """
    if not value:
        return ''

    return value.split(';')[0].strip()


def resolve(type_resolvers: Iterable[ContentTypeResolver],
            request: Request, default_content_type: str=None) -> Optional[str]:
    """
    Resolve content types from a request.
    """
    for resolver in type_resolvers:
        content_type = parse_content_type(resolver(request))
        if content_type:
            return content_type
    return default_content_type
