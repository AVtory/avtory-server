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


async def view_item(request, item_id):
    _, session_data = request.app['session'].get_session(request)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''SELECT *
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
                WHERE Item_ID=%s
                ''', (item_id))
            item = {key: value for key, value in
                    zip((col[0] for col in cur.description),
                        await cur.fetchone())}

            await cur.execute(
                '''SELECT *
                FROM CHECKOUT
                JOIN EMPLOYEE
                ON EMPLOYEE.Employee_ID=CHECKOUT.Employee_ID
                WHERE Item_ID=%s''', item_id)
            if cur.rowcount == 0:
                action = "Checkout"
                checkout = None
            else:
                action = "Checkin"
                checkout = {key: value for key, value in
                            zip((col[0] for col in cur.description),
                                await cur.fetchone())}

            await cur.execute(
                '''SELECT Log_Date, Event, Comment, EMPLOYEE.Last_Name, EMPLOYEE.First_Name
                FROM LOG
                JOIN EMPLOYEE
                ON EMPLOYEE.Employee_ID=LOG.Employee_ID
                WHERE Item_ID=%s
                ORDER BY Log_Date DESC''',
                item_id)
            log = [{key: value for key, value
                    in zip((col[0] for col in cur.description),
                           data)}
                   for data in await cur.fetchall()]

    link = '{}view_item?Item_ID={}'.format(request.app['config']['avtory']
                                           ['website'], item_id)

    return web.Response(text=request.app['env']
                        .get_template('view_item.html')
                        .render(admin=session_data['admin'],
                                item=item,
                                log=log,
                                action=action,
                                checkout=checkout,
                                link=link),
                        content_type="text/html")


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


async def delete_item(request, item_id):
    ''' Deletes a Equipment Item & redirects to item_list page '''
    _, session_data = request.app['session'].get_session(request)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
            DELETE FROM ITEM
            WHERE item_id=%s""", (item_id,))
            await conn.commit()
            raise web.HTTPFound('/item_list')


async def view_item_post(request):
    '''WAITING FOR USER ACTION '''
    _, session_data = request.app['session'].get_session(request)

    '''
    Edit/Update an Item from the view_item page
    '''
    data = await request.post()
    action = data['action']

    # Call appropriate Delete, Show, or Modify functions
    if action == 'delete':
        # Pass in the request and item_ID --> Not good
        return await delete_item(request, data['Item_ID'])
    elif action == 'show':
        # View item based on ID --> Should be good
        return await view_item(request, data['Item_ID'])
    elif action == 'modify':
        return await modify_item(request, data)
    elif action == 'Checkout':
        return await checkout(request, data)
    elif action == 'Checkin':
        return await checkin(request, data)


async def checkout(request, data):
    _, session_data = request.app['session'].get_session(request)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''INSERT INTO LOG
                (Log_Date, Event, Employee_ID, Item_ID, Comment)
                VALUES
                (NOW(), "checkout", %s, %s, %s)''',
                (session_data['employee_id'], data['Item_ID'],
                 data['comment']))
            await cur.execute(
                '''INSERT INTO CHECKOUT
                (Item_ID, Employee_ID, Date_Checked_Out, Due_Date)
                VALUES
                (%s, %s, NOW(), NOW() + INTERVAL %s DAY)''',
                (data['Item_ID'], session_data['employee_id'],
                 data['duration']))
            await conn.commit()
    return await view_item(request, data['Item_ID'])


async def checkin(request, data):
    _, session_data = request.app['session'].get_session(request)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                '''INSERT INTO LOG
                (Log_Date, Event, Employee_ID, Item_ID, Comment)
                VALUES
                (NOW(), "checkin", %s, %s, %s)''',
                (session_data['employee_id'],
                 data['Item_ID'],
                 data['comment']))
            await cur.execute('DELETE FROM CHECKOUT WHERE Item_ID=%s',
                              data['Item_ID'])
            await conn.commit()
    return await view_item(request, data['Item_ID'])


async def view_item_get(request):
    return await view_item(request, request.query['Item_ID'])


async def modify_item(request, data):
    _, session_data = request.app['session'].get_session(request)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """UPDATE ITEM
                SET Item_Name = %s,
                Description = %s,
                Model = %s,
                Serial = %s
                WHERE Item_ID=%s""",
                (data['item_name'],
                 data['item_descp'],
                 data['item_model'],
                 data['item_serial'],
                 data['Item_ID']))
            await conn.commit()

    raise web.HTTPFound('/item_list')
