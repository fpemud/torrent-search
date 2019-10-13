#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import urllib.error
import urllib.parse
import urllib.request
import time
import imp
import libxml2
import os
from gi.repository import GObject
from gi.repository import Gtk
import _thread
from constants import *
from informations import *
import exceptions

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

from constants import *


class TorrentResultComment(object):
    def __init__(self, content, comment_date=None, user_name="", user_url=""):
        self.content = content
        self.date = comment_date
        self.user_name = user_name
        self.user_url = user_url


class CommentsList(list):
    pass


class FileList(list):
    def append(self, filename, size):
        list.append(self, (filename, size))


class PluginResult(object):

    def __init__(self, label, date, size, seeders=-1, leechers=-1, magnet_link=None, hashvalue=None, category="", nb_comments=0, orig_url=""):
        self.size = size
        self.label = label
        self.date = date
        self.seeders = seeders
        self.leechers = leechers
        self.category = category
        self.nb_comments = nb_comments
        self._comments_loaded = False
        self._filelist_loaded = False
        self._poster_loaded = False
        self._poster_pix_loaded = False
        self.comments_loaded_lock = _thread.allocate_lock()    # FIXME
        self.filelist_loaded_lock = _thread.allocate_lock()    # FIXME
        self.poster_loaded_lock = _thread.allocate_lock()    # FIXME
        self.poster_pix_loaded_lock = _thread.allocate_lock()    # FIXME
        self.comments_loading_progress_lock = _thread.allocate_lock()    # FIXME
        self._comments_loading_progress = 0
        if magnet_link:
            self.magnet_link = magnet_link.lower()
            if "&" in self.magnet_link:
                i = self.magnet_link.index("&")
                self.magnet_link = self.magnet_link[:i]
        elif hashvalue:
            self.magnet_link = "magnet:?xt=urn:btih:"+hashvalue.lower()
        else:
            self.magnet_link = None
        self.orig_url = orig_url

    def load_poster_pix(self):
        _thread.start_new_thread(self._do_load_poster_pix, ())    # FIXME

    def _do_load_poster_pix(self):
        res = None
        if self.poster:
            try:
                filename, msg = urllib.request.urlretrieve(self.poster)
#            res = Gtk.Image.new_from_file_at_size(filename, 300, 300)
                res = Gtk.Image.new_from_file(filename)
                os.unlink(filename)
            except:
                res = None
        self.poster_pix = res
        self.poster_pix_loaded = True

    def _get_comments_loading_progress(self):
        self.comments_loading_progress_lock.acquire()
        res = self._comments_loading_progress
        self.comments_loading_progress_lock.release()
        return res

    def _set_comments_loading_progress(self, value):
        self.comments_loading_progress_lock.acquire()
        self._comments_loading_progress = value
        self.comments_loading_progress_lock.release()
    comments_loading_progress = property(
        _get_comments_loading_progress, _set_comments_loading_progress)

    def _get_comments_loaded(self):
        self.comments_loaded_lock.acquire()
        res = self._comments_loaded
        self.comments_loaded_lock.release()
        return res

    def _set_comments_loaded(self, value):
        self.comments_loaded_lock.acquire()
        self._comments_loaded = value
        self.comments_loaded_lock.release()
    comments_loaded = property(_get_comments_loaded, _set_comments_loaded)

    def _get_filelist_loaded(self):
        self.filelist_loaded_lock.acquire()
        res = self._filelist_loaded
        self.filelist_loaded_lock.release()
        return res

    def _set_filelist_loaded(self, value):
        self.filelist_loaded_lock.acquire()
        self._filelist_loaded = value
        self.filelist_loaded_lock.release()
    filelist_loaded = property(_get_filelist_loaded, _set_filelist_loaded)

    def _get_poster_loaded(self):
        self.poster_loaded_lock.acquire()
        res = self._poster_loaded
        self.poster_loaded_lock.release()
        return res

    def _set_poster_loaded(self, value):
        self.poster_loaded_lock.acquire()
        self._poster_loaded = value
        self.poster_loaded_lock.release()
    poster_loaded = property(_get_poster_loaded, _set_poster_loaded)

    def _get_poster_pix_loaded(self):
        self.poster_pix_loaded_lock.acquire()
        res = self._poster_pix_loaded
        self.poster_pix_loaded_lock.release()
        return res

    def _set_poster_pix_loaded(self, value):
        self.poster_pix_loaded_lock.acquire()
        self._poster_pix_loaded = value
        self.poster_pix_loaded_lock.release()
    poster_pix_loaded = property(_get_poster_pix_loaded, _set_poster_pix_loaded)

    def load_comments(self):
        _thread.start_new_thread(self._load_comments, ())    # FIXME

    def _load_comments(self):
        try:
            self.comments = self._do_load_comments()
        except:
            self.comments = CommentsList()
        self.comments_loaded = True

    def _do_load_comments(self):
        return CommentsList()

    def load_filelist(self):
        _thread.start_new_thread(self._load_filelist, ())    # FIXME

    def _load_filelist(self):
        try:
            self.filelist = self._do_load_filelist()
        except:
            self.filelist = FileList()
        self.filelist_loaded = True

    def _do_load_filelist(self):
        return FileList()

    def load_poster(self):
        _thread.start_new_thread(self._load_poster, ())    # FIXME

    def _load_poster(self):
        try:
            self.poster = self._do_load_poster()
        except:
            self.poster = None
        self.poster_loaded = True

    def _do_load_poster(self):
        return None

    def _get_poster(self):
        if not hasattr(self, "_poster"):
            self._poster = self._do_get_poster()
        return self._poster

    def _get_link(self):
        if not hasattr(self, "_link"):
            self._link = self._do_get_link()
        return self._link
    link = property(_get_link)

    # def _get_icon(self):
    #     return self.plugin.icon
    # icon = property(_get_icon)

    def _get_rate(self):
        if not hasattr(self, "_rate"):
            self._rate = self._load_rate()
        return self._rate
    rate = property(_get_rate)

    def _load_rate(self):
        return 0


