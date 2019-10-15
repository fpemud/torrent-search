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
from gi.repository import GObject
import _thread
import http.client
import urllib.request
import urllib.parse
import urllib.error
import torrentApps
import os
import gzip
from constants import *


class DownloadItem(object):
    def __init__(self, search_result):
        self.status_lock = threading.Lock()        # FIXME
        self._item = search_result
        self.title = search_result.label
        self._status = DOWNLOAD_TORRENT_STATUS_WAITING
        self.plugin = search_result.plugin

    def get_link(self):
        return self._item.link

    def _get_status(self):
        self.status_lock.acquire()
        res = self._status
        self.status_lock.release()
        return res

    def _set_status(self, value):
        self.status_lock.acquire()
        self._status = value
        self.status_lock.release()
    status = property(_get_status, _set_status)

    def _get_status_label(self):
        labels = [_("WAITING"), _("GETTING_LINK"), _(
            "DOWNLOADING"), _("FINISHED"), _("FAILED")]
        return labels[self.status]
    status_label = property(_get_status_label)


class DownloadManager(Gtk.VBox):
    def __init__(self, app):
        Gtk.VBox.__init__(self)
        self.set_size_request(app.config["download_manager_width"], 1)
        self.connect("size_allocate", self.on_size_allocate)
        self._app = app
        scw = Gtk.ScrolledWindow()
        self.pack_start(scw, False, False, 0)
        scw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.tv = Gtk.TreeView()
        self.tv.connect('button_press_event', self.on_tv_button_press_event)
        scw.add(self.tv)
        self.lb = Gtk.ListStore(object, int)
        self.tv.set_model(self.lb)
        r = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("TITLE"), r)
        col.set_cell_data_func(r, self.title_data_func)
        self.tv.append_column(col)
        col = Gtk.TreeViewColumn(_("STATUS"))
        self.tv.append_column(col)
        r = Gtk.CellRendererText()
        col.pack_start(r, False)
        col.set_cell_data_func(r, self.status_data_func)
        r = Gtk.CellRendererText()
        col.pack_start(r, False)
        r = Gtk.CellRendererText()
        col.pack_start(r, False)
        GObject.timeout_add(50, self._check)

    def on_size_allocate(self, widget, rect):
        self._app.config["download_manager_width"] = rect.width

    def remove_at_path(self, path):
        del self.lb[path[0]]

    def redo_at_path(self, path):
        self.lb[path[0]][0].status = DOWNLOAD_TORRENT_STATUS_WAITING

    def show_help(self):
        item = self._app.get_help_item(self)
        self._app.show_help(item)

    def on_tv_button_press_event(self, widget, event):
        if event.button == 3:
            m = Gtk.Menu()
            data = widget.get_path_at_pos(int(event.x), int(event.y))
            if data:
                path, column, x, y = data
                item = self.lb.get_value(self.lb.get_iter(path), 0)
                if item.status == DOWNLOAD_TORRENT_STATUS_FAILED:
                    i = Gtk.ImageMenuItem(Gtk.STOCK_REMOVE)
                    m.add(i)
                    i.connect("activate", lambda w,
                              p: self.remove_at_path(p), path)
                    i = Gtk.ImageMenuItem(_("RETRY_MENU_ITEM"))
                    img = Gtk.Image()
                    img.set_from_stock(Gtk.STOCK_REDO, Gtk.ICON_SIZE_MENU)
                    i.set_image(img)
                    m.add(i)
                    i.connect("activate", lambda w,
                              p: self.redo_at_path(p), path)
                if item.status == DOWNLOAD_TORRENT_STATUS_WAITING:
                    i = Gtk.ImageMenuItem(Gtk.STOCK_CANCEL)
                    m.add(i)
                    i.connect('activate', lambda w,
                              p: self.cancel_at_path(p), path)
            if m.get_children():
                m.add(Gtk.SeparatorMenuItem())
            i = Gtk.ImageMenuItem(_("RETRY_ALL_FAILED"))
            img = Gtk.Image()
            img.set_from_stock(Gtk.STOCK_REDO, Gtk.ICON_SIZE_MENU)
            i.set_image(img)
            i.connect('activate', lambda w: self.retry_all())
            m.add(i)
            i = Gtk.ImageMenuItem(_("CANCEL_ALL_FAILED"))
            img = Gtk.Image()
            img.set_from_stock(Gtk.STOCK_CANCEL, Gtk.ICON_SIZE_MENU)
            i.set_image(img)
            i.connect('activate', lambda w: self.cancel_all_failed())
            m.add(i)
            i = Gtk.ImageMenuItem(_("CANCEL_ALL"))
            img = Gtk.Image()
            img.set_from_stock(Gtk.STOCK_CANCEL, Gtk.ICON_SIZE_MENU)
            i.set_image(img)
            i.connect('activate', lambda w: self.cancel_all())
            m.add(i)
            m.add(Gtk.SeparatorMenuItem())
            i = Gtk.ImageMenuItem(Gtk.STOCK_HELP)
            m.add(i)
            i.connect('activate', lambda w: self.show_help())
            m.show_all()
            m.popup(None, None, None, 3, event.time)

    def cancel_all(self):
        i = 0
        while i < len(self.lb):
            item = self.lb[i][0]
            if item.status in [DOWNLOAD_TORRENT_STATUS_WAITING, DOWNLOAD_TORRENT_STATUS_FAILED]:
                del self.lb[i]
            else:
                i += 1

    def retry_all(self):
        for i in self.lb:
            if i[0].status == DOWNLOAD_TORRENT_STATUS_FAILED:
                i[0].status = DOWNLOAD_TORRENT_STATUS_WAITING

    def cancel_all_failed(self):
        i = 0
        while i < len(self.lb):
            item = self.lb[i][0]
            if item.status == DOWNLOAD_TORRENT_STATUS_FAILED:
                del self.lb[i]
            else:
                i += 1

    def cancel_at_path(self, path):
        item = self.lb[path[0]][0]
        if item.status == DOWNLOAD_TORRENT_STATUS_WAITING:
            del self.lb[path[0]]

    def _check(self):
        i = 0
        while i < len(self.lb):
            if self.lb[i][0].status == DOWNLOAD_TORRENT_STATUS_FINISHED:
                del self.lb[i]
            else:
                i += 1
        if self.downloading < max(1, self._app.config["max_sim_downloads"]):
            for i in self.lb:
                if i[0].status == DOWNLOAD_TORRENT_STATUS_WAITING:
                    self.start_download(i[0])
                    break
        for i in range(len(self.lb)):
            self.lb[i][1] = self.lb[i][0].status
        return True

    def start_download(self, item):
        _thread.start_new_thread(self._download_item, (item,))       # FIXME

    def _download_item(self, item):
        try:
            self._do_download(item)
        except:
            item.status = DOWNLOAD_TORRENT_STATUS_FAILED

    def _do_download(self, item, url=None, cookie=None, init_url=None, retry=0):
        # TODO: Handle download by magnet link
        if url is None:
            item.status = DOWNLOAD_TORRENT_STATUS_GETTING_LINK
            try:
                url = item.get_link()
            except:
                item.status = DOWNLOAD_TORRENT_STATUS_FAILED
                return
            init_url = url
            item.status = DOWNLOAD_TORRENT_STATUS_DOWNLOADING
        utype, path = urllib.parse.splittype(url)
        host, path = urllib.parse.splithost(path)
        c = http.client.HTTPConnection(host)
        if item.plugin.require_auth and not cookie:
            cookie = self._app.parse_cookie(item.plugin.login_cookie)
        headers = {'User-Agent': 'torrent-search'}
        if cookie:
            headers['Cookie'] = cookie
        c.request('GET', path, headers=headers)
        resp = c.getresponse()
        redirect_url = None
        content_type = None
        remote_filename = None
        content_encoding = None
        for key, value in resp.getheaders():
            if key == "set-cookie":
                cookie = self._app.parse_cookie(value)
            if key == "location":
                redirect_url = value
            if key == "content-type":
                content_type = value
            if key == "content-encoding":
                content_encoding = value
            if key == "content-disposition":
                if 'filename="' in value:
                    i = value.index('filename="')+10
                    value = value[i:]
                    i = value.index('"')
                    remote_filename = value[:i]
        if redirect_url:
            c.close()
            return self._do_download(item, redirect_url, cookie, init_url)
        if content_type.split(';')[0] == "text/html":
            c.close()
            if retry < 1:
                return self._do_download(item, init_url, cookie, init_url, retry+1)
            else:
                item.status = DOWNLOAD_TORRENT_STATUS_FAILED
                return
        if resp.status != 200:
            c.close()
            self.status = DOWNLOAD_TORRENT_STATUS_FAILED
            return
        else:
            if self._app.config["torrent_mode"] == "save_in_folder":
                if remote_filename:
                    basename = remote_filename
                else:
                    basename = url
                    while "/" in basename:
                        i = basename.index("/")
                        basename = basename[i+1:]
                filename = os.path.join(
                    self._app.config["torrent_save_folder"], basename)
                f = open(filename, "wb")
                f.write(resp.read())
                f.close()
                c.close()
                if content_encoding == "gzip":
                    f = gzip.open(filename)
                    data = f.read()
                    f.close()
                    f = open(filename, "wb")
                    f.write(data)
                    f.close()
                item.status = DOWNLOAD_TORRENT_STATUS_FINISHED
            else:
                fd, filename = self._app.get_tempfile()
                os.write(fd, resp.read())
                os.close(fd)
                if content_encoding == "gzip":
                    f = gzip.open(filename)
                    data = f.read()
                    f.close()
                    f = open(filename, "wb")
                    f.write(data)
                    f.close()
                item.status = DOWNLOAD_TORRENT_STATUS_FINISHED
                command = None
                if self._app.config["torrent_mode"] == "use_standard_app":
                    selAppID = self._app.config["torrent_standard_app"]
                    for appID, label, com in torrentApps.listApps():
                        if appID == selAppID:
                            command = com
                else:
                    command = self._app.config["torrent_custom_app"]
                if command is None:
                    return
                file_param = False
                for i in ["%f", "%F", "%u", "%U"]:
                    if i in command:
                        file_param = True
                        break
                try:
                    caption = desktop_data[1]
                except:
                    caption = _("NO_TITLE")
                command = command.replace("%f", filename).replace("%F", filename).replace(
                    "%u", "file://"+filename).replace("%U", "file://"+filename).replace("%c", caption).replace("%i", "")
                if not file_param:
                    command += ' "%s"' % filename
                self._run_command(item, command)
            c.close()

    def _run_command(self, item, command):
        words = []
        i = 0
        ws = 0
        while i < len(command):
            if command[i] in ['"', "'"]:
                j = command[i+1:].index(command[i])+i+1
                words.append(command[i+1:j])
                i = j+1
                ws = i
            elif command[i] == " ":
                words.append(command[ws:i])
                i += 1
                ws = i
            else:
                i += 1
        words.append(command[ws:])
        i = 0
        while i < len(words):
            if words[i]:
                i += 1
            else:
                del words[i]
        try:
            if os.fork() == 0:
                os.execvp(words[0], ("",)+tuple(words[1:]))
        except:
            os.spawnv(os.P_NOWAIT, words[0], tuple(words[1:])+tuple(words[1:]))

    def _get_downloading(self):
        res = 0
        for i in self.lb:
            if i[0].status in [DOWNLOAD_TORRENT_STATUS_GETTING_LINK, DOWNLOAD_TORRENT_STATUS_DOWNLOADING]:
                res += 1
        return res
    downloading = property(_get_downloading)

    def status_data_func(self, col, cell, model, iter):
        item = model.get_value(iter, 0)
        cell.set_property('text', item.status_label)
        if item.status == DOWNLOAD_TORRENT_STATUS_FAILED:
            color = "#FF0000"
        elif item.status in [DOWNLOAD_TORRENT_STATUS_GETTING_LINK, DOWNLOAD_TORRENT_STATUS_DOWNLOADING]:
            color = "#00FF00"
        else:
            color = "#FFFFFF"
        cell.set_property("background", color)

    def title_data_func(self, col, cell, model, iter):
        item = model.get_value(iter, 0)
        cell.set_property("text", item.title)
        if item.status == DOWNLOAD_TORRENT_STATUS_FAILED:
            color = "#FF0000"
        elif item.status in [DOWNLOAD_TORRENT_STATUS_GETTING_LINK, DOWNLOAD_TORRENT_STATUS_DOWNLOADING]:
            color = "#00FF00"
        else:
            color = "#FFFFFF"
        cell.set_property("background", color)

    def append(self, search_result):
        self.lb.append([DownloadItem(search_result),
                        DOWNLOAD_TORRENT_STATUS_WAITING])
