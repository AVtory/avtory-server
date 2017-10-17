#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
from hashlib import pbkdf2_hmac
from base64 import b64decode


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

    if password_hash == pbkdf2_hmac('sha256', password,
                                    salt, 1 << work_factor, dklen=64):
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
