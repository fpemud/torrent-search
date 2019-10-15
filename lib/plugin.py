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
import imp
import libxml2
import threading
import urllib.error
import urllib.parse
import urllib.request
from gi.repository import GObject
from gi.repository import Gtk
import constants
import exceptions


class Plugin(object):

    def __init__(self, app, id, path, param):
        # get metadata.xml file
        metadata_file = os.path.join(path, "metadata.xml")
        if not os.path.exists(metadata_file):
            raise exceptions.PluginFileNotFound(metadata_file)
        if not os.path.isfile(metadata_file):
            raise exceptions.PluginFileNotFile(metadata_file)
        if not os.access(metadata_file, os.R_OK):
            raise exceptions.PluginFileNotReadable(metadata_file)

        # check metadata.xml file content
        tree = libxml2.parseFile(metadata_file)
        if True:
            dtd = libxml2.parseDTD(None, constants.PATH_PLUGIN_DTD_FILE)
            ctxt = libxml2.newValidCtxt()
            messages = []
            ctxt.setValidityErrorHandler(lambda item, msgs: msgs.append(item), None, messages)
            if tree.validateDtd(ctxt, dtd) != 1:
                msg = ""
                for i in messages:
                    msg += i
                raise exceptions.IncorrectPluginMetaFile(metadata_file, msg)

        # get metadata from metadata.xml file
        metadata = {}
        if True:
            root = tree.getRootElement()
            metadata["id"] = root.prop("id")
            metadata["version"] = root.prop("version")
            metadata["icon_url"] = None
            metadata["require_auth"] = False
            metadata["default_disable"] = False
            child = root.children
            while child:
                if child.name == "require_auth":
                    metadata["require_auth"] = (child.getContent() == "true")
                elif child.name == "default_disable":
                    metadata["default_disable"] = (child.getContent() == "true")
                elif child.type == "element":
                    metadata[child.name] = child.getContent()
                child = child.next

        # plugin properties
        if True:
            print(id)
            print(metadata["id"])
            assert id == metadata["id"]
            self.ID = metadata["id"]
        self.TITLE = metadata['title']
        self.VERSION = metadata["version"]
        self.AUTHOR = metadata["author"]
        self.RELEASED_TIME = metadata["released_time"]
        self.ICON_URL = metadata["icon_url"]
        if True:
            fn = os.path.join(path, "icon.png")
            if os.path.exists(fn):
                self.ICON_FILENAME = fn                         # FIXME: should move to ICON_URL, like file://
            else:
                self.ICON_FILENAME = None
        self.WEBSITE_URL = metadata["WEBSITE_URL"]
        self.require_auth = metadata["require_auth"]            # FIXME
        self.default_disable = metadata["default_disable"]      # FIXME

        # create real plugin object
        self._obj = None
        if True:
            filename = os.path.join(path, metadata["filename"])
            if not os.path.exists(filename):
                raise exceptions.PluginFileNotFound(filename)
            if not os.path.isfile(filename):
                raise exceptions.PluginFileNotFile(filename)
            if not os.access(filename, os.R_OK):
                raise exceptions.PluginFileNotReadable(filename)

            plugin_class = None
            try:
                f = open(filename)
                m = imp.load_module(metadata["filename"][:-3], f, filename, ('.py', 'r', imp.PY_SOURCE))
                plugin_class = getattr(m, metadata["classname"])
            except:
                raise exceptions.PluginSyntaxError(filename)
            self._obj = plugin_class(_PluginApi(self))

        # static variables
        self._app = app                                                 # FIXME
        self._credential = param.get("credential", None)
        self._max_results_loaded = param.get("max_results_loaded", None)

        # status variables
        self._login_status = None
        self._login_cookie = None
        self._search_status = None

        # search results total count
        self._results_total_count_lock = threading.Lock()
        self._results_total_count = None

        # loaded search result
        self._results_tmp_queue_lock = threading.Lock()
        self._results_tmp_queue = None

        # loaded result total count
        self._results_loaded = None     # only used in working thread, no lock needed

    @property
    def login_status(self):
        return self._login_status

    @property
    def login_cookie(self):
        return self._login_cookie

    @property
    def search_status(self):
        return self._search_status

    # FIXME should notify to application, like 
    @property
    def results_total_count(self):
        self._results_total_count_lock.acquire()
        try:
            return self._results_total_count
        finally:
            self._results_total_count_lock.release()

    def search(self, pattern):
        # initialize variables
        self._login_status = constants.LOGIN_STATUS_WAITING
        self._login_cookie = None
        self._search_status = constants.SEARCH_STATUS_WORKING
        self._results_total_count = 0
        self._results_tmp_queue = []
        self._results_loaded = 0

        # create working thread
        threading.Thread(target=self._do_search, kwargs=(pattern,)).start()
        GObject.timeout_add(200, self._check_results)

    def stop(self):
        if self._search_status != constants.SEARCH_STATUS_WORKING:
            return
        self._search_status = constants.SEARCH_STATUS_STOPPING

    def _do_search(self, pattern):
        try:
            if self.require_auth:
                self._login_cookie = self._obj.try_login()
                if self._login_cookie is None:
                    self._login_status = constants.LOGIN_STATUS_FAILED
                    self._search_status = constants.SEARCH_STATUS_FAILED
                    return
            self._login_status = constants.LOGIN_STATUS_OK

            param = {
                "notify-results-total-count": self.__notify_results_total_count,
                "notify-one-result": self.__notify_one_result,
            }
            self._obj.run_search(pattern, param)

            self._search_status = constants.SEARCH_STATUS_OK
        except:
            self._search_status = constants.SEARCH_STATUS_FAILED

    def _check_results(self):
        # check login status
        if self._login_status == constants.LOGIN_STATUS_FAILED:
            self._app.notify_plugin_login_failed(self)

        # send all results in temporary queue to application
        self._results_tmp_queue_lock.acquire()
        try:
            while len(self._results_tmp_queue):
                item = self._results_tmp_queue[0]
                item.plugin = self
                item.category = self._app.categories[item.category]
                del self._results_tmp_queue[0]
                self._app.add_result(self, item)
        finally:
            self._results_tmp_queue_lock.release()

        # search finished?
        if self._search_status in [constants.SEARCH_STATUS_OK, constants.SEARCH_STATUS_FAILED]:
            self._app.notify_search_finished(self)
            self._login_status = None
            self._login_cookie = None
            self._search_status = None
            self._results_total_count = None
            self._results_tmp_queue = None
            self._results_loaded = None
            return False

        return True

    def __notify_results_total_count(self, value):
        assert type(value) == int
        self._results_total_count_lock.acquire()
        try:
            self._results_total_count = value
        finally:
            self._results_total_count_lock.release()

    def __notify_one_result(self, result):
        # create result object from dict data
        result = _PluginResult(result)

        # add result to temp list
        self._results_tmp_queue_lock.acquire()
        try:
            self._results_tmp_queue.append(result)
        finally:
            self._results_tmp_queue_lock.release()

        # check if we have enough results
        self._results_loaded += 1
        if self._max_results_loaded is not None and self._results_loaded >= self._max_results_loaded:
            self._search_status = constants.SEARCH_STATUS_STOPPING

