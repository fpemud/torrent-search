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
sys.path.append("/usr/lib64/torrent-search")
import lang
import plugin


class FakeApp:

    def __init__(self):
        self.categories = dict()

    def notify_plugin_login_failed(self, plugin):
        print("notify_plugin_login_failed", plugin.ID)

    def add_result(self, item):
        print("add_result", item)

    def notify_search_finished(self):
        print("notify_search_finished")


if len(sys.argv) < 3:
    print("syntax: test-plugin.py <plugin-directory> <search-pattern> [username] [password]")
    sys.exit(1)

pluginDir = sys.argv[1]
searchPattern = sys.argv[2]
pobj = plugin.Plugin(FakeApp(), pluginDir, {"debug": True})
if pobj.require_auth:
    if len(sys.argv) >= 5:
        pobj.set_credential(sys.argv[3], sys.argv[4])
pobj.search(searchPattern)
