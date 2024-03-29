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
import time
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import webbrowser
import torrentApps


class PreferencesDialog(Gtk.Dialog):
    def __init__(self, app):
        self._app = app
        Gtk.Dialog.__init__(self, _("PREFERENCES"), app)

        self.resize(app.config['config_dialog_width'],
                    app.config['config_dialog_height'])
        self._accel_group = Gtk.AccelGroup()
        self.add_accel_group(self._accel_group)
        self.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        self.help_button = Gtk.Button(stock=Gtk.STOCK_HELP)
        key, mod = Gtk.accelerator_parse("F1")
        self.help_button.add_accelerator("clicked", self._accel_group, key, mod, Gtk.AccelFlags.VISIBLE)
        self.action_area.add(self.help_button)
        self.action_area.set_child_secondary(self.help_button, True)
        self.set_icon_name("gtk-preferences")
        notebook = Gtk.Notebook()
        notebook.set_border_width(5)
        self.add(notebook)
        self.general_page = _GeneralPreferencesPage(app)
        notebook.append_page(self.general_page, Gtk.Label(_('GENERAL_OPTIONS')))
        notebook.append_page(_PluginsPreferencesPage(
            app), Gtk.Label(_('SEARCH_PLUGINS')))
        self.help_button.connect(
            "clicked", lambda w, n: self.show_help(n), notebook)
        self.connect('configure_event', self._on_configure_event)

    def _on_configure_event(self, window, event):
        self._app.config["config_dialog_width"] = event.width
        self._app.config["config_dialog_height"] = event.height

    def show_help(self, notebook):
        item = ["preferences-general",
                "preferences-plugins"][notebook.get_current_page()]
        self._app.show_help(item)

    def run(self):
        self.show_all()
        Gtk.Dialog.run(self)
        self._app.config['torrent_save_folder'] = self.general_page.torrent_save_in_folder_fs.get_filename()
        self.hide()