class ResultsList(object):
    def __init__(self):
        self._list = []
        self._lock = _thread.allocate_lock()    # FIXME

    def append(self, item):
        self._lock.acquire()
        self._list.append(item)
        self._lock.release()

    def __getitem__(self, index):
        self._lock.acquire()
        res = self._list[index]
        self._lock.release()
        return res

    def __setitem__(self, index, value):
        self._lock.acquire()
        self._list[index] = value
        self._lock.release()

    def __delitem__(self, index):
        self._lock.acquire()
        del self._list[index]
        self._lock.release()

    def __iter__(self):
        self._lock.acquire()
        res = iter(self._list)
        self._lock.release()
        return res

    def __len__(self):
        self._lock.acquire()
        res = len(self._list)
        self._lock.release()
        return res


class Plugin(object):
    TITLE = "No title"
    AUTHOR = ""
    RELEASED_TIME = ""

    def __init__(self, app):
        self._app = app
        self.search_finished_lock = _thread.allocate_lock()    # FIXME
        self.stop_search_lock = _thread.allocate_lock()    # FIXME
        self.results_count_lock = _thread.allocate_lock()    # FIXME
        self.icon_lock = _thread.allocate_lock()    # FIXME
        self.credentials_lock = _thread.allocate_lock()    # FIXME
        self.login_cookie_lock = _thread.allocate_lock()    # FIXME
        self.login_status_lock = _thread.allocate_lock()    # FIXME
        self._login_cookie = None
        self._credentials = None
        self._search_finished = True
        self._stop_search = False
        self._results_count = -1
        self._icon_url = None
        self.results_loaded = 0

    def http_queue_request(self, uri, method='GET', body=None, headers=None, redirections=5, connection_type=None):
        return self._app.http_queue_request(uri, method, body, headers, redirections, connection_type)

    def _get_login_cookie(self):
        self.login_cookie_lock.acquire()
        res = self._login_cookie
        self.login_cookie_lock.release()
        return res

    def _set_login_cookie(self, value):
        self.login_cookie_lock.acquire()
        self._login_cookie = value
        self.login_cookie_lock.release()

    login_cookie = property(_get_login_cookie, _set_login_cookie)

    def _get_credentials(self):
        self.credentials_lock.acquire()
        res = self._credentials
        self.credentials_lock.release()
        return res

    def _set_credentials(self, value):
        self.credentials_lock.acquire()
        self._credentials = value
        self.credentials_lock.release()

    credentials = property(_get_credentials, _set_credentials)

    # def _set_icon_url(self, url):
    #     if url:
    #         _thread.start_new_thread(self._try_load_icon, (url,))    # FIXME
    #         GObject.timeout_add(100, self._watch_load_icon)

    # icon_url = property(None, _set_icon_url)

    # def _watch_load_icon(self):
    #     self.icon_lock.acquire()
    #     res = not hasattr(self, "_icon")
    #     self.icon_lock.release()
    #     if not res:
    #         self._app.notify_plugin_icon(self)
    #     return res

