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
import logging
import libxml2
import threading
import urllib.error
import urllib.parse
import urllib.request
import selenium
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from gi.repository import Gtk
import constants
import exceptions
import htmltools


class Plugin(object):

    def __init__(self, app, path, param):
        self.param = param
        if "max_results_loaded" not in self.param:
            self.param["max_results_loaded"] = None
        if "debug" not in self.param:
            self.param["debug"] = False

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
            metadata["require_selenium"] = False
            child = root.children
            while child:
                if child.name == "require_auth":
                    metadata["require_auth"] = (child.getContent() == "true")
                elif child.name == "require_selenium":
                    metadata["require_selenium"] = (child.getContent() == "true")
                elif child.type == "element":
                    metadata[child.name] = child.getContent()
                child = child.next

        # plugin properties
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
        self.WEBSITE_URL = metadata["website_url"]

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
            self._obj = plugin_class()

        # static variables
        self._app = app                                                 # FIXME
        self._require_auth = metadata["require_auth"]
        self._require_selenium = metadata["require_selenium"]

        # logger
        self._logger = logging.getLogger(self.ID)

        # login status
        self._credential = None
        self._login_status = None
        self._login_cookie = None

        # search status
        self._search_status = None
        self._search_param = None

        # search results total count
        self._results_total_count_lock = threading.Lock()
        self._results_total_count = None
        self._results_total_count_changed = None

        # loaded search result
        self._results_tmp_queue_lock = threading.Lock()
        self._results_tmp_queue = None

        # loaded result total count
        self._results_loaded = None     # only used in working thread, no lock needed

    @property
    def require_auth(self):
        return self._require_auth

    @property
    def login_status(self):
        return self._login_status

    @property
    def login_cookie(self):
        return self._login_cookie

    @property
    def search_status(self):
        return self._search_status

    # FIXME should notify to application, like one result
    @property
    def results_total_count(self):
        self._results_total_count_lock.acquire()
        try:
            return self._results_total_count
        finally:
            self._results_total_count_lock.release()

    def set_credential(self, credential):
        assert self._require_auth
        assert self._login_status is None
        self._credential = credential

    def search(self, pattern):
        # initialize variables
        self._login_status = constants.LOGIN_STATUS_WAITING
        self._login_cookie = None
        self._search_status = constants.SEARCH_STATUS_WORKING
        self._results_total_count = 0
        self._results_total_count_changed = False
        self._results_tmp_queue = []
        self._results_loaded = 0

        # create working thread
        threading.Thread(target=self._do_search, args=(pattern,)).start()
        GObject.timeout_add(200, self._check_results)

    def stop(self):
        if self._search_status != constants.SEARCH_STATUS_WORKING:
            return
        self._search_status = constants.SEARCH_STATUS_STOPPING

    def _do_search(self, pattern):
        try:
            # initialize search param
            self._search_param = dict()
            if self._require_selenium:
                options = selenium.webdriver.firefox.options.Options()
                if self.param["debug"]:
                    options.add_argument('--headless')
                self._search_param["selenium-driver"] = selenium.webdriver.Firefox(options=options)
            self._search_param["log"] = self.__log
            self._search_param["get-credential"] = self.__get_credential
            self._search_param["get-login-cookie"] = self.__get_login_cookie
            self._search_param["is-stopping"] = self.__is_stopping
            self._search_param["notify-results-total-count"] = self.__notify_results_total_count
            self._search_param["notify-one-result"] = self.__notify_one_result

            # FIXME
            self._search_param["find-elements"] = htmltools.find_elements
            self._search_param["parse-cookie"] = htmltools.parse_cookie

            # do login
            if self._require_auth:
                if self._credential is None:
                    self._login_status = constants.LOGIN_STATUS_FAILED
                    self._search_status = constants.SEARCH_STATUS_FAILED
                    return
                self._login_cookie = self._obj.try_login(self._search_param)
                while self._login_cookie is None:
                    self._login_status = constants.LOGIN_STATUS_FAILED
                    self._search_status = constants.SEARCH_STATUS_FAILED
                    return
                self._login_status = constants.LOGIN_STATUS_OK

            # do search
            self._obj.run_search(self._search_param, pattern)

            # search finished
            self._search_status = constants.SEARCH_STATUS_OK
        except Exception as e:
            # search failed
            self._logger.error(str(e), exc_info=True, stack_info=True)
            self._search_status = constants.SEARCH_STATUS_FAILED

    def _check_results(self):
        # check login status
        if self._login_status == constants.LOGIN_STATUS_FAILED:
            self._app.notify_plugin_login_failed(self)

        # send result total count to application
        self._results_total_count_lock.acquire()
        try:
            if self._results_total_count_changed:
                # notify application
                self._results_total_count_changed = False
        finally:
            self._results_total_count_lock.release()

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
            if True:
                self._search_param["selenium-driver"].quit()
                self._search_param = None
            self._results_total_count = None
            self._results_total_count_changed = None
            self._results_tmp_queue = None
            self._results_loaded = None
            return False

        return True

    def __log(self, msg):
        self._logger.warn(msg)

    def __get_credential(self):
        assert self._require_auth
        return self._credential

    def __get_login_cookie(self):
        assert self._require_auth
        return self.parent._login_cookie

    def __is_stopping(self):
        return self._search_status == constants.SEARCH_STATUS_STOPPING

    def __notify_results_total_count(self, value):
        assert type(value) == int
        self._results_total_count_lock.acquire()
        try:
            self._results_total_count = value
            self._results_total_count_changed = True
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
        if self.param["max_results_loaded"] is not None and self._results_loaded >= self.param["max_results_loaded"]:
            self._search_status = constants.SEARCH_STATUS_STOPPING


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

