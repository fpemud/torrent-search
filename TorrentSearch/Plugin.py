#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import urllib.error
import urllib.parse
import urllib.request
import time
import httplib2
import imp
import libxml2
import os
import _thread
from .constants import *
from .informations import *
from .exceptions import *
from gi.repository import GObject
from gi.repository import Gtk
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
            GObject.timeout_add_seconds(
                1, self.response, Gtk.ResponseType.CLOSE)
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
            GObject.timeout_add_seconds(
                1, self.response, Gtk.ResponseType.CLOSE)
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
                    path = os.path.join(
                        APPDATA_PATH, "search-plugins", i["id"])
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
            resp, content = c.request("http://torrent-search.sourceforge.net/plugins-db/" + VERSION)
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
    poster_pix_loaded = property(
        _get_poster_pix_loaded, _set_poster_pix_loaded)

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

    def _get_icon(self):
        return self.plugin.icon
    icon = property(_get_icon)

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

    def _set_icon_url(self, url):
        if url:
            _thread.start_new_thread(self._try_load_icon, (url,))    # FIXME
            GObject.timeout_add(100, self._watch_load_icon)
    icon_url = property(None, _set_icon_url)

    def _watch_load_icon(self):
        self.icon_lock.acquire()
        res = not hasattr(self, "_icon")
        self.icon_lock.release()
        if not res:
            self._app.notify_plugin_icon(self)
        return res

    def _try_load_icon(self, url):
        try:
            filename, msg = urllib.request.urlretrieve(url)
#         self.icon=Gtk.gdk.pixbuf_new_from_file_at_size(filename,16,16)
            self.icon = Gtk.Image_new_from_file(filename)
            os.unlink(filename)
        except:
            self.icon = None

    def _get_icon(self):
        self.icon_lock.acquire()
        if hasattr(self, '_icon'):
            res = self._icon
        else:
            res = None
        self.icon_lock.release()
        return res

    def _set_icon(self, value):
        self.icon_lock.acquire()
        self._icon = value
        self.icon_lock.release()
    icon = property(_get_icon, _set_icon)

    def _get_enabled(self):
        return  self.ID not in self._app.config["disabled_plugins"]

    def _set_enabled(self, value):
        l = self._app.config["disabled_plugins"]
        if value:
            while self.ID in l:
                i = l.index(self.ID)
                del l[i]
        else:
            l.append(self.ID)
        self._app.config["disabled_plugins"] = l
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

    def download(self, link):
        self._app.download(link)

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
                if self.login_cookie == None:
                    self.login_cookie = self._try_login()
                if self.login_cookie == None:
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
    dtd = libxml2.parseDTD(None, os.path.join(
        app.options.share_dir, UNIXNAME, "dtds", "torrent-search-plugin.dtd"))
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
        raise PluginFileNotFound(metadata_file)
    if not os.path.isfile(metadata_file):
        raise PluginFileNotFile(metadata_file)
    if not os.access(metadata_file, os.R_OK):
        raise PluginFileNotReadable(metadata_file)
    metadata = parse_metadata(app, metadata_file)
    filename = os.path.join(path, metadata["filename"])
    if not os.path.exists(filename):
        raise PluginFileNotFound(filename)
    if not os.path.isfile(filename):
        raise PluginFileNotFile(filename)
    if not os.access(filename, os.R_OK):
        raise PluginFileNotReadable(filename)
    try:
        f = open(filename)
        m = imp.load_module(metadata["filename"][:-3],
                            f, filename, ('.py', 'r', imp.PY_SOURCE))
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
        return res
    except:
        raise PluginSyntaxError(filename)
