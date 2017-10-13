#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio


class SimpleSessionManager:
    def __init__(self, timeout=45, period=5):
        self.sessions = {}
        self.timeout = timeout

        self.task = asyncio.ensure_future(self.clean_expired_sessions(period))

    async def clean_expired_sessions(self, period):
        while True:
            await asyncio.sleep(period)

            self.sessions = {session_id: session_data
                             for session_id, session_data
                             in self.sessions.items()
                             # if <session is not expired>
                             }

    def __getitem__(self, session_id):
        return self.sessions[session_id]

    def __setitem__(self, session_id, session_data):
        self[session_id] = session_data
