from http import HTTPStatus
from typing import Any, Dict


class Error:
    @staticmethod
    def from_status(http_status: HTTPStatus, code_index: int=0, message: str=None,
                    developer_message: str=None, meta: Any=None) -> Dict[str, Any]:
        """
        Automatically build an HTTP Response form HTTP Status code.

        :param http_status: HTTP Status code
        :param code_index: Unique status code index.
        :param message: End user message
        :param developer_message: Developer message
        :param meta: Additional error metadata

        """
        return dict(status=http_status,
                    code=(http_status * 100) + code_index,
                    message=message or http_status.phrase,
                    developer_message=developer_message or http_status.description,
                    meta=meta)