# FIXME
class _PluginApi:

    def __init__(self, parent):
        self.parent = parent

    def http_queue_request(self, uri, method='GET', body=None, headers=None, redirections=5, connection_type=None):
        return self.parent._app.http_queue_request(uri, method, body, headers, redirections, connection_type)

    def get_credential(self):
        assert self.parent.require_auth
        return self.parent._credential

    def get_login_cookie(self):
        return self.parent._login_cookie

    def find_elements(self, node, elname=None, maxdepth=-1, **params):
        res = []
        if elname is None or node.name == elname:
            add = True
            for i in params:
                if node.prop(i) != params[i]:
                    add = False
                    break
            if add:
                res.append(node)
        if maxdepth != 0:
            child = node.children
            while child:
                res += self.find_elements(child, elname, maxdepth-1, **params)
                child = child.next
        return res

    # FIXME
    @property
    def stop_search(self):
        return self.parent._search_status == constants.SEARCH_STATUS_STOPPING


class _PluginResult(object):

    def __init__(self, plugin, data):
        self.plugin = plugin

        # basic properties
        self.id = data["id"]
        self.label = data["label"]
        self.date = data["date"]
        self.size = data["size"]
        self.seeders = data.get("seeders", -1)
        self.leechers = data.get("leechers", -1)
        self.category = data.get("category", "")
        self.orig_url = data.get("orig_url", "")
        self.link = data.get("link", "")
        self.rate = data.get("rate", None)
        self.nb_comments = data.get("nb_comments", 0)       # FIXME

        # comments
        self._comments_loaded_lock = threading.Lock()
        self._comments_loaded = False
        self._comments = []

        self._comments_loading_progress_lock = threading.Lock()
        self._comments_loading_progress = None

        if "comments" in data:
            for item in data["comments"]:
                self.comments.append(_PluginResultComment(item))
        self._comments_loaded = True

        # filelist
        self._filelist_loaded_lock = threading.Lock()
        self._filelist_loaded = False
        self._filelist = []

        if "filelist" in data:
            for item in data["filelist"]:
                self.filelist.append(item)
        self._filelist_loaded = True

        # poster
        self._poster_lock = threading.Lock()
        self._poster_loaded = False
        self._poster = None

        # poster pixmap
        self._poster_pix_lock = threading.Lock()
        self._poster_pix_loaded = False
        self._poster_pix = None

        # magnet link
        self.magnet_link = None
        if "magnet_link" in data:
            self.magnet_link = data["magnet_link"].lower()
            if "&" in self.magnet_link:
                i = self.magnet_link.index("&")
                self.magnet_link = self.magnet_link[:i]
        elif "hashvalue" in data:
            self.magnet_link = "magnet:?xt=urn:btih:" + data["hashvalue"].lower()

    def load_comments(self):
        threading.Thread(self._load_comments, ()).start()

    def _load_comments(self):
        # do work
        res = []
        if hasattr(self.plugin._obj, "load_comments"):
            param = {
                "notify-progress": self.__notify_comments_loading_progress,
            }
            res = self.plugin._obj.load_comments(self.id, param)

        # assign value with lock
        self._comments_lock.acquire()
        try:
            self._comments = []
            for item in res:
                self._comments.append(_PluginResultComment(item))
            self._comments_loaded = True
        finally:
            self._comments_lock.release()

    def __notify_comments_loading_progress(self, value):
        self._comments_loading_progress_lock.acquire()
        try:
            self._comments_loading_progress = value
        finally:
            self._comments_loading_progress_lock.release()

    def load_filelist(self):
        threading.Thread(self._load_filelist, ()).start()

    def _load_filelist(self):
        # do work
        res = []
        if hasattr(self.plugin._obj, "load_filelist"):
            res = self.plugin._obj.load_filelist(self.id)

        # assign value with lock
        self._filelist_lock.acquire()
        try:
            self._filelist = []
            for item in res:
                self._filelist.append(_PluginResultFile(item))
            self._filelist_loaded = True
        finally:
            self._filelist_lock.release()

    def load_poster(self):
        threading.Thread(self._load_poster, ()).start()

    def _load_poster(self):
        # do work
        res = None
        if hasattr(self.plugin._obj, "load_poster"):
            res = self.plugin._obj.load_poster(self.id)

        # assign value with lock
        self._poster_lock.acquire()
        try:
            self._poster = res
            self._poster_loaded = True
        finally:
            self._poster_lock.release()

    def load_poster_pix(self):
        threading.Thread(self._load_poster_pix, ()).start()

    def _load_poster_pix(self):
        # do work
        res = None
        if self._poster:
            try:
                filename, msg = urllib.request.urlretrieve(self._poster)
