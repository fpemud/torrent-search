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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gtk.keysyms
import webbrowser
from .constants import *


class HelpMenu(Gtk.MenuItem):
    def __init__(self, app):
        Gtk.MenuItem.__init__(self, _("HELP_MENU_LABEL"))
        menu = Gtk.Menu()
        self.set_submenu(menu)
        item = Gtk.ImageMenuItem(Gtk.STOCK_HELP)
        menu.add(item)
        item.connect('activate', lambda w: app.show_help())
        app.add_accelerator(
            item, "activate", Gtk.keysyms.F1, 0, Gtk.ACCEL_VISIBLE)
        item = Gtk.MenuItem(_("CONTACT"))
        menu.add(item)
        submenu = Gtk.Menu()
        item.set_submenu(submenu)
        item = Gtk.MenuItem(_("REPORT_BUG"))
        submenu.add(item)
        item.connect('activate', lambda w: webbrowser.open(BUG_REPORT_PAGE))
        item = Gtk.MenuItem(_("REQUEST_FEATURE"))
        submenu.add(item)
        item.connect('activate', lambda w: webbrowser.open(
            FEATURE_REQUEST_PAGE))
        item = Gtk.ImageMenuItem(Gtk.STOCK_ABOUT)
        menu.add(item)
        item.connect('activate', lambda w: app.show_about_dialog())


class FileMenu(Gtk.MenuItem):
    def __init__(self, app):
        Gtk.MenuItem.__init__(self, _("FILE_MENU_LABEL"))
        menu = Gtk.Menu()
        self.set_submenu(menu)
        item = Gtk.ImageMenuItem(Gtk.STOCK_QUIT)
        menu.add(item)
        item.connect('activate', lambda w: app.quit())
        app.add_accelerator(item, "activate", ord(
            'q'), Gtk.gdk.CONTROL_MASK, Gtk.ACCEL_VISIBLE)


class EditMenu(Gtk.MenuItem):
    def __init__(self, app):
        Gtk.MenuItem.__init__(self, _("EDIT_MENU_LABEL"))
        menu = Gtk.Menu()
        self.set_submenu(menu)
        item = Gtk.ImageMenuItem(Gtk.STOCK_PREFERENCES)
        menu.add(item)
        item.connect('activate', lambda w: app.show_preferences_dialog())
        app.add_accelerator(item, "activate", ord(
            'p'), Gtk.gdk.CONTROL_MASK, Gtk.ACCEL_VISIBLE)
