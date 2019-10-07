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


class PluginException(Exception):
    def __init__(self, mesg):
        Exception.__init__(self, mesg)
        self._mesg = mesg

    def handle(self):
        sys.stderr.write(self._mesg+"\n")


class PluginFileNotFound(PluginException):
    def __init__(self, metafile):
        try:
            PluginException.__init__(
                self, _("PLUGIN_FILE_NOT_FOUND") % metafile)
        except:
            PluginException.__init__(self, _("PLUGIN_FILE_NOT_FOUND"))


class PluginFileNotFile(PluginException):
    def __init__(self, metafile):
        try:
            PluginException.__init__(
                self, _("PLUGIN_FILE_NOT_FILE") % metafile)
        except:
            PluginException.__init__(self, _("PLUGIN_FILE_NOT_FILE"))


class PluginFileNotReadable(PluginException):
    def __init__(self, metafile):
        try:
            PluginException.__init__(
                self, _("PLUGIN_FILE_NOT_READABLE") % metafile)
        except:
            PluginException.__init__(self, _("PLUGIN_FILE_NOT_READABLE"))


class IncorrectPluginMetaFile(PluginException):
    def __init__(self, filename, msg):
        PluginException.__init__(self, filename+": "+msg)


class PluginSyntaxError(PluginException):
    def __init__(self, filename):
        PluginException.__init__(self, filename+": "+_("SYNTAX_ERROR"))
