from aiohttp import web
from http import HTTPStatus
from typing import Any, Dict


class Request(web.Request):
    """
    Incoming HTTP request
    """
    request_codec: Any = None
    response_codec: Any = None


class Response(web.Response):
    """
    Outgoing HTTP response
    """
    @classmethod
    def create(cls, request: Request, body: Any=None, status: HTTPStatus=None,
               headers: Dict[str, str]=None) -> 'Response':
        """
        Generate a Response.

        :param request: Request object
        :param body: Body of the response
        :param status: HTTP status code
        :param headers: Any headers.

        """
        if body is None:
            return cls(
                status=status or HTTPStatus.NO_CONTENT,
                headers=headers
            )
        else:
            body = request.response_codec.dumps(body)
            return cls(
                body=body, headers=headers,
                status=status or HTTPStatus.OK,
                content_type=request.response_codec.content_type
            )