#     def _try_load_icon(self, url):
#         try:
#             filename, msg = urllib.request.urlretrieve(url)
# #         self.icon=Gtk.gdk.pixbuf_new_from_file_at_size(filename,16,16)
#             self.icon = Gtk.Image_new_from_file(filename)
#             os.unlink(filename)
#         except:
#             self.icon = None

    # def _get_icon(self):
    #     self.icon_lock.acquire()
    #     if hasattr(self, '_icon'):
    #         res = self._icon
    #     else:
    #         res = None
    #     self.icon_lock.release()
    #     return res

    # def _set_icon(self, value):
    #     self.icon_lock.acquire()
    #     self._icon = value
    #     self.icon_lock.release()

    # icon = property(_get_icon, _set_icon)

    def _get_enabled(self):
        return self.ID not in self._app.config["disabled_plugins"]

    def _set_enabled(self, value):
        tl = self._app.config["disabled_plugins"]
        if value:
            while self.ID in tl:
                i = tl.index(self.ID)
                del tl[i]
        else:
            tl.append(self.ID)
        self._app.config["disabled_plugins"] = tl

    enabled = property(_get_enabled, _set_enabled)

    def _get_results_count(self):
        self.results_count_lock.acquire()
        res = self._results_count
        self.results_count_lock.release()
        return res

    def _set_results_count(self, value):
        self.results_count_lock.acquire()
        if type(value) == int:
            self._results_count = value
        self.results_count_lock.release()

    results_count = property(_get_results_count, _set_results_count)

    def stop(self):
        self.stop_search = True
        while not self.search_finished:
            time.sleep(0.1)
        while len(self.new_results):
            del self.new_results[0]

    def _get_search_finished(self):
        self.search_finished_lock.acquire()
        res = self._search_finished
        self.search_finished_lock.release()
        return res

    def _set_search_finished(self, value):
        self.search_finished_lock.acquire()
        self._search_finished = value
        self.search_finished_lock.release()

    search_finished = property(_get_search_finished, _set_search_finished)

    def _get_stop_search(self):
        self.stop_search_lock.acquire()
        res = self._stop_search
        self.stop_search_lock.release()
        return res

    def _set_stop_search(self, value):
        self.stop_search_lock.acquire()
        self._stop_search = value
        self.stop_search_lock.release()

    stop_search = property(_get_stop_search, _set_stop_search)

    def _get_login_status(self):
        self.login_status_lock.acquire()
        res = self._login_status
        self.login_status_lock.release()
        return res

    def _set_login_status(self, value):
        self.login_status_lock.acquire()
        self._login_status = value
        self.login_status_lock.release()

    login_status = property(_get_login_status, _set_login_status)

    def search(self, pattern):
        if not hasattr(self, "new_results"):
            self.new_results = ResultsList()
        while len(self.new_results):
            del self.new_results[0]
        self.search_finished = False
        self.stop_search = False
        self.results_count = -1
        self.results_loaded = 0
        self.login_status = LOGIN_STATUS_WAITING
        _thread.start_new_thread(self._do_search, (pattern,))    # FIXME
        GObject.timeout_add(200, self._check_results)
        GObject.timeout_add(50, self._check_login_status)

    def _check_login_status(self):
        if self.login_status == LOGIN_STATUS_WAITING:
            return True
        if self.login_status == LOGIN_STATUS_FAILED:
            self._app.notify_plugin_login_failed(self)
        return False

    def _check_results(self):
        while len(self.new_results):
            item = self.new_results[0]
            item.plugin = self
            item.category = self._app.categories[item.category]
            del self.new_results[0]
            self._app.add_result(self, item)
            del item
        if self.search_finished:
            self._app.notify_search_finished(self)
        return not self.search_finished

    def add_result(self, result):
        self.new_results.append(result)
        self.results_loaded += 1
        if self._app.config["stop_search_when_nb_plugin_results_reaches_enabled"] and self.results_loaded >= self._app.config["stop_search_when_nb_plugin_results_reaches_value"]:
            self.stop_search = True

    def _login_failed(self):
        self.login_status = LOGIN_STATUS_FAILED

    def _do_search(self, pattern):
        try:
            if self.require_auth:
                if self.login_cookie is None:
                    self.login_cookie = self._try_login()
                if self.login_cookie is None:
                    self._login_failed()
                    return
            self.login_status = LOGIN_STATUS_OK
            self._run_search(pattern)
        except:
            pass
        self.search_finished = True

    def _run_search(self, pattern):
        pass


