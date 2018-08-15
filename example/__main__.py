from aiohttp import web
from aiodinweb.aiohttp import AioApiInterface

from .api import example_api


app = web.Application()
AioApiInterface(
    example_api
).setup(app)
web.run_app(app)
