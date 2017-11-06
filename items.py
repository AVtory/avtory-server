#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web


async def add_item_get(request):
    _, session_data = request.app['session'].get_session(request)


async def add_item_post(request):
    _, session_data = request.app['session'].get_session(request)


async def item_list(request, where_name=None, where_value=None):
    _, session_data = request.app['session'].get_session(request)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            query = '''SELECT *
            FROM ITEM
            LEFT JOIN CATEGORY
            ON ITEM.category_id = CATEGORY.category_id
            LEFT JOIN ITEM_TYPE
            ON ITEM.item_type_id=ITEM_TYPE.item_type_id
            '''
            query_value = None
            if where_name is not None:
                query += 'WHERE {} = %s'.format(where_name)
                query_value = (where_value,)
            await cur.execute(query, query_value)
            items = [{key: value
                      for key, value
                      in zip((col[0] for col in cur.description), item)}
                     for item in await cur.fetchall()]
            return web.Response(text=request
                                .app['env']
                                .get_template('items.html')
                                .render(admin=session_data['admin'],
                                        items=items),
                                content_type='text.html')
