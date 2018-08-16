"""
AIO Odin Web
~~~~~~~~~~~~

Web APIs utilising Odin for encoding/decoding and validation.

"""
__authors__ = "Tim Savage"
__author_email__ = "tim@savage.company"
__copyright__ = "Copyright (C) 2018 Tim Savage"

from .containers import (
    ApiCollection,
    ApiVersion,
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
