#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import secrets
from aiohttp import web
from hashlib import pbkdf2_hmac
from base64 import b64encode, b64decode


def hash_pw(password, salt, work_factor):
    return pbkdf2_hmac('sha512', password, salt, 1 << work_factor, dklen=64)


async def create_user(request):
    session_id, session_data = (request
                                .app['session']
                                .get_session(request, True))
    data = await request.post()

    if len(data) > 0:
        username = data['username']
        password = data['password'].encode()
        name = data['name'] if data['name'] != "" else None
        email = data['email'] if data['email'] != "" else None
        admin = ('admin'
                 if 'admin' in data and data['admin'] == 'on'
                 else 'user')

        salt = secrets.token_urlsafe(32).encode()
        password_hash = hash_pw(password, salt, 15)
        password_hash = b64encode(password_hash)

        async with request.app['pool'].acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO users
                (username, email, realname, password_hash, salt, privs)
                VALUES (%s, %s, %s, %s, %s, %s)""",
                                  (username, email, name, password_hash,
                                   salt, admin))
            await conn.commit()

    return web.Response(text=request
                        .app['env']
                        .get_template('create_user.html')
                        .render(),
                        content_type='text/html')


async def login_get(request):
    return web.Response(text=request
                        .app['env']
                        .get_template('login.html')
                        .render(),
                        content_type='text/html')


async def login_post(request):
    data = await request.post()
    username = data['username']
    password = data['password'].encode()
    async with request.app['pool'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """SELECT password_hash, salt, work_factor, privs
                FROM users
                WHERE username=%s""",
                username)
            if cur.rowcount == 0:
                print("invalid login")
                raise web.HTTPFound('/login')
            password_hash, salt, work_factor, privs = await cur.fetchone()
            salt = salt.encode()
            password_hash = b64decode(password_hash)

    if password_hash == hash_pw(password, salt, work_factor):
        session_id, session_data = request.app['session'].new_session(request)
        session_data['privs'] = privs

        response = web.Response(text='''<html><head>
        <meta http-equiv="refresh" content="0; url=/" />
        </head></html>''', content_type='text/html')
        response.set_cookie('session_id', session_id)
        return response
    else:
        print("invalid login")
        raise web.HTTPFound('/login')
