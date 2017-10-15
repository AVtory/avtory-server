#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import secrets
import time


class SimpleSessionManager:
    def __init__(self, timeout=45, period=5):
        self.sessions = {}
        self.timeout = timeout
        self.cleanup = asyncio.ensure_future(self.clean_expired(period))

    async def clean_expired(self, period):
        while True:
            await asyncio.sleep(period)

            now = time.time()
            self.sessions = {
                session_id: session_data
                for session_id, session_data
                in self.sessions.items()
                if now - session_data['active'] > 60 * self.timeout
            }

    async def __getitem__(self, request):
        if ('session_id' in request.cookies and
                request.cookies['session_id'] in self.sessions):
            session_id = request.cookies['session_id']
            session_data = self.sessions[session_id]
            session_data['active'] = time.time()

            return session_id, self.sessions[session_id]
        else:
            session_id = secrets.token_urlsafe(32)
            while session_id in self.sessions:
                session_id = secrets.token_urlsafe(32)
            session_data = {'active': time.time()}
            self.sessions[session_id] = session_data
            return session_id, session_data
