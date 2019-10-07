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

try:
    import dbus
    import dbus.service
    import dbus.glib
    DBUS_SUPPORT = True
except:
    DBUS_SUPPORT = False

if DBUS_SUPPORT:
    class DbusControler(dbus.service.Object):
        def __init__(self, app, *args):
            dbus.service.Object.__init__(self, *args)
            self.app = app

        @dbus.service.method('org.freedesktop.TorrentSearchIFace', in_signature='s')
        def run_search(self, pattern):
            self.app.ext_run_search(pattern)
            return True


def init_dbus():
    try:
        bus = dbus.SessionBus()
    except:
        print("Warning: Could not initiate dbus !")
        bus = None
    return bus


def try_dbus_connection(bus, search_pattern):
    try:
        proxy_obj = bus.get_object('org.freedesktop.TorrentSearch', '/org/freedesktop/TorrentSearchObject')
        iface = dbus.Interface(proxy_obj, 'org.freedesktop.TorrentSearchIFace')
        iface.run_search(search_pattern)
        return True
    except:
        return False


def open_dbus_controller(bus, app):
    try:
        bus_name = dbus.service.BusName('org.freedesktop.TorrentSearch', bus)
        dbusControler = DbusControler(app, bus_name, '/org/freedesktop/TorrentSearchObject')
    except:
        pass
