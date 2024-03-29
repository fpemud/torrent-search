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
import webbrowser
import informations


class MainMenu(Gtk.MenuBar):
    def __init__(self, app):
        Gtk.MenuBar.__init__(self)
        self.add(FileMenu(app))
        self.add(EditMenu(app))
        self.add(HelpMenu(app))


class HelpMenu(Gtk.MenuItem):
    def __init__(self, app):
        Gtk.MenuItem.__init__(self, _("HELP_MENU_LABEL"))
        menu = Gtk.Menu()
        self.set_submenu(menu)
        item = Gtk.ImageMenuItem(Gtk.STOCK_HELP)
        menu.add(item)
        item.connect('activate', lambda w: app.show_help())
        key, mod = Gtk.accelerator_parse("F1")
        app.add_accelerator(item, "activate", key, mod, Gtk.AccelFlags.VISIBLE)
        item = Gtk.MenuItem(_("CONTACT"))
        menu.add(item)
        submenu = Gtk.Menu()
        item.set_submenu(submenu)
        item = Gtk.MenuItem(_("REPORT_BUG"))
        submenu.add(item)
        item.connect('activate', lambda w: webbrowser.open(informations.BUG_REPORT_PAGE))
        item = Gtk.MenuItem(_("REQUEST_FEATURE"))
        submenu.add(item)
        item.connect('activate', lambda w: webbrowser.open(informations.FEATURE_REQUEST_PAGE))
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
        key, mod = Gtk.accelerator_parse("<Control>Q")
        app.add_accelerator(item, "activate", key, mod, Gtk.AccelFlags.VISIBLE)


class EditMenu(Gtk.MenuItem):
    def __init__(self, app):
        Gtk.MenuItem.__init__(self, _("EDIT_MENU_LABEL"))
        menu = Gtk.Menu()
        self.set_submenu(menu)
        item = Gtk.ImageMenuItem(Gtk.STOCK_PREFERENCES)
        menu.add(item)
        item.connect('activate', lambda w: app.show_preferences_dialog())
        key, mod = Gtk.accelerator_parse("<Control>P")
        app.add_accelerator(item, "activate", key, mod, Gtk.AccelFlags.VISIBLE)
