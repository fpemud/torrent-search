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
import httplib2
import time
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GObject
import _thread
import constants
import informations


class PluginsUpdatesChecker(Gtk.Dialog):

    def __init__(self, app):
        self._app = app
        self.plugins_list_lock = _thread.allocate_lock()    # FIXME
        self.status_lock = _thread.allocate_lock()    # FIXME
        self.submesg_lock = _thread.allocate_lock()    # FIXME
        self.progress_lock = _thread.allocate_lock()    # FIXME
        self.submesg = ""
        self.progress = None
        self._status = 0
        Gtk.Dialog.__init__(self, _("CHECKING_PLUGIN_UPDATES"), app)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.set_deletable(False)
        self.set_border_width(0)
        self.connect('key_press_event', self.on_key_press_event)
        vbox = Gtk.VBox()
        self.add(vbox)
        vbox.set_border_width(5)
        vbox.set_spacing(10)
        self.main_mesg = Gtk.Label()
        self.main_mesg.set_width_chars(50)
        self.main_mesg.set_alignment(0, 0.5)
        vbox.pack_start(self.main_mesg, False, False, 0)
        self.pb = Gtk.ProgressBar()
        vbox.pack_start(self.pb, False, False, 0)
        self.sub_mesg = Gtk.Label()
        self.sub_mesg.set_alignment(0, 0.5)
        vbox.pack_start(self.sub_mesg, False, False, 0)
        self.cancel_button = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        self.cancel_button.connect('clicked', lambda w: self.cancel())
        self.action_area.pack_start(self.cancel_button, False, False, 0)

    def cancel(self):
        self.status = -2
        self.response(Gtk.ResponseType.CANCEL)

    def _get_submesg(self):
        self.submesg_lock.acquire()
        res = self._submesg
        self.submesg_lock.release()
        return res

    def _set_submesg(self, value):
        self.submesg_lock.acquire()
        self._submesg = value
        self.submesg_lock.release()
    submesg = property(_get_submesg, _set_submesg)

    def _get_progress(self):
        self.progress_lock.acquire()
        res = self._progress
        self.progress_lock.release()
        return res

    def _set_progress(self, value):
        self.progress_lock.acquire()
        self._progress = value
        self.progress_lock.release()
    progress = property(_get_progress, _set_progress)

    def _get_status(self):
        self.status_lock.acquire()
        res = self._status
        self.status_lock.release()
        return res

    def _set_status(self, value):
        self.status_lock.acquire()
        if self._status >= 0:
            self._status = value
        self.status_lock.release()
    status = property(_get_status, _set_status)

    def _get_plugins_list(self):
        self.plugins_list_lock.acquire()
        res = self._plugins_list
        self.plugins_list_lock.release()
        return res

    def _set_plugins_list(self, value):
        self.plugins_list_lock.acquire()
        self._plugins_list = value
        self.plugins_list_lock.release()
    plugins_list = property(_get_plugins_list, _set_plugins_list)

    def on_key_press_event(self, widget, event):
        if event.keyval == 65307:
            return True

    def check_status(self):
        if self.progress is None:
            self.pb.pulse()
        else:
            self.pb.set_fraction(self.progress)
        if self.status == 1:
            self.set_main_mesg(_("CHECKING_PLUGINS_VERSIONS"))
        if self.status == 2:
            self.set_main_mesg(_("DOWNLOADING_PLUGINS_UPDATES"))
            self.set_sub_mesg(self.submesg)
        if self.status == 3:
            self.pb.set_fraction(1)
            self.set_main_mesg(_("DONE"))
            self.set_sub_mesg("")
            self.cancel_button.set_sensitive(False)
            GObject.timeout_add_seconds(1, self.response, Gtk.ResponseType.CLOSE)
            return False
        if self.status == 4:
            self.pb.set_fraction(1)
            self.set_main_mesg(_("DONE"))
            self.set_sub_mesg("")
            self.response(Gtk.ResponseType.CLOSE)
            return False
        if self.status == -1:
            self.pb.set_fraction(1)
            self.set_main_mesg(_("FAILED"))
            self.set_sub_mesg("")
            self.cancel_button.set_sensitive(False)
            GObject.timeout_add_seconds(1, self.response, Gtk.ResponseType.CLOSE)
            return False
        if self.status == -2:
            return False
        return True

    def set_main_mesg(self, mesg):
        self.main_mesg.set_markup("<span size='large'><b>%s</b></span>" % mesg)

    def set_sub_mesg(self, mesg):
        self.sub_mesg.set_text(mesg)

    def check_versions(self):
        to_download = []
        for i in self.plugins_list:
            must_download = True
            itime = time.strptime(i["released_time"], "%Y-%m-%d %H:%M:%S")
            for j in self._app.search_plugins:
                if j.ID == i["id"]:
                    jtime = time.strptime(j.RELEASED_TIME, "%Y-%m-%d %H:%M:%S")
                    if jtime >= itime:
                        must_download = False
            if must_download:
                to_download.append(i)
        if to_download:
            self.status = 2
            self.download_updates(to_download)
        else:
            self.status = 3

    def download_updates(self, to_download):
        c = httplib2.Http()
        n = len(to_download)
        p = 0.
        downloaded = 0
        for i in to_download:
            if self.status <= 0:
                break
            try:
                self.submesg = i["title"]
                url = i["download_url"]
                resp, content = c.request(url)
                if resp.status == 200:
                    path = os.path.join(constants.APPDATA_PATH, "search-plugins", i["id"])
                    if not os.path.exists(path):
                        self._app.rec_mkdir(path)
                    metafile = os.path.join(path, "metadata.xml")
                    codefile = os.path.join(path, i["filename"])
                    f = open(codefile, "w")
                    f.write(content)
                    f.close()
                    tree = libxml2.newDoc("1.0")
                    root = libxml2.newNode("plugin")
                    tree.setRootElement(root)
                    root.setProp("id", i["id"])
                    root.setProp("version", i["version"])
                    for j in ["title", "released_time", "author", "filename", "classname", "download_url", "website_url", "icon_url", "require_auth", "default_disable"]:
                        if j in i:
                            root.newTextChild(None, j, i[j])
                    tree.saveFormatFileEnc(metafile, "utf-8", True)
                    downloaded += 1
            except:
                pass
            p += 1
            self.progress = p/n
        if downloaded:
            self.status = 4
        else:
            self.status = 3

    def parse_plugin(self, node):
        res = {}
        res["id"] = node.prop('id')
        res["version"] = node.prop('version')
        child = node.children
        while child:
            if child.type == "element":
                res[child.name] = child.getContent()
            child = child.__next__           # FIXME
        return res

    def parse_list(self, tree):
        root = tree.getRootElement()
        res = []
        child = root.children
        while child:
            if child.name == "plugin":
                res.append(self.parse_plugin(child))
            child = child.__next__           # FIXME
        return res

    def retrieve_list(self, threaded=False):
        if not threaded:
            _thread.start_new_thread(self.retrieve_list, (True,))    # FIXME
            return

        try:
            c = httplib2.Http()
            resp, content = c.request("http://torrent-search.sourceforge.net/plugins-db/" + informations.VERSION)
            if resp.status == 200:
                tree = libxml2.parseDoc(content)
                self.plugins_list = self.parse_list(tree)
                self.status = 1
                if self.status >= 0:
                    self.check_versions()
            else:
                self.status = -1
        except:
            self.status = -1

    def run(self):
        self.status = 0
        self.show_all()
        self.pulse_timer = GObject.timeout_add(50, self.check_status)
        self.set_main_mesg(_("GETTING_PLUGINS_LIST"))
        self.retrieve_list()
        Gtk.Dialog.run(self)
        self.destroy()
        GObject.source_remove(self.pulse_timer)
        return self.status == 4
