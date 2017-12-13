#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
from item_types import type_list
from items import item_list


async def add_category_post(request):
    _, session_data = request.app['session'].get_session(request, True)
    data = await request.post()
    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''INSERT INTO CATEGORY (Category_Name)
                VALUES (%s)''', (data['category'],))
            await conn.commit()
    raise web.HTTPFound('/categories')


async def add_category_get(request):
    _, session_data = request.app['session'].get_session(request, True)
    return web.Response(text=request
                        .app['env']
                        .get_template('add_category.html')
                        .render(admin=session_data['admin']),
                        content_type='text/html')


async def category_list(request):
    _, session_data = request.app['session'].get_session(request)

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
                        .render(admin=session_data['admin'],
                                categories=categories),
                        content_type='text/html')


async def delete_categories(request, data):
    _, session_data = request.app['session'].get_session(request, True)
    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''DELETE FROM CATEGORY
                WHERE Category_ID = %s''', (data['delete_category'],))
            await conn.commit()
    return await category_list(request)


async def category_post(request):
    _, session_data = request.app['session'].get_session(request)
    data = await request.post()
    if 'show_item_types' in data:
        return await type_list(request, data['show_item_types'])
    elif 'show_equipment' in data:
        return await item_list(request, where_name='ITEM.category_id',
                               where_value=data['show_equipment'])
    elif 'delete_category' in data:
        return await delete_categories(request, data)
