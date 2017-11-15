#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import secrets
import string
from aiohttp import web
from hashlib import pbkdf2_hmac
from base64 import b64encode, b64decode
from config import create_pool, read_config
from argparse import ArgumentParser
from getpass import getpass
import asyncio


def hash_pw(password, salt, work_factor):
    return pbkdf2_hmac('sha512', password, salt, 1 << work_factor, dklen=64)


async def logout(request):
    session_id, session_data = request.app['session'].get_session(request)
    response = web.Response(text='''<html><head>
    <meta http-equiv="refresh" content="0; url=/" />
    </head></html>''', content_type='text/html')
    response.del_cookie('session_id')
    return response


async def delete_user(request, user_id):
    _, session_data = request.app['session'].get_session(request, True)
    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
            DELETE FROM USERS
            WHERE user_id=%s""", (user_id,))
            await conn.commit()
            raise web.HTTPFound('/users')


async def show_user(request, employee_id):
    _, session_data = request.app['session'].get_session(request, True)
    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """SELECT USERS.user_id, employee_id, USERS.username,
                last_name, first_name, email,
                phone_number, is_admin, role
                FROM EMPLOYEE
                JOIN USERS ON USERS.user_id=EMPLOYEE.user_id
                WHERE employee_id=%s""", (employee_id,))
            userdata = {key: value
                        for key, value
                        in zip((col[0] for col in cur.description),
                               await cur.fetchone())}
            return web.Response(text=request.app['env']
                                .get_template('user_mod.html')
                                .render(admin=session_data['admin'],
                                        userdata=userdata),
                                content_type='text/html')


async def modify_user(request, data):
    _, session_data = request.app['session'].get_session(request, True)
    phonenumber = [n for n in data['phone_number']
                   if n in string.digits]
    phonenumber.insert(3, '-')
    phonenumber.insert(7, '-')
    phonenumber = ''.join(phonenumber)

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """UPDATE EMPLOYEE
                SET Last_Name = %s,
                First_Name = %s,
                Email = %s,
                Phone_Number = %s,
                Is_Admin = %s,
                Role = %s
                WHERE employee_id=%s""",
                (data['last_name'],
                 data['first_name'],
                 data['email'],
                 phonenumber,
                 1 if 'admin' in data and data['admin'] == 'on' else 0,
                 data['role'],
                 data['employee_id']))
            if data['password'] != '':
                salt = secrets.token_urlsafe(32).encode()
                password_hash = hash_pw(data['password'].encode(),
                                        salt, 15)
                password_hash = b64encode(password_hash)
                await cur.execute(
                    """UPDATE USERS
                    SET Password_Hash = %s,
                    Salt = %s
                    WHERE user_id = %s
                    """, (password_hash, salt, data['user_id']))
            await conn.commit()
    raise web.HTTPFound('/users')


async def user_mod(request):
    data = await request.post()
    action = data['action']

    if action == 'delete':
        return await delete_user(request, data['user_id'])
    elif action == 'show':
        return await show_user(request, data['employee_id'])
    elif action == 'modify':
        return await modify_user(request, data)


async def insert_user(pool, username, password, lastname, firstname, email,
                      phonenumber, admin, role):
    salt = secrets.token_urlsafe(32).encode()
    password_hash = hash_pw(password, salt, 15)
    password_hash = b64encode(password_hash)

    phonenumber = [n for n in phonenumber
                   if n in string.digits]
    phonenumber.insert(3, '-')
    phonenumber.insert(7, '-')
    phonenumber = ''.join(phonenumber)

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
            INSERT INTO USERS
            (Username, Password_Hash, Salt, Work_Factor)
            VALUES (%s, %s, %s, %s)""",
                              (username, password_hash, salt, 15))
            await cur.execute("""
            INSERT INTO EMPLOYEE
            (user_id, First_Name, Last_Name,
            Email, Phone_Number, Is_Admin, Role)
            VALUES (LAST_INSERT_ID(), %s, %s, %s, %s, %s, %s)""",
                              (firstname, lastname,
                               email, phonenumber, admin, role))
            await conn.commit()


async def create_user(request):
    _, session_data = request.app['session'].get_session(request, True)
    data = await request.post()

    if len(data) > 0:
        username = data['username']
        password = data['password'].encode()
        lastname = data['lastname']
        firstname = data['firstname']
        email = data['email']
        phonenumber = data['phonenumber']
        role = data['role']
        admin = 1 if 'admin' in data and data['admin'] == 'on' else 0

        await insert_user(request.app['pool'], username, password, lastname,
                          firstname, email, phonenumber, admin, role)

    return web.Response(text=request
                        .app['env']
                        .get_template('create_user.html')
                        .render(admin=session_data['admin']),
                        content_type='text/html')


async def login_get(request):
    return web.Response(text=request
                        .app['env']
                        .get_template('login.html')
                        .render(),
                        content_type='text/html')


async def users(request):
    _, session_data = (request.app['session'].get_session(request, True))

    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """SELECT USERS.user_id, employee_id, USERS.username,
                last_name, first_name, email,
                phone_number, is_admin, role
                FROM EMPLOYEE
                JOIN USERS ON USERS.user_id=EMPLOYEE.user_id""")
            columns = tuple((col[0] for col in cur.description))
            userlist = {row[1]: {key: value
                                 for key, value
                                 in zip(columns, row)}
                        for row
                        in await cur.fetchall()}

    return web.Response(text=request.app['env']
                        .get_template('users.html')
                        .render(admin=session_data['admin'],
                                userlist=userlist),
                        content_type='text/html')


async def login_post(request):
    data = await request.post()
    username = data['username']
    password = data['password'].encode()
    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """SELECT Password_Hash, Salt, Work_Factor, EMPLOYEE.Is_Admin
                FROM USERS
                JOIN EMPLOYEE ON USERS.user_id=EMPLOYEE.user_id
                WHERE Username=%s""",
                username)
            if cur.rowcount == 0:
                return web.Response(
                    text=request.app['env']
                    .get_template('login.html')
                    .render(error_msg="Invalid username or password"),
                    content_type='text/html')
            password_hash, salt, work_factor, is_admin = await cur.fetchone()

    salt = salt.encode()
    password_hash = b64decode(password_hash)

    if password_hash == hash_pw(password, salt, work_factor):
        session_id, session_data = request.app['session'].new_session(request)
        session_data['admin'] = bool(is_admin)

        response = web.Response(text='''<html><head>
        <meta http-equiv="refresh" content="0; url=/" />
        </head></html>''', content_type='text/html')

        response.set_cookie('session_id', session_id,
                            secure=request.app['config']
                            ['avtory'].getboolean('secure_cookies'))
        return response
    else:
        return web.Response(
            text=request.app['env']
            .get_template('login.html')
            .render(error_msg="Invalid username or password"),
            content_type='text/html')


if __name__ == "__main__":
    parser = ArgumentParser("Add an administrator to the database")
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-l', '--lastname', required=True)
    parser.add_argument('-f', '--firstname', required=True)
    parser.add_argument('-e', '--email', required=True)
    parser.add_argument('-p', '--phonenumber', required=True)
    parser.add_argument('-r', '--role', required=True)

    args = vars(parser.parse_args())
    password = getpass().encode()
    config = read_config()
    loop = asyncio.get_event_loop()
    pool = create_pool(config.items('mysql'))

    try:
        loop.run_until_complete(
            insert_user(pool, args['username'], password, args['lastname'],
                        args['firstname'], args['email'], args['phonenumber'],
                        1, args['role']))
    finally:
        pool.close()
