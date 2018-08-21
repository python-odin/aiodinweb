# flake8: noqa
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
    ResourceApi,
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
    # Routing
    operation,
    route,
    listing,
    create,
    detail,
    update,
    patch,
    delete,

    # Request
    query_param,
    header_param,
    cookie_param,

    # Doc
    deprecated,
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
