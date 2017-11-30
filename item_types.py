#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web

from items import item_list


async def add_item_type_get(request):
    _, session_data = request.app['session'].get_session(request)
    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('''SELECT Category_ID, Category_Name
            FROM CATEGORY
            ORDER BY Category_Name''')
            return web.Response(text=request.app['env']
                                .get_template('add_item_type.html')
                                .render(admin=session_data['admin'],
                                        categories=await cur.fetchall()),
                                content_type='text/html')


async def add_item_type_post(request):
    _, session_data = request.app['session'].get_session(request)
    data = await request.post()

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''INSERT INTO ITEM_TYPE (Category_ID, Item_Type_Name)
                VALUES (%s, %s)''', (data['category_id'], data['item_type']))
            await conn.commit()

    return await add_item_type_get(request)


async def type_list(request, category_id=None):
    _, session_data = request.app['session'].get_session(request)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            if category_id is None:
                await cur.execute(
                    '''SELECT Item_Type_ID, Category_Name, Item_Type_Name
                    FROM ITEM_TYPE
                    JOIN CATEGORY
                    ON ITEM_TYPE.Category_ID=CATEGORY.Category_ID
                    ORDER BY Category_Name, Item_Type_Name''')
            else:
                await cur.execute(
                    '''SELECT Item_Type_ID, Category_Name, Item_Type_Name
                    FROM ITEM_TYPE
                    JOIN CATEGORY
                    ON ITEM_TYPE.Category_ID=CATEGORY.Category_ID
                    AND ITEM_TYPE.Category_ID=%s
                    ORDER BY Category_Name, Item_Type_Name''', (category_id,))
            return web.Response(text=request.app['env']
                                .get_template('item_types.html')
                                .render(admin=session_data['admin'],
                                        item_types=await cur.fetchall()),
                                content_type='text/html')


async def delete_item(request, data):
    _, session_data = request.app['session'].get_session(request, True)
    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''DELETE FROM ITEM_TYPE
                WHERE Item_Type_ID = %s''', (data['delete_item'],))
            await conn.commit()
    return await type_list(request)


async def item_type_post(request):
    _, session_data = request.app['session'].get_session(request)
    data = await request.post()
    if 'delete_item' in data:
        return await delete_item(request, data)
    elif 'show_items' in data:
        return await item_list(request, where_name='ITEM.item_type_id',
                               where_value=data['show_items'])
