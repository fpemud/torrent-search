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

PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRCPATH = os.path.join(PATH, "manpages")
DESTPATH = os.path.join(PATH, "share", "man")

if __name__ == "__main__":
    os.chdir(SRCPATH)
    for i in os.listdir(SRCPATH):
        if i[-1] != "~" and i[0] != '.':
            prg, lang, ext = i.split('.')
            if lang == "en":
                path = os.path.join(DESTPATH, "man1")
            else:
                path = os.path.join(DESTPATH, lang, "man1")
            if not os.path.exists(path):
                os.system('mkdir -p "%s"' % path)
            os.system('gzip -c "%s" > "%s"' % (i, os.path.join(path, "torrent-search.1.gz")))
