#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
from jinja2 import Environment, PackageLoader, select_autoescape
import asyncio
import aiomysql

from session import SimpleSessionManager
from login import login_get, login_post
from users import create_user


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
    try:
        loop = asyncio.get_event_loop()
        pool = loop.run_until_complete(aiomysql.create_pool(
            user='avtory',
            unix_socket='/var/run/mysqld/mysqld.sock',
            db='avtory'))
        app = web.Application()
        app['env'] = Environment(
            loader=PackageLoader('avtory', 'templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )
        app['session'] = SimpleSessionManager()
        app['pool'] = pool

        app.router.add_get('/', hello)
        app.router.add_get('/login', login_get)
        app.router.add_post('/login', login_post)
        app.router.add_get('/create_user', create_user)
        app.router.add_post('/create_user', create_user)
        web.run_app(app)
    finally:
        pool.close()


if __name__ == "__main__":
    main()