def check_plugin_dtd(tree, dtd, filename):
    ctxt = libxml2.newValidCtxt()
    messages = []
    ctxt.setValidityErrorHandler(
        lambda item, msgs: msgs.append(item), None, messages)
    if tree.validateDtd(ctxt, dtd) != 1:
        msg = ""
        for i in messages:
            msg += i
        raise IncorrectPluginMetaFile(filename, msg)


def parse_metadata(app, filename):
    res = {}
    dtd = libxml2.parseDTD(None, os.path.join(DEFAULT_SHARE_DIR, APPID, "dtds", "torrent-search-plugin.dtd"))
    tree = libxml2.parseFile(filename)
    check_plugin_dtd(tree, dtd, filename)
    root = tree.getRootElement()
    res["id"] = root.prop("id")
    res["version"] = root.prop("version")
    res["icon_url"] = None
    res["require_auth"] = False
    res["default_disable"] = False
    child = root.children
    while child:
        if child.name == "require_auth":
            res["require_auth"] = (child.getContent() == "true")
        elif child.name == "default_disable":
            res["default_disable"] = (child.getContent() == "true")
        elif child.type == "element":
            res[child.name] = child.getContent()
        child = child.__next__    # FIXME
    return res


def load_plugin(app, path):
    metadata_file = os.path.join(path, "metadata.xml")
    if not os.path.exists(metadata_file):
        raise exceptions.PluginFileNotFound(metadata_file)
    if not os.path.isfile(metadata_file):
        raise exceptions.PluginFileNotFile(metadata_file)
    if not os.access(metadata_file, os.R_OK):
        raise exceptions.PluginFileNotReadable(metadata_file)
    metadata = parse_metadata(app, metadata_file)

    filename = os.path.join(path, metadata["filename"])
    if not os.path.exists(filename):
        raise exceptions.PluginFileNotFound(filename)
    if not os.path.isfile(filename):
        raise exceptions.PluginFileNotFile(filename)
    if not os.access(filename, os.R_OK):
        raise exceptions.PluginFileNotReadable(filename)
    try:
        f = open(filename)
        m = imp.load_module(metadata["filename"][:-3], f, filename, ('.py', 'r', imp.PY_SOURCE))
        plugin_class = getattr(m, metadata["classname"])
        res = plugin_class(app)
        res.TITLE = metadata['title']
        res.VERSION = metadata["version"]
        res.ID = metadata["id"]
        res.AUTHOR = metadata["author"]
        res.RELEASED_TIME = metadata["released_time"]
        res.icon_url = metadata["icon_url"]
        res.website_url = metadata["website_url"]
        res.require_auth = metadata["require_auth"]
        res.default_disable = metadata["default_disable"]

        icon_filename = os.path.join(constants.APPDATA_PATH, "search-plugins", res.ID, "icon.png")
        if os.path.exists(icon_filename):
            res.icon_filename = icon_filename
        else:
            res.icon_filename = None

        return res
    except:
        raise exceptions.PluginSyntaxError(filename)



