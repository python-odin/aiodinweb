"""
AIO Odin Web
~~~~~~~~~~~~

Web APIs utilising Odin for encoding/decoding and validation.

"""
__authors__ = "Tim Savage"
__author_email__ = "tim@savage.company"
__copyright__ = "Copyright (C) 2018 Tim Savage"

from http import HTTPStatus
from .containers import (
    ApiCollection,
    ApiVersion,
    AioApi,
)
from .constants import (
    Method,
    In,
    DataType,
)
from .cors import (
    CORS,
    AnyOrigin,
)
from .decorators import (
    operation,
    listing,
    create,
    detail,
    update,
    delete,
)
from .exceptions import (
    ImmediateHttpResponse,
    HttpError,
    AccessDenied,
    PermissionDenied,
)
from .web import (
    Request,
    Response,
)
