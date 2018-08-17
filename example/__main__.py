from aiohttp import web
from aiodinweb import api
from aiodinweb.openapi import OpenApiSpec

from .api import example_api, second_api


app = web.Application()

api.CORS(
    api.AioApi(
        api.ApiVersion(
            example_api,
            second_api,
            OpenApiSpec("Example", enable_ui=True),
        )
    ),
    origins=['http://localhost']
).add_routes(app)

# See http://localhost:8080/api/v1/openapi/ui
web.run_app(app)
