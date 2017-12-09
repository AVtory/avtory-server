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
from item_types import (type_list, add_item_type_get, add_item_type_post,
                        item_type_post)
from items import item_list, add_item_post, view_item_post, view_item_get
from department import (department_list, department_post, add_department_get,
                        add_department_post)
from location import (location_list, location_post, add_location_get,
                      add_location_post)


async def home(request):
    _, session_data = request.app['session'].get_session(request)
    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''SELECT Item_Name, Description, Date_Added, ITEM_TYPE.Item_Type_Name
                FROM ITEM
                JOIN ITEM_TYPE ON ITEM.Item_Type_ID = ITEM_TYPE.Item_Type_ID
                ORDER BY Item_ID DESC LIMIT 10''')
            items = [{key: value for key, value in
                      zip((col[0] for col in cur.description),
                          data)}
                     for data in await cur.fetchall()]

            await cur.execute(
                '''SELECT
                Comment, ITEM.Item_Name,
                CHECKOUT.Due_Date, CHECKOUT.Date_Checked_Out,
                EMPLOYEE.Last_Name, EMPLOYEE.First_Name
                FROM LOG
                JOIN ITEM ON LOG.Item_ID = ITEM.Item_ID
                JOIN EMPLOYEE ON LOG.Employee_ID = EMPLOYEE.Employee_ID
                JOIN CHECKOUT ON LOG.Item_ID = CHECKOUT.Item_ID
                    AND LOG.Log_Date = CHECKOUT.Date_Checked_Out
                WHERE LOG.Event = "checkout"
                ORDER BY LOG.Log_ID DESC LIMIT 10''')
            checkout = [{key: value for key, value in
                         zip((col[0] for col in cur.description),
                             data)}
                        for data in await cur.fetchall()]

            await cur.execute(
                '''SELECT
                Log_Date, Comment, ITEM.Item_Name,
                EMPLOYEE.Last_Name, EMPLOYEE.First_Name
                FROM LOG
                JOIN ITEM ON LOG.Item_ID = ITEM.Item_ID
                JOIN EMPLOYEE ON EMPLOYEE.Employee_ID = LOG.Employee_ID
                WHERE LOG.Event = "checkin"
                ORDER BY LOG.Log_ID DESC LIMIT 10''')
            checkin = [{key: value for key, value in
                        zip((col[0] for col in cur.description),
                            data)}
                       for data in await cur.fetchall()]

    return web.Response(text=request
                        .app['env']
                        .get_template('home.html')
                        .render(admin=session_data['admin'],
                                checkout=checkout,
                                checkin=checkin,
                                items=items),
                        content_type="text/html")


def main():
    app = web.Application()
    app['config'] = read_config()
    app['env'] = Environment(
        loader=PackageLoader('avtory', 'templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    app['session'] = SimpleSessionManager()
    app['pool'] = create_pool(app['config'].items('mysql'))
    '''WEBPAGE -> PYTHON FUNCTION'''
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

    app.router.add_get('/item_types', type_list)
    app.router.add_post('/item_types', item_type_post)
    app.router.add_get('/add_item_type', add_item_type_get)
    app.router.add_post('/add_item_type', add_item_type_post)

    app.router.add_get('/item_list', item_list)
    app.router.add_post('/add_item', add_item_post)
    app.router.add_get('/view_item', view_item_get)
    app.router.add_post('/view_item', view_item_post)

    app.router.add_get('/departments', department_list)
    app.router.add_post('/departments', department_post)
    app.router.add_get('/add_department', add_department_get)
    app.router.add_post('/add_department', add_department_post)

    app.router.add_get('/locations', location_list)
    app.router.add_post('/locations', location_post)
    app.router.add_get('/add_location', add_location_get)
    app.router.add_post('/add_location', add_location_post)

    logger = logging.getLogger('aiohttp.access')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    # after the pool has been created, we should remove access to the db
    # password
    app['config'].remove_option('mysql', 'password')

    web.run_app(app)


if __name__ == "__main__":
    main()
