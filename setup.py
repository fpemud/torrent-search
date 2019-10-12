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
import sys
from distutils.core import setup


def list_lib_files():
    res = []
    for path, dirs, files in os.walk("lib"):
        files2 = []
        for i in files:
            if os.path.isfile(os.path.join(path, i)):
                if i[-1] != "~" and i[-4:] != ".bak":
                    files2.append(os.path.join(path, i))
        if files2 != []:
            res.append((path, files2))
    return []           # FIXME


def list_share_files():
    res = []
    for path, dirs, files in os.walk("share"):
        files2 = []
        for i in files:
            if os.path.isfile(os.path.join(path, i)):
                if i[-1] != "~" and i[-4:] != ".bak":
                    files2.append(os.path.join(path, i))
        if files2 != []:
            res.append((path, files2))
    return res


# We use Makefile instead
assert False

setup(name="torrent-search",
      version="0.11.2",
      author="Gwendal Le Bihan",
      author_email="gwendal.lebihan.dev@gmail.com",
      maintainer="Gwendal Le Bihan",
      maintainer_email="gwendal.lebihan.dev@gmail.com",
      description="Search for torrents on different websites",
      scripts=["torrent-search"],
      packages=["TorrentSearch", "TorrentSearch.exceptions"],
      data_files=list_lib_files()+list_share_files(),
      url="http://torrent-search.sourceforge.net",
      download_url="http://sourceforge.net/projects/torrent-search/files/",
      )
