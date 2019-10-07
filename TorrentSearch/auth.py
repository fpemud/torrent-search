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

import libxml2
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os
from .constants import *


class AuthDialog(Gtk.Dialog):

    def __init__(self, app):
        Gtk.Dialog.__init__(self, _("AUTHENTICATION"), app)
        self.add_button(Gtk.STOCK_OK, Gtk.RESPONSE_OK)
        self.add_button(Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL)
        vbox = Gtk.VBox()
        vbox.set_border_width(5)
        vbox.set_spacing(10)
        self.child.add(vbox)
        hbox = Gtk.HBox()
        hbox.set_spacing(10)
        vbox.pack_start(hbox, False, False)
        img = Gtk.Image()
        img.set_from_stock(Gtk.STOCK_DIALOG_AUTHENTICATION, Gtk.ICON_SIZE_DIALOG)
        hbox.pack_start(img, False, False)
        table = Gtk.Table()
        table.set_col_spacings(10)
        table.set_row_spacings(10)
        hbox.pack_start(table)
        self.mesg_label = Gtk.Label()
        self.mesg_label.set_alignment(0, 0.5)
        table.attach(self.mesg_label, 0, 2, 0, 1, yoptions=0)
        l = Gtk.Label(_("USERNAME"))
        l.set_alignment(0, 0.5)
        table.attach(l, 0, 1, 1, 2, xoptions=Gtk.FILL, yoptions=0)
        self.username = Gtk.Entry()
        table.attach(self.username, 1, 2, 1, 2, yoptions=0)
        l = Gtk.Label(_("PASSWORD"))
        l.set_alignment(0, 0.5)
        table.attach(l, 0, 1, 2, 3, xoptions=Gtk.FILL, yoptions=0)
        self.password = Gtk.Entry()
        table.attach(self.password, 1, 2, 2, 3, yoptions=0)
        self.password.set_visibility(False)
        self.remember = Gtk.CheckButton(_("REMEMBER_AUTH"))
        vbox.pack_start(self.remember, False, False)
        self.username.connect("activate", lambda w: self.password.grab_focus())
        self.password.connect("activate", lambda w: self.response(Gtk.RESPONSE_OK))

    def run(self, plugin, failed=False):
        self.username.set_text("")
        self.password.set_text("")
        if failed:
            self.mesg_label.set_markup("<span color='#FF0000'><b>%s</b></span>" % (_("AUTH_FAILED_FOR_PLUGIN") % plugin.TITLE))
        else:
            self.mesg_label.set_markup("<b>%s</b>" % (_("AUTH_REQUIRED_FOR_PLUGIN") % plugin.TITLE))
        self.username.grab_focus()
        self.show_all()
        if Gtk.Dialog.run(self) == Gtk.RESPONSE_OK:
            res = self.username.get_text(), self.password.get_text(), self.remember.get_active()
        else:
            res = None
        self.hide()
        return res


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
        if not os.path.exists(APPDATA_PATH):
            self._app.rec_mkdir(APPDATA_PATH)
        filename = os.path.join(APPDATA_PATH, "auth.xml")
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
            child = child.__next__                # FIXME
        self._auths[plugin] = (username, password)

    def _load(self):
        try:
            filename = os.path.join(APPDATA_PATH, "auth.xml")
            d = libxml2.parseFile(filename)
            root = d.getRootElement()
            child = root.children
            while child:
                if child.name == "auth":
                    self._load_auth(child)
                child = child.__next__             # FIXME
        except:
            pass
