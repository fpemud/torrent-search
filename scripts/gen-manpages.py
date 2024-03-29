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
import gettext
import datetime
import optparse
from TorrentSearch.config import CONFIG_KEYS
from TorrentSearch.informations import *
from TorrentSearch.clp import OptionParser

LANGS = ["en", "fr"]
PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

HEADER = ''
HEADER += '.TH TORRENT-SEARCH "1" "%%_DATE%%" "torrent-search %%_VERSION%%" "%%_CAT%%"\n'
HEADER += '.SH %%^NAME%%\n'
HEADER += 'torrent-search \- %%_SIMPLE_DESC%% %%_VERSION%%\n'
HEADER += '.SH %%^SYNOPSIS%%\n'
HEADER += '.B torrent-search\n'
HEADER += '[\\fIoptions\\fR]\n'

FOOTER = ''
FOOTER += '.SH %%^_AUTHOR%%\n'
FOOTER += 'Gwendal Le Bihan (gwendal.lebihan.dev@gmail.com)\n'

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "fr": ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"],
}


def gen_date(lang):
    d = datetime.date.today()
    day = str(d.day)
    if len(day) == 1:
        day = "0" + day
    month = MONTHS[lang][d.month-1]
    return day + " " + month + " " + str(d.year)


SPEC_KEYS = {
    "_DATE": gen_date,
    "_CAT": lambda l: "Application",
    "_SIMPLE_DESC": lambda l: {'en': 'manual page for torrent-search', 'fr': 'page de manuel pour torrent-search'}[l],
    "_VERSION": lambda l: VERSION,
    "_AUTHOR": lambda l: {'en': 'Author', 'fr': 'Auteur'}[l],
}


class ManFormatter(optparse.IndentedHelpFormatter):
    def format_option_strings(self, option):
        res = ""
        for i in option._short_opts+option._long_opts:
            if res:
                res += ", "
            res += "\\fB"+i.replace('-', '\\-')+"\\fR"
        return res

    def format_option(self, option):
        return ".TP\n"+self.format_option_strings(option)+"\n"+option.help+"\n"

    def format_heading(self, heading):
        if self.current_indent:
            return ".SH "+heading.upper()+"\n"
        else:
            return ""


def format_options(lang):
    translation = gettext.translation(APPID, os.path.join(PATH, "share", "locale"), [lang])
    translation.install()
    optparser = OptionParser()
    return optparser.format_option_help(ManFormatter())


def format_string(s, lang):
    translation = gettext.translation(APPID, os.path.join(PATH, "share", "locale"), [lang])
    data = s
    while "%%" in data:
        i = data.index("%%")
        j = i + 2
        while data[j:j+2] != "%%":
            j += 1
        key = data[i+2:j]
        if key[0] == "^":
            upper = True
            key = key[1:]
        else:
            upper = False
        if key in SPEC_KEYS:
            value = SPEC_KEYS[key](lang)
        else:
            value = translation.gettext(key)
        if upper:
            value = value.upper()
        data = data[:i] + value + data[j+2:]
    return data


if __name__ == "__main__":
    for lang in LANGS:
        data = format_string(HEADER, lang) + "\n" + format_options(lang)+format_string(FOOTER, lang)
        data = data.replace("\n\n", "\n")
        with open(os.path.join(PATH, "manpages", "torrent-search.%s.man" % (lang)), "w") as f:
            f.write(data)
