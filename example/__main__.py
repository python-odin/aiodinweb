from aiohttp import web
from aiodinweb import api
from aiodinweb.openapi import OpenApiSpec

from .api import ExampleApi, second_api


app = web.Application()

api.CORS(
    api.AioApi(
        api.ApiVersion(
            ExampleApi(),
            second_api,

            # See http://localhost:8080/api/v1/openapi/ui
            OpenApiSpec("Example", enable_ui=True),
        )
    ),
    origins=['http://localhost']
).add_routes(app)

web.run_app(app)
