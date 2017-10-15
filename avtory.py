#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
from jinja2 import Environment, PackageLoader, select_autoescape
from session import SimpleSessionManager


async def hello(request):
    session_id, session_data = await request.app['session'][request]
    response = web.Response(text=request
                            .app['env']
                            .get_template('hello.html')
                            .render(),
                            content_type="text/html")
    response.set_cookie('session_id', session_id)
    return response


def main():
    app = web.Application()
    app['env'] = Environment(
        loader=PackageLoader('avtory', 'templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    app['session'] = SimpleSessionManager()

    app.router.add_get('/', hello)
    web.run_app(app)


if __name__ == "__main__":
    main()