class _GeneralPreferencesPage(Gtk.VBox):

    def __init__(self, app):
        self._app = app
        Gtk.VBox.__init__(self)
        self.set_border_width(5)
        self.set_spacing(10)
        f = Gtk.Frame()
        l = Gtk.Label()
        l.set_markup("<b>%s</b>" % _("TORRENT_FILES"))
        f.set_label_widget(l)
        self.pack_start(f, False, False, 0)
        table = Gtk.Table()
        table.set_border_width(5)
        table.set_col_spacings(10)
        table.set_row_spacings(10)
        f.add(table)
        self.torrent_save_in_folder_rb = Gtk.RadioButton(None, _("SAVE_IN_FOLDER"))
        table.attach(self.torrent_save_in_folder_rb, 0, 1, 0, 1, xoptions=Gtk.AttachOptions.FILL, yoptions=0)
        self.torrent_save_in_folder_fs = Gtk.FileChooserButton(_("SELECT_FOLDER"))
        self.torrent_save_in_folder_fs.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        table.attach(self.torrent_save_in_folder_fs, 1, 2, 0, 1, yoptions=0)
        self.torrent_save_in_folder_fs.set_sensitive(False)
        self.torrent_use_standard_app_rb = Gtk.RadioButton(self.torrent_save_in_folder_rb, _("USE_STANDARD_APP"))
        table.attach(self.torrent_use_standard_app_rb, 0, 1, 1, 2, xoptions=Gtk.AttachOptions.FILL, yoptions=0)
        self.torrent_use_standard_app_cb = Gtk.ComboBox()
        table.attach(self.torrent_use_standard_app_cb, 1, 2, 1, 2, yoptions=0)
        self.torrent_use_standard_app_cb_ls = Gtk.ListStore(str, str)
        self.torrent_use_standard_app_cb.set_model(self.torrent_use_standard_app_cb_ls)
        r = Gtk.CellRendererText()
        self.torrent_use_standard_app_cb.pack_start(r, False)
        self.torrent_use_standard_app_cb.add_attribute(r, "text", 1)
        self.torrent_use_standard_app_cb.set_sensitive(False)
        for appID, label, command in torrentApps.listApps():
            self.torrent_use_standard_app_cb_ls.append([appID, label])
        for i in range(len(self.torrent_use_standard_app_cb_ls)):
            if self.torrent_use_standard_app_cb_ls[i][0] == app.config["torrent_standard_app"]:
                self.torrent_use_standard_app_cb.set_active(i)
        self.torrent_use_custom_app_rb = Gtk.RadioButton(
            self.torrent_save_in_folder_rb, _("USE_CUSTOM_APP"))
        table.attach(self.torrent_use_custom_app_rb, 0, 1,
                     2, 3, xoptions=Gtk.AttachOptions.FILL, yoptions=0)
        self.torrent_use_custom_app_entry = Gtk.Entry()
        table.attach(self.torrent_use_custom_app_entry, 1,
                     2, 2, 3, xoptions=Gtk.AttachOptions.FILL, yoptions=0)
        self.torrent_use_custom_app_entry.set_text(
            app.config['torrent_custom_app'])
        self.torrent_use_custom_app_entry.set_sensitive(False)
        if app.config["torrent_mode"] == "save_in_folder":
            self.torrent_save_in_folder_rb.set_active(True)
            self.torrent_save_in_folder_fs.set_sensitive(True)
        elif app.config["torrent_mode"] == "use_standard_app":
            self.torrent_use_standard_app_rb.set_active(True)
            self.torrent_use_standard_app_cb.set_sensitive(True)
        else:
            self.torrent_use_custom_app_rb.set_active(True)
            self.torrent_use_custom_app_entry.set_sensitive(True)
        for i in [self.torrent_save_in_folder_rb, self.torrent_use_standard_app_rb, self.torrent_use_custom_app_rb]:
            i.connect('toggled', self.on_torrent_mode_changed)
        self.torrent_use_standard_app_cb.connect(
            'changed', self.on_torrent_standard_app_changed)
        self.torrent_use_custom_app_entry.connect(
            'changed', self.on_torrent_custom_app_changed)
        if os.path.exists(app.config['torrent_save_folder']) and os.path.isdir(app.config['torrent_save_folder']):
            self.torrent_save_in_folder_fs.set_current_folder(app.config['torrent_save_folder'])
        else:
            self.torrent_save_in_folder_fs.set_current_folder(os.getenv('HOME'))
            app.config['torrent_save_folder'] = os.getenv('HOME')
        f = Gtk.Frame()
        l = Gtk.Label()
        l.set_markup("<b>%s</b>" % _("PLUGINS_UPDATES"))
        f.set_label_widget(l)
        self.pack_start(f, False, False, 0)
        vbox = Gtk.VBox()
        f.add(vbox)
        vbox.set_border_width(5)
        vbox.set_spacing(10)
        b = Gtk.Button(_("CHECK_NOW"))
        img = Gtk.Image()
        img.set_from_stock(Gtk.STOCK_REFRESH, Gtk.IconSize.BUTTON)
        b.set_image(img)
        vbox.pack_start(b, False, False, 0)
        b.connect('clicked', lambda w: self._app.check_plugin_updates())
        f = Gtk.Frame()
        l = Gtk.Label()
        l.set_markup("<b>%s</b>" % _("SEARCH_OPTIONS"))
        f.set_label_widget(l)
        self.pack_start(f, False, False, 0)
        table = Gtk.Table()
        f.add(table)
        table.set_border_width(5)
        table.set_col_spacings(10)
        table.set_row_spacings(10)
        self.stop_search_when_nb_results_reaches_cb = Gtk.CheckButton(
            _("STOP_SEARCH_WHEN_NB_RESULTS_REACHES"))
        self.stop_search_when_nb_results_reaches_cb.set_active(
            app.config["stop_search_when_nb_results_reaches_enabled"])
        table.attach(self.stop_search_when_nb_results_reaches_cb,
                     0, 1, 0, 1, xoptions=Gtk.AttachOptions.FILL, yoptions=0)
        self.stop_search_when_nb_results_reaches_nb = Gtk.SpinButton()
        self.stop_search_when_nb_results_reaches_nb.set_range(10, 10000)
        self.stop_search_when_nb_results_reaches_nb.set_increments(10, 100)
        table.attach(self.stop_search_when_nb_results_reaches_nb,
                     1, 2, 0, 1, yoptions=0)
        self.stop_search_when_nb_results_reaches_cb.connect(
            'toggled', self.on_stop_search_when_nb_results_reaches_cb_toggled)
        self.stop_search_when_nb_results_reaches_nb.connect(
            'changed', self.on_stop_search_when_nb_results_reaches_nb_changed)
        self.stop_search_when_nb_results_reaches_nb.set_value(
            app.config["stop_search_when_nb_results_reaches_value"])

    def on_stop_search_when_nb_results_reaches_cb_toggled(self, widget):
        self._app.config["stop_search_when_nb_results_reaches_enabled"] = widget.get_active()

    def on_stop_search_when_nb_results_reaches_nb_changed(self, widget):
        self._app.config["stop_search_when_nb_results_reaches_value"] = int(widget.get_value())

    def on_hide_zero_seeders_toggled(self, widget):
        self._app.config["hide_zero_seeders"] = widget.get_active()

    def on_torrent_custom_app_changed(self, widget):
        self._app.config['torrent_custom_app'] = widget.get_text()

    def on_torrent_standard_app_changed(self, widget):
        self._app.config["torrent_standard_app"] = self.torrent_use_standard_app_cb_ls[widget.get_active()][0]

    def on_torrent_mode_changed(self, widget):
        self.torrent_save_in_folder_fs.set_sensitive(False)
        self.torrent_use_standard_app_cb.set_sensitive(False)
        self.torrent_use_custom_app_entry.set_sensitive(False)
        if self.torrent_save_in_folder_rb.get_active():
            self._app.config["torrent_mode"] = "save_in_folder"
            self.torrent_save_in_folder_fs.set_sensitive(True)
        elif self.torrent_use_standard_app_rb.get_active():
            self._app.config["torrent_mode"] = "use_standard_app"
            self.torrent_use_standard_app_cb.set_sensitive(True)
        else:
            self._app.config["torrent_mode"] = "use_custom_app"
            self.torrent_use_custom_app_entry.set_sensitive(True)


