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
import libxml2
import constants


class AuthMemory(object):
    def __init__(self, app):
        self._app = app
        self._auths = {}
        self._load()

    def __iter__(self):
        return iter(self._auths)

    def __setitem__(self, key, value):
        self._auths[key] = value
        self._save()

    def __getitem__(self, key):
        return self._auths[key]

    def __delitem__(self, plugin_id):
        if plugin_id in self._auths:
            del self._auths[plugin_id]
            self._save()

    def _save(self):
        d = libxml2.newDoc("1.0")
        root = libxml2.newNode("torrent-search-auth")
        d.setRootElement(root)
        for plugin in self._auths:
            username, password = self._auths[plugin]
            node = libxml2.newNode("auth")
            root.addChild(node)
            node.setProp('plugin', plugin)
            node.newTextChild(None, 'username', username)
            node.newTextChild(None, 'password', password)
        if not os.path.exists(constants.APPDATA_PATH):
            self._app.rec_mkdir(constants.APPDATA_PATH)
        filename = os.path.join(constants.APPDATA_PATH, "auth.xml")
        d.saveFormatFileEnc(filename, "utf-8", True)

    def _load_auth(self, node):
        username = ""
        password = ""
        plugin = node.prop('plugin')
        child = node.children
        while child:
            if child.name == "username":
                username = child.content
            if child.name == "password":
                password = child.content
            child = child.next
        self._auths[plugin] = (username, password)

    def _load(self):
        try:
            filename = os.path.join(constants.APPDATA_PATH, "auth.xml")
            d = libxml2.parseFile(filename)
            root = d.getRootElement()
            child = root.children
            while child:
                if child.name == "auth":
                    self._load_auth(child)
                child = child.next
        except:
            pass
