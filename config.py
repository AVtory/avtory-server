#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiomysql
from configparser import ConfigParser
from os.path import expanduser, join, split, abspath


def create_pool(config):
    loop = asyncio.get_event_loop()
    pool = loop.run_until_complete(aiomysql.create_pool(
        **{k: v for k, v in config}
    ))
    return pool


def read_config():
    config = ConfigParser()
    config.read(['/etc/avtory/avtory.conf',
                 expanduser('~/.config/avtory.conf'),
                 'avtory.conf',
                 join(split(abspath(__file__))[0], 'avtory.conf')])
    return config
