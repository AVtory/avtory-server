#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
from location import location_list
from items import item_list


async def add_department_get(request):
    _, session_data = request.app['session'].get_session(request, True)
    return web.Response(text=request
                        .app['env']
                        .get_template('add_department.html')
                        .render(admin=session_data['admin']),
                        content_type='text/html')


async def add_department_post(request):
    _, session_data = request.app['session'].get_session(request, True)
    data = await request.post()
    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''INSERT INTO DEPARTMENT (department_name)
                VALUES (%s)''', (data['department'],))
            await conn.commit()
    return await add_department_get(request)


async def department_list(request):
    _, session_data = request.app['session'].get_session(request)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''SELECT department_id, department_name
                FROM DEPARTMENT
                ORDER BY department_name''')
            departments = {id: name
                           for id, name
                           in await cur.fetchall()}
    return web.Response(text=request.app['env']
                        .get_template('departments.html')
                        .render(admin=session_data['admin'],
                                departments=departments),
                        content_type='text/html')


async def delete_department(request, department_id):
    _, session_data = request.app['session'].get_session(request, True)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''DELETE FROM DEPARTMENT
                WHERE department_id = %s''', (department_id,))
            await conn.commit()
    return await department_list(request)


async def department_post(request):
    _, session_data = request.app['session'].get_session(request)
    data = await request.post()

    if 'show_equipment' in data:
        return await item_list(request, where_name='LOCATION.department_id',
                               where_value=data['show_equipment'])
    elif 'show_locations' in data:
        return await location_list(request, data['show_locations'])
    elif 'delete_department' in data:
        return await delete_department(request, data['delete_department'])
