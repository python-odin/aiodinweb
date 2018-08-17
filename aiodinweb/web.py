from aiohttp import web
from http import HTTPStatus
from typing import Any, Dict


class Request(web.Request):
    """
    Incoming HTTP request
    """
    current_operation = None
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
                headers=headers,
                content_type=request.response_codec.content_type
            )
        else:
            body = request.response_codec.dumps(body)
            return cls(
                body=body, headers=headers,
                status=status or HTTPStatus.OK,
                content_type=request.response_codec.content_type
            )

    @classmethod
    def from_status(cls, status: HTTPStatus, *,
                    reason: str=None,
                    description: str=None,
                    headers: Dict[str, str]=None) -> 'Response':
        """
        Generate a response from a Status code
        :param status: HTTP Status code
        :param reason: Error reason (defaults to phrase of HTTPStatus)
        :param description: Error description (defaults to description of
            HTTPStatus)
        :param headers: Any headers.

        """
        return cls(
            status=status,
            reason=reason or status.phrase,
            text=description or status.description,
            headers=headers,
        )
