#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web


async def add_item_post(request):
    _, session_data = request.app['session'].get_session(request)
    data = await request.post()
    data = {k: v
            for k, v
            in data.items()}

    async def option_prompt(table,
                            id_column, name_column,
                            where_name=None, where_value=None):
        query = (
            '''SELECT {id_column}, {name_column}
            FROM {table}\n'''
            .format(table=table, id_column=id_column,
                    name_column=name_column))
        if where_name is not None:
            query += "WHERE {}=%s\n".format(where_name)
        query += 'ORDER BY {}'.format(name_column)
        async with request.app['pool'].acquire() as conn:
            async with conn.cursor() as cur:
                if where_name is None:
                    await cur.execute(query)
                else:
                    await cur.execute(query, (where_value,))
                options = await cur.fetchall()

        return web.Response(text=request.app['env']
                            .get_template('add_item_select.html')
                            .render(admin=session_data['admin'],
                                    data=data,
                                    prompt_id=id_column,
                                    options=options),
                            content_type="text/html")

    if 'Location_ID' not in data:
        if 'Department_ID' not in data:
            return await option_prompt("DEPARTMENT", "Department_ID",
                                       "Department_Name")
        else:
            return await option_prompt("LOCATION",
                                       "Location_ID", "Location_Name",
                                       "Department_ID", data['Department_ID'])
    if 'Category_ID' not in data:
        return await option_prompt("CATEGORY", "Category_ID", "Category_Name")
    if 'Item_Type_ID' not in data:
        return await option_prompt("ITEM_TYPE",
                                   "Item_Type_ID", "Item_Type_Name",
                                   "Category_ID", data['Category_ID'])
    if 'Item_Name' not in data:
        return web.Response(text=request.app['env']
                            .get_template('add_item_form.html')
                            .render(admin=session_data['admin'],
                                    data=data,
                                    inputs=[
                                        ('Item_Name', 'Name'),
                                        ('Description', 'Description'),
                                        ('Model', 'Model #'),
                                        ('Serial', 'Serial #'),
                                        ('In_Service', 'In Service'),
                                        ('Price', 'Price'),
                                        ('Depreciation', 'Depreciation'),
                                    ]),
                            content_type="text/html")
    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''INSERT INTO FINANCE
                (Price, Depreciation)
                VALUES (%s, %s)''',
                (data['Price'], data['Depreciation']))
            await cur.execute(
                '''INSERT INTO ITEM
                (Category_ID, Location_ID, Finance_ID, Item_Type_ID,
                Item_Name, Date_Added, Description,
                Model, Serial, In_service)
                VALUES (%s, %s, LAST_INSERT_ID(), %s,
                %s, NOW(), %s,
                %s, %s, %s)''',
                (data['Category_ID'], data['Location_ID'],
                 data['Item_Type_ID'],
                 data['Item_Name'], data['Description'],
                 data['Model'], data['Serial'], data['In_Service']))
            await conn.commit()

    return await item_list(request)


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
            LEFT JOIN FINANCE
            ON ITEM.finance_id=FINANCE.finance_id
            LEFT JOIN LOCATION
            ON ITEM.location_id=LOCATION.location_id
            LEFT JOIN DEPARTMENT
            ON LOCATION.department_id=DEPARTMENT.department_id
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
    return web.Response(text=request.app['env']
                        .get_template('items.html')
                        .render(admin=session_data['admin'], items=items),
                        content_type='text.html')
