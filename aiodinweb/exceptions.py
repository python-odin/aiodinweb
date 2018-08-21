"""
Exceptions
~~~~~~~~~~

"""
from http import HTTPStatus
from typing import Any, Dict

from .resources import Error


class ImmediateHttpResponse(Exception):
    """
    A response that should be returned immediately.
    """
    def __init__(self, resource: Any, status: HTTPStatus=HTTPStatus.OK, headers: Dict[str, str]=None) -> None:
        self.resource = resource
        self.status = status
        self.headers = headers


class HttpError(ImmediateHttpResponse):
    """
    An error response that should be returned immediately.
    """
    def __init__(self, status: HTTPStatus, code_index: int=0, message: str=None, developer_message: str=None,
                 meta: Dict[str, Any]=None, headers: Dict[str, str]=None):
        super().__init__(
            Error.from_status(status,
                              code_index=code_index,
                              message=message,
                              developer_message=developer_message,
                              meta=meta),
            status, headers
        )


class PermissionDenied(HttpError):
    """
    Authorization is required before making this request.
    """
    def __init__(self, message: str=None, developer_method: str=None, headers: Dict[str, str]=None):
        super().__init__(HTTPStatus.UNAUTHORIZED, 0, message, developer_method, None, headers)


class AccessDenied(HttpError):
    """
    Access to the specified resource is denied.
    """
    def __init__(self, message: str=None, developer_method: str=None, headers: Dict[str, str]=None):
        super().__init__(HTTPStatus.FORBIDDEN, 0, message, developer_method, None, headers)
