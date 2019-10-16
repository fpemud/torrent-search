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
import constants


CONFIG_KEYS = {
    "torrent_mode": ("torrent_mode", "string", "save_in_folder"),
    "torrent_standard_app": ("torrent_standard_app", "string", ""),
    "torrent_custom_app": ("torrent_custom_app", "string", ""),
    "torrent_save_folder": ("torrent_save_folder", "string", os.getcwd()),
    "window_x": ("window_pos/x", "int", 100),
    "window_y": ("window_pos/y", "int", 100),
    "window_width": ("window_pos/width", "int", 640),
    "window_height": ("window_pos/height", "int", 480),
    "config_dialog_width": ("window_pos/config_dialog_width", "int", 1),
    "config_dialog_height": ("window_pos/config_dialog_height", "int", 400),
    "window_maximized": ("window_pos/maximized", "bool", False),
    "disabled_plugins": ("disabled_plugins", "string_list", []),
    "hide_zero_seeders": ("hide_zero_seeders", "bool", False),
    "min_size_enable": ("min_size_enable", "bool", False),
    "max_size_enable": ("max_size_enable", "bool", False),
    "min_size_value": ("min_size_value", "int", 50),
    "max_size_value": ("max_size_value", "int", 200),
    "min_size_unit": ("min_size_unit", "string", "MB"),
    "max_size_unit": ("max_size_unit", "string", "MB"),
    "only_exact_phrase": ("only_exact_phrase", "bool", False),
    "only_all_words": ("only_all_words", "bool", False),
    "name_does_not_contain": ("name_does_not_contain", "string", ""),
    "name_contains": ("name_contains", "string", ""),
    "download_manager_width": ("download_manager_width", "int", 450),
    "search_options_expanded": ("search_options_expanded", "bool", False),
    "max_sim_downloads": ("max_sim_downloads", "int", 3),
    "check_plugins_updates": ("check_plugins_updates", "bool", True),
    "filter_duplicates": ("filter_duplicates", "bool", False),
    "converted_from_gconf": ("converted_from_gconf", "bool", False),
    "after_date_enable": ("after_date_enable", "bool", False),
    "before_date_enable": ("before_date_enable", "bool", False),
    "after_date": ("after_date", "string", ""),
    "before_date": ("before_date", "string", ""),
    "category": ("category", "object", None),
    "stop_search_when_nb_results_reaches_enabled": ("stop_search_when_nb_results_reaches_enabled", "bool", False),
    "stop_search_when_nb_results_reaches_value": ("stop_search_when_nb_results_reaches_value", "int", 100),
    "stop_search_when_nb_plugin_results_reaches_enabled": ("stop_search_when_nb_plugin_results_reaches_enabled", "bool", True),
    "stop_search_when_nb_plugin_results_reaches_value": ("stop_search_when_nb_plugin_results_reaches_value", "int", 100),
    "sort_column": ("sort_column", "int", -1),
    "sort_desc": ("sort_desc", "bool", False),
}
# TODO1: Add option to limit the number of comments to load


class AppConfig(object):
    def __init__(self, app):
        self._app = app
        self._values = {}
        self._listeners = []
        for key in CONFIG_KEYS:
            real_key, keytype, default = CONFIG_KEYS[key]
            self._values[key] = default
        self._load()

    def _notify(self, key):
        for i in self._listeners:
            i(key, self[key])

    def register_listener(self, listener):
        self._listeners.append(listener)

    def __getitem__(self, key):
        return self._values[key]

    def __setitem__(self, key, value):
        real_key, keytype, default = CONFIG_KEYS[key]
        if value != self[key] or keytype == "string_list":
            self._values[key] = value
            self._save()
            self._notify(key)

    def __call__(self, key, value):
        self[key] = value

    def _save(self):
        d = libxml2.newDoc("1.0")
        root = libxml2.newNode("torrent-search-config")
        d.setRootElement(root)
        for key in CONFIG_KEYS:
            real_key, keytype, default = CONFIG_KEYS[key]
            if keytype == "string":
                root.newTextChild(None, key, self[key]).setProp('type', 'string')
            if keytype == "int":
                root.newTextChild(None, key, str(self[key])).setProp('type', 'int')
            if keytype == "bool":
                if self[key]:
                    root.newTextChild(None, key, "true").setProp('type', 'bool')
                else:
                    root.newTextChild(None, key, "false").setProp('type', 'bool')
            if keytype == "string_list":
                node = libxml2.newNode(key)
                node.setProp('type', 'string_list')
                root.addChild(node)
                for item in self[key]:
                    node.newTextChild(None, "item", item)
        if not os.path.exists(constants.APPDATA_PATH):
            self._app.rec_mkdir(constants.APPDATA_PATH)
        filename = os.path.join(constants.APPDATA_PATH, "config.xml")
        d.saveFormatFileEnc(filename, "utf-8", True)

    def _load(self):
        try:
            filename = os.path.join(constants.APPDATA_PATH, "config.xml")
            d = libxml2.parseFile(filename)
            root = d.getRootElement()
            child = root.children
            while child:
                if child.type == "element":
                    if child.prop('type') == "string":
                        self._values[child.name] = child.getContent().decode("utf-8")[0]
                    if child.prop('type') == "int":
                        self._values[child.name] = int(child.getContent())
                    if child.prop('type') == "bool":
                        self._values[child.name] = (
                            child.getContent() == "true")
                    if child.prop('type') == "string_list":
                        res = []
                        item = child.children
                        while item:
                            if item.name == "item":
                                res.append(item.getContent().decode("utf-8")[0])
                            item = item.__next__            # FIXME
                        self._values[child.name] = res
                child = child.__next__                      # FIXME
        except:
            pass
