from aiodinweb import api

example_api = api.ApiCollection(name='example')


@example_api.listing
async def example_listing(request: api.Request):
    raise NotImplementedError()


@example_api.create
async def example_create(request: api.Request):
    pass


@example_api.detail
async def example_detail(request: api.Request):
    raise api.PermissionDenied("Uh uh aah!")


@example_api.update
async def example_update(request: api.Request):
    pass


@example_api.delete
async def example_delete(request: api.Request):
    pass


second_api = api.ApiCollection(name='second')


@second_api.listing
async def second_listing(request: api.Request):
    return [
        {"foo": 'bar'}
    ]
