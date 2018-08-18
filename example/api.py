from aiodinweb import api


class ExampleApi(api.ResourceApi):
    name = 'example'

    @api.listing
    async def example_listing(self, request: api.Request):
        raise NotImplementedError()

    @api.create
    async def example_create(self, request: api.Request):
        pass

    @api.detail
    async def example_detail(self, request: api.Request):
        raise api.PermissionDenied("Uh uh aah!")

    @api.update
    async def example_update(self, request: api.Request):
        pass

    @api.delete
    async def example_delete(self, request: api.Request):
        pass


second_api = api.ApiCollection(name='second')


@second_api.listing
async def second_listing(request: api.Request):
    return [
        {"name": 'foo'},
        {"name": 'bar'},
    ]
