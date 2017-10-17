#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import secrets
from aiohttp import web
from hashlib import pbkdf2_hmac
from base64 import b64encode


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
        password_hash = pbkdf2_hmac('sha256',
                                    password,
                                    salt,
                                    1 << 15,
                                    dklen=64)
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
