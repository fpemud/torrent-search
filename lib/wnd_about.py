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


def on_url_activated(dialog, url, data):
    webbrowser.open(url)


def on_email_activated(dialog, link, data):
    if link[:7] == "http://":
        on_url_activated(dialog, link, data)
    else:
        webbrowser.open("mailto:"+link)


class AboutDialog(Gtk.AboutDialog):
    def __init__(self, app):
        # Gtk.about_dialog_set_url_hook(on_url_activated, None)       # FIXME, use activate-link?
        # Gtk.about_dialog_set_email_hook(on_email_activated, None)   # FIXME, use activate-link?
        Gtk.AboutDialog.__init__(self)
        self.set_transient_for(app)
        self.set_program_name(informations.APPNAME)
        self.set_version(informations.VERSION)
        self.set_authors(informations.AUTHORS)
        self.set_documenters(informations.DOCUMENTERS)
        self.set_translator_credits(informations.TRANSLATOR_CREDITS)
        self.set_website(informations.WEBSITE)
        self.set_copyright(informations.COPYRIGHT)
        self.set_license(informations.LICENSE)
        self.set_artists(informations.ARTISTS)
        self.set_logo_icon_name("torrent-search")
        self.set_comments(_("ABOUT_DIALOG_COMMENTS"))

    def run(self):
        self.show_all()
        Gtk.AboutDialog.run(self)
        self.hide()