class _PluginsPreferencesPage(Gtk.ScrolledWindow):
    def __init__(self, app):
        Gtk.ScrolledWindow.__init__(self)
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.tv = Gtk.TreeView()
        self.tv.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        self.add(self.tv)
        self.lb = Gtk.ListStore(object, str)
        self.tv.set_model(self.lb)
        r = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("PLUGIN_NAME"), r, text=1)
        self.tv.append_column(col)
        r = Gtk.CellRendererToggle()
        col = Gtk.TreeViewColumn(_("ENABLE"), r)
        self.tv.append_column(col)
        r.set_property("activatable", True)
        r.connect('toggled', self._on_enabled_toggled)
        col.set_cell_data_func(r, self._enabled_data_func)
        r = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("LAST_UPDATE"), r)
        self.tv.append_column(col)
        col.set_cell_data_func(r, self._last_update_data_func)
        r = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("URL"), r)
        self.tv.append_column(col)
        col.set_cell_data_func(r, self._url_data_func)
        r = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("AUTHOR"), r)
        self.tv.append_column(col)
        col.set_cell_data_func(r, self._author_data_func)
        l = []
        for i in app.search_plugins:
            l.append(i)
        l.sort(key=_getkey)
        for i in l:
            self.lb.append((i, i.TITLE))
        self.tv.connect('button_press_event', self.on_button_press_event)
        self.tv.connect('motion_notify_event', self.on_motion_notify_event)

    def on_motion_notify_event(self, widget, event):
        data = widget.get_path_at_pos(int(event.x), int(event.y))
        if data:
            path, column, x, y = data
            if column.get_property('title') == _("URL"):
                self.tv.window.set_cursor(Gtk.gdk.Cursor(Gtk.gdk.HAND2))
                return
        self.tv.window.set_cursor(Gtk.gdk.Cursor(Gtk.gdk.ARROW))

    def _url_data_func(self, column, cell, model, iter):
        plugin = model.get_value(iter, 0)
        cell.set_property(
            'markup', "<span color='#0000FF'><u>%s</u></span>" % plugin.WEBSITE_URL)

    def enable_items(self, paths):
        for i in paths:
            self.lb[i][0].enabled = True

    def disable_items(self, paths):
        for i in paths:
            self.lb[i][0].enabled = False

    def on_button_press_event(self, widget, event):
        if event.button == 1:
            data = widget.get_path_at_pos(int(event.x), int(event.y))
            if data:
                path, column, x, y = data
                if column.get_property('title') == _("URL"):
                    iter = self.lb.get_iter(path)
                    plugin = self.lb.get_value(iter, 0)
                    webbrowser.open(plugin.WEBSITE_URL)
                    return True
        if event.button == 3:
            data = widget.get_path_at_pos(int(event.x), int(event.y))
            res = False
            if data:
                sel = []
                for i in self.tv.get_selection().get_selected_rows()[1]:
                    sel.append(i[0])
                path, col, cx, cy = data
                if path[0] in sel:
                    res = True
                else:
                    sel = [path[0]]
                if sel:
                    m = Gtk.Menu()
                    item = Gtk.MenuItem(_("ENABLE"))
                    m.add(item)
                    item.connect('activate', lambda w,
                                 s: self.enable_items(s), sel)
                    item = Gtk.MenuItem(_("DISABLE"))
                    m.add(item)
                    item.connect('activate', lambda w,
                                 s: self.disable_items(s), sel)
                    m.show_all()
                    m.popup(None, None, None, 3, event.time)
            return res

    def _last_update_data_func(self, column, cell, model, iter):
        plugin = model.get_value(iter, 0)
        try:
            cell.set_property("text", time.strftime(
                "%c", time.strptime(plugin.RELEASED_TIME, "%Y-%m-%d %H:%M:%S")))
        except:
            cell.set_property("text", _("UNKNOWN"))

    def _author_data_func(self, column, cell, model, iter):
        plugin = model.get_value(iter, 0)
        cell.set_property('text', plugin.AUTHOR)

    def _on_enabled_toggled(self, cell, path):
        iter = self.lb.get_iter(path)
        plugin = self.lb.get_value(iter, 0)
        plugin.enabled = not plugin.enabled

    def _enabled_data_func(self, column, cell, model, iter):
        plugin = model.get_value(iter, 0)
        cell.set_property('active', plugin.enabled)


def _getkey(a):
    return a.TITLE.lower()
