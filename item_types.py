#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web


async def add_item_type_get(request):
    session_id, session_data = request.app['session'].get_session(request)
    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('''SELECT Category_ID, Category_Name
            FROM CATEGORY
            ORDER BY Category_Name''')
            return web.Response(text=request.app['env']
                                .get_template('add_item_type.html')
                                .render(privs=session_data['privs'],
                                        categories=await cur.fetchall()),
                                content_type='text/html')


async def add_item_type_post(request):
    session_id, session_data = request.app['session'].get_session(request)
    data = await request.post()
    print(data)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''INSERT INTO ITEM_TYPE (Category_ID, Item_Type_Name)
                VALUES (%s, %s)''', (data['category_id'], data['item_type']))
            await conn.commit()

    return await add_item_type_get(request)


async def type_list(request):
    session_id, session_data = request.app['session'].get_session(request)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''SELECT Item_Type_ID, Category_Name, Item_Type_Name
                FROM ITEM_TYPE
                LEFT JOIN CATEGORY
                ON ITEM_TYPE.Category_ID=CATEGORY.Category_ID
                ORDER BY Category_Name, Item_Type_Name''')
            return web.Response(text=request.app['env']
                                .get_template('item_types.html')
                                .render(privs=session_data['privs'],
                                        item_types=await cur.fetchall()),
                                content_type='text/html')
