from aiohttp import web
from aiodinweb import api
from aiodinweb.openapi import OpenApiSpec

from .api import example_api, second_api


app = web.Application()

api_v1 = api.ApiVersion(
    example_api,
    second_api,
    OpenApiSpec("Example", enable_ui=True),
)

api.CORS(api.AioApi(api_v1), ['http://localhost']).add_routes(app)

web.run_app(app)
