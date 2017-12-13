#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
from items import item_list


async def location_list(request, department_id=None):
    _, session_data = request.app['session'].get_session(request)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''SELECT *
                FROM LOCATION
                JOIN DEPARTMENT
                ON LOCATION.department_id=DEPARTMENT.department_id
                {}
                ORDER BY Department_Name, Location_Name
                '''.format("" if department_id is None else
                           "WHERE LOCATION.department_id = %s"),
                None if department_id is None else (department_id,))
            locations = [{k: v
                          for k, v
                          in zip((col[0] for col in cur.description), loc)}
                         for loc in await cur.fetchall()]
    return web.Response(text=request.app['env']
                        .get_template('locations.html')
                        .render(admin=session_data['admin'],
                                locations=locations),
                        content_type='text/html')


async def add_location_get(request):
    _, session_data = request.app['session'].get_session(request)
    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''SELECT Department_ID, Department_Name
                FROM DEPARTMENT
                ORDER BY Department_Name''')
            return web.Response(text=request
                                .app['env']
                                .get_template('add_location.html')
                                .render(admin=session_data['admin'],
                                        departments=await cur.fetchall()),
                                content_type='text/html')


async def add_location_post(request):
    _, session_data = request.app['session'].get_session(request)
    data = await request.post()

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''INSERT INTO LOCATION (Department_ID, Location_Name)
                VALUES (%s, %s)''',
                (data['department_id'], data['location']))
            await conn.commit()

    raise web.HTTPFound('/locations')


async def delete_location(request, location_id):
    _, session_data = request.app['session'].get_session(request, True)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''DELETE FROM LOCATION
                WHERE location_id = %s''', (location_id,))
            await conn.commit()
    return await location_list(request)


async def location_post(request):
    _, session_data = request.app['session'].get_session(request)

    data = await request.post()
    if 'show_items' in data:
        return await item_list(request, where_name="LOCATION.location_id",
                               where_value=data['show_items'])
    elif 'delete_location' in data:
        return await delete_location(request, data['delete_location'])
