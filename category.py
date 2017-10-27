#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web


async def add_category_post(request):
    session_id, session_data = (request.app['session']
                                .get_session(request, True))
    data = await request.post()
    print(data, data['category'])
    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''INSERT INTO CATEGORY (Category_Name)
                VALUES (%s)''', (data['category'],))
            await conn.commit()
    return await add_category_get(request)


async def add_category_get(request):
    session_id, session_data = (request.app['session']
                                .get_session(request, True))
    return web.Response(text=request
                        .app['env']
                        .get_template('add_category.html')
                        .render(privs=session_data['privs']),
                        content_type='text/html')


async def category_list(request):
    session_id, session_data = request.app['session'].get_session(request)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''SELECT Category_ID, Category_Name
                FROM CATEGORY
                ORDER BY Category_Name''')
            categories = {id: name
                          for id, name
                          in await cur.fetchall()}
    return web.Response(text=request.app['env']
                        .get_template('categories.html')
                        .render(privs=session_data['privs'],
                                categories=categories),
                        content_type='text/html')


async def show_equipment(request, data, session_data):
    pass


async def delete_categories(request, data):
    session_id, session_data = (request.app['session']
                                .get_session(request, True))
    category_id = [cat_id
                   for cat_id, value in data.items()
                   if value == "on"][0]
    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''DELETE FROM CATEGORY
                WHERE Category_ID = %s''', (category_id,))
            await conn.commit()
    return await category_list(request)


async def category_post(request):
    session_id, session_data = request.app['session'].get_session(request)
    data = await request.post()
    if 'show_equipment' in data:
        return await show_equipment(request, data, session_data)
    elif 'delete_categories' in data:
        return await delete_categories(request, data)
