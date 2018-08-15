from aiodinweb import api

example_api = api.ApiCollection()


@example_api.listing
async def example_listing(request: api.Request):
    pass


@example_api.create
async def example_create(request: api.Request):
    pass


@example_api.detail
async def example_detail(request: api.Request, resource_id: int):
    pass


@example_api.update
async def example_update(request: api.Request, resource_id: int):
    pass


@example_api.delete
async def example_delete(request: api.Request, resource_id: int):
    pass
