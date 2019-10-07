#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

"""
    This file is part of Torrent Search.

    Torrent Search is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Torrent Search is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys

DOWNLOAD_TORRENT_STATUS_WAITING = 0
DOWNLOAD_TORRENT_STATUS_GETTING_LINK = 1
DOWNLOAD_TORRENT_STATUS_DOWNLOADING = 2
DOWNLOAD_TORRENT_STATUS_FINISHED = 3
DOWNLOAD_TORRENT_STATUS_FAILED = 4

LOGIN_STATUS_WAITING = 0
LOGIN_STATUS_OK = 1
LOGIN_STATUS_FAILED = 2

if os.getenv('APPDATA'):
    APPDATA_PATH = os.path.join(os.getenv('APPDATA'), "torrent-search")
else:
    APPDATA_PATH = os.path.join(os.getenv('HOME'), ".torrent-search")

if os.path.exists("/usr"):
    try:
        i = __file__.index("/lib/")
        DEFAULT_SHARE_PATH = __file__[:i]+'/share'
    except:
        DEFAULT_SHARE_PATH = "/usr/share"
    PLATFORM = "unix"
else:
    DEFAULT_SHARE_PATH = os.path.join(os.path.split(sys.argv[0])[0], "share")
    PLATFORM = "windows"

BUG_REPORT_PAGE = "http://sourceforge.net/tracker/?func=add&group_id=337561&atid=1414043"
FEATURE_REQUEST_PAGE = "http://sourceforge.net/tracker/?func=add&group_id=337561&atid=1414046"

AVAILABLE_LANGUAGES = [
    ('Deutsch', 'de'),
    ('English', 'en'),
    ('Français', 'fr'),
    ('Nederlands', 'nl'),
    ('Polski', 'pl'),
    ('Русский', 'ru'),
    ('Română', 'ro'),
    ('Svenska', 'sv'),
]
