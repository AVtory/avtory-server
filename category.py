#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web


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
                        .render(categories=categories),
                        content_type='text/html')
