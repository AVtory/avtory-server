#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import secrets
import time
from aiohttp import web


class SimpleSessionManager:
    def __init__(self, timeout=45, period=5):
        self.sessions = {}
        self.timeout = timeout
        self.cleanup = asyncio.ensure_future(self.clean_expired(period))

    async def logout(self, session_id):
        try:
            del self.sessions[session_id]
        # If a user is trying to log out, we don't actually care if they have
        # a valid session.
        except KeyError:
            pass

    async def clean_expired(self, period):
        while True:
            await asyncio.sleep(period * 60)

            now = time.time()
            self.sessions = {
                session_id: session_data
                for session_id, session_data
                in self.sessions.items()
                if now < 60 * self.timeout + session_data['active']
            }

    def new_session(self, request):
        session_id = secrets.token_urlsafe(32)
        while session_id in self.sessions:
            session_id = secrets.token_urlsafe(32)
        session_data = {'active': time.time()}
        self.sessions[session_id] = session_data
        return session_id, session_data

    def get_session(self, request, admin_required=False):
        if ('session_id' in request.cookies and
                request.cookies['session_id'] in self.sessions):
            session_id = request.cookies['session_id']
            session_data = self.sessions[session_id]
            session_data['active'] = time.time()

            if (admin_required and (
                    'admin' not in session_data
                    or not session_data['admin'])):
                raise web.HTTPForbidden()

            return session_id, session_data
        else:
            # user is logged out. This exception will propogate all the way
            # back to the router, redirecting the user to the login page.
            raise web.HTTPFound('/login')
