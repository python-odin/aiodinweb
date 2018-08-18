import odin

from http import HTTPStatus
from typing import Any


class Error(odin.Resource):
    """
    Standard error response
    """
    status = odin.IntegerField(verbose_name="HTTP status code")
    code = odin.IntegerField(verbose_name="Error code")
    message = odin.StringField(verbose_name="End user message")
    developer_message = odin.StringField(verbose_name="Developer message", null=True)
    meta = odin.DictField(verbose_name='Error specific metadata', null=True)

    @classmethod
    def from_status(
            cls, status: HTTPStatus, *,
            code_index: int=0,
            message: str=None,
            developer_message: str=None,
            meta: Any=None
    ) -> 'Error':
        """
        Automatically build an HTTP Response form HTTP Status code.

        :param status: HTTP Status code
        :param code_index: Unique status code index.
        :param message: End user message
        :param developer_message: Developer message
        :param meta: Additional error metadata

        """
        return cls(
            status=status,
            code=(status * 100) + code_index,
            message=message or status.phrase,
            developer_message=developer_message or status.description,
            meta=meta
        )
