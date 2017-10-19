#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
from jinja2 import Environment, PackageLoader, select_autoescape
from config import create_pool, read_config

from session import SimpleSessionManager
from users import create_user, login_get, login_post


async def hello(request):
    session_id, session_data = request.app['session'].get_session(request)
    response = web.Response(text=request
                            .app['env']
                            .get_template('hello.html')
                            .render(),
                            content_type="text/html")
    response.set_cookie('session_id', session_id)
    return response


def main():
    app = web.Application()
    app['config'] = read_config()
    app['env'] = Environment(
        loader=PackageLoader('avtory', 'templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    app['session'] = SimpleSessionManager()
    app['pool'] = create_pool(app['config'].items('mysql'))

    app.router.add_get('/', hello)
    app.router.add_get('/login', login_get)
    app.router.add_post('/login', login_post)
    app.router.add_get('/create_user', create_user)
    app.router.add_post('/create_user', create_user)

    # after the pool has been created, we should remove access to the db
    # password
    app['config'].remove_option('mysql', 'password')

    web.run_app(app)


if __name__ == "__main__":
    main()
