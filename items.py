#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web


async def item_list(request, category=None, item_type=None):
    _, session_data = request.app['session'].get_session(request)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            if category is None and item_type is None:
                await cur.execute(
                    '''SELECT
                    item_id, ITEM.category_id, location_id, finance_id,
                    ITEM.item_type_id, item_name, date_added, description,
                    model, serial, in_service
                    FROM ITEM
                    LEFT JOIN CATEGORY
                    ON ITEM.category_id=CATEGORY.category_id
                    LEFT JOIN ITEM_TYPE
                    ON ITEM.item_type_id=ITEM_TYPE.item_type_id''')
            elif category is not None:
                await cur.execute(
                    '''SELECT
                    item_id, ITEM.category_id, location_id, finance_id,
                    ITEM.item_type_id, item_name, date_added, description,
                    model, serial, in_service
                    FROM ITEM
                    LEFT JOIN CATEGORY
                    ON ITEM.category_id = CATEGORY.category_id
                    AND ITEM.category_id = %s
                    LEFT JOIN ITEM_TYPE
                    ON ITEM.item_type_id = ITEM_TYPE.item_type_id''',
                    (category,))
            elif item_type is not None:
                await cur.execute(
                    '''SELECT
                    item_id, ITEM.category_id, location_id, finance_id,
                    ITEM.item_type_id, item_name, date_added, description,
                    model, serial, in_service
                    FROM ITEM
                    LEFT JOIN CATEGORY
                    ON ITEM.category_id = CATEGORY.category_id
                    LEFT JOIN ITEM_TYPE
                    ON ITEM.item_type_id = ITEM_TYPE.item_type_id
                    AND ITEM.item_type_id = %s''',
                    (item_type,))
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