#            res = Gtk.Image.new_from_file_at_size(filename, 300, 300)
                res = Gtk.Image.new_from_file(filename)
                os.unlink(filename)
            except:
                res = None

        # assign value with lock
        self._poster_pix_lock.acquire()
        try:
            self._poster_pix = res
            self._poster_pix_loaded = True
        finally:
            self._poster_pix_lock.release()

    @property
    def comments(self):
        self._comments_lock.acquire()
        try:
            return self._comments
        finally:
            self._comments_lock.release()

    @property
    def comments_loading_progress(self):
        self._comments_loading_progress_lock.acquire()
        try:
            return self._comments_loading_progress
        finally:
            self._comments_loading_progress_lock.release()

    @property
    def comments_loaded(self):
        self._comments_lock.acquire()
        try:
            return self._comments_loaded
        finally:
            self._comments_lock.release()

    @property
    def filelist(self):
        self._filelist_lock.acquire()
        try:
            return self._filelist
        finally:
            self._filelist_lock.release()

    @property
    def filelist_loaded(self):
        self._filelist_lock.acquire()
        try:
            return self._filelist_loaded
        finally:
            self._filelist_lock.release()

    @property
    def poster(self):
        self._poster_lock.acquire()
        try:
            return self._poster
        finally:
            self._poster_lock.release()

    @property
    def poster_loaded(self):
        self._poster_lock.acquire()
        try:
            return self._poster_loaded
        finally:
            self._poster_lock.release()

    @property
    def poster_fix(self):
        self._poster_pix_lock.acquire()
        try:
            return self._poster_pix
        finally:
            self._poster_pix_lock.release()

    @property
    def poster_pix_loaded(self):
        self._poster_pix_lock.acquire()
        try:
            return self._poster_pix_loaded
        finally:
            self._poster_pix_lock.release()


class _PluginResultComment:

    def __init__(self, data):
        self.content = data["content"]
        self.date = data.get("comment_date", None)
        self.user_name = data.get("user_name", "")
        self.user_url = data.get("user_url", "")


class _PluginResultFile:

    def __init__(self, data):
        self.filename = data["filename"]
        self.size = int(data["size"])           # in bytes










# plugin template

# def try_login(self):
#     # implemented by plugin
#     assert False
#
# def run_search(self, pattern, notify_results_total_count, notify_one_result):
#     # implemented by plugin
#     assert False
#
# def load_comments(self, result_id, notify_progress):
#     # implemented by plugin
#     assert False
#
# def load_filelist(self, result_id):
#     # implemented by plugin
#     assert False
#
# def load_poster(self, result_id):
#     # implemented by plugin
#     assert False
#
# def load_poster_pix(self, result_id):
#     # implemented by plugin
#     assert False
#



# {
#     "label": "xxxxx",
#     "title": "xxxx",
#     "comments": "xxxx",
#     "torrent_url": "XXXX",  # torrent file download url
#     "magnet_link": "XXXX",  # magnet link url
#     "date": "2010-01-01",
#     "size": 100,            # in bytes
#     "seeders": 10,          # how many seeders (optional)
#     "leechers": 10,         # how many leechers (optional)
#     "hash": XXX,            # optional
# }

#there should be at least one of torrent_url or magnet_link

