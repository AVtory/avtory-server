#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
from jinja2 import Environment, PackageLoader, select_autoescape
import logging

from config import create_pool, read_config
from session import SimpleSessionManager
from users import create_user, login_get, login_post, users, logout, user_mod
from category import (category_list, category_post, add_category_get,
                      add_category_post)


async def home(request):
    session_id, session_data = request.app['session'].get_session(request)
    response = web.Response(text=request
                            .app['env']
                            .get_template('home.html')
                            .render(privs=session_data['privs']),
                            content_type="text/html")
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

    app.router.add_get('/', home)
    app.router.add_get('/login', login_get)
    app.router.add_post('/login', login_post)
    app.router.add_get('/logout', logout)

    app.router.add_get('/create_user', create_user)
    app.router.add_post('/create_user', create_user)
    app.router.add_get('/users', users)
    app.router.add_post('/user_mod', user_mod)

    app.router.add_get('/categories', category_list)
    app.router.add_post('/categories', category_post)
    app.router.add_get('/add_category', add_category_get)
    app.router.add_post('/add_category', add_category_post)

    logger = logging.getLogger('aiohttp.access')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    # after the pool has been created, we should remove access to the db
    # password
    app['config'].remove_option('mysql', 'password')

    web.run_app(app)


if __name__ == "__main__":
    main()
