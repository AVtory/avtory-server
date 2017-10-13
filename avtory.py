#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web


async def hello(request):
    return web.Response(
        text="<html><title>Hello world!</title>"
        "<body>Hello world!</body></html>",
        content_type="text/html")


if __name__ == "__main__":
    app = web.Application()
    app.router.add_get('/', hello)

    web.run_app(app)
