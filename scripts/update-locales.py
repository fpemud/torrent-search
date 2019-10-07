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
import gnomevfs
import gettext
import gconf
import gtk
import libxml2
from TorrentSearch import htmltools

PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def walk_sources(res, path, files):
    for i in files:
        filename = path+"/"+i
        try:
            mime = gnomevfs.get_mime_type(filename)
            if mime == "text/x-python" and filename != __file__ and filename[-9:] != ".svn-base":
                res.append(filename)
        except:
            pass


def list_sources():
    res = []
    os.path.walk(PATH, walk_sources, res)
    return res


def list_keys_for_file(filename, res):
    i = 0
    f = open(filename)
    data = f.read()
    f.close()
    while i < len(data):
        if data[i:i+3] in ["_(\"", "_('"]:
            j = data[i+3:].index(data[i+2])+i+3
            if not "\n" in data[i+3:j] and not data[i+3:j] in res:
                res.append(data[i+3:j])
            i = j+1
        else:
            i += 1


def list_keys():
    l = list_sources()
    res = []
    for i in l:
        list_keys_for_file(i, res)
    d = libxml2.parseFile(os.path.join(
        PATH, "share", "torrent-search", "categories.xml"))
    items = htmltools.find_elements(d, "category")
    for i in items:
        item = i.prop('description')
        if not item in res:
            res.append(item)
    return res


def list_langs():
    path = PATH+"/po files"
    res = []
    for i in os.listdir(path):
        if i[-3:] == ".po":
            res.append(i[:-3])
    #res=['en', 'fr','it']
    return res


def compute_po_file(lang):
    src = PATH+"/po files/%s.po" % lang
    destpath = PATH+"/share/locale/%s/LC_MESSAGES/" % lang
    dest = destpath+"torrent-search.mo"
    if not os.path.exists(destpath):
        os.system('mkdir -p "%s"' % destpath)
    os.system('msgfmt "%s" -o "%s"' % (src, dest))


class TranslateDialog(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(self, "Translation")
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        table = gtk.Table()
        self.child.add(table)
        table.set_border_width(5)
        table.set_col_spacings(10)
        table.set_row_spacings(10)
        l = gtk.Label('Language')
        l.set_alignment(0, 0.5)
        table.attach(l, 0, 1, 0, 1, xoptions=gtk.FILL, yoptions=0)
        self.language = gtk.Label()
        table.attach(self.language, 1, 2, 0, 1, yoptions=0)
        self.language.set_alignment(0, 0.5)
        l = gtk.Label('Key')
        l.set_alignment(0, 0.5)
        table.attach(l, 0, 1, 1, 2, xoptions=gtk.FILL, yoptions=0)
        self.key = gtk.Label()
        self.key.set_alignment(0, 0.5)
        table.attach(self.key, 1, 2, 1, 2, yoptions=0)
        l = gtk.Label('Translation')
        l.set_alignment(0, 0)
        table.attach(l, 0, 1, 2, 3, xoptions=gtk.FILL)
        self.translation = gtk.TextView()
        scw = gtk.ScrolledWindow()
        scw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scw.add(self.translation)
        scw.set_size_request(400, 300)
        table.attach(scw, 1, 2, 2, 3, yoptions=0)

    def run(self, lang, key):
        self.language.set_text(lang)
        self.key.set_text(key)
        self.translation.get_buffer().set_text("")
        self.show_all()
        if gtk.Dialog.run(self) == gtk.RESPONSE_OK:
            siter = self.translation.get_buffer().get_start_iter()
            eiter = self.translation.get_buffer().get_end_iter()
            res = self.translation.get_buffer().get_text(siter, eiter)
        else:
            res = ""
        self.hide()
        return res


if __name__ == '__main__':
    dialog = TranslateDialog()
    langs = list_langs()
    keys = list_keys()
    for i in langs:
        os.system(
            'rm "%s/share/locale/%s/LC_MESSAGES/torrent-search.mo"' % (PATH, i))
        compute_po_file(i)
        print "Checking language %s..." % i
        try:
            t = gettext.translation(
                "torrent-search", PATH+"/share/locale", [i])
            add_all = False
        except:
            add_all = True
        add_values = []
        for j in keys:
            if (add_all or t.gettext(j) == j) and not j in ['URL']:
                value = dialog.run(i, j)
                if value:
                    add_values.append((j, value))
        if add_values:
            add_data = ""
            for j, k in add_values:
                add_data += "msgid \"%s\"\nmsgstr \"%s\"\n\n" % (
                    j, k.replace('"', '\\"'))
            f = open(PATH+"/po files/%s.po" % i, "a")
            f.write(add_data)
            f.close()
        compute_po_file(i)
    d = gtk.MessageDialog()
    d.set_markup("<span size='large'><b>Done.</b></span>")
    d.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
    d.run()
