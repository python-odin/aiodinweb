"""
Content Type Resolves
~~~~~~~~~~~~~~~~~~~~~

Collection of methods for resolving the content type of a request.

"""
from aiohttp.web import Request
from typing import Callable, Optional


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
