#!/usr/bin/env python3

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


def _walk_lib_files(res, path, files):
    if ".git" in path:
        return
    tl = []
    for i in files:
        if os.path.isfile(os.path.join(path, i)):
            if i[-1] != "~" and i[-4:] != ".bak":
                tl.append(os.path.join(path, i))
    if tl != []:
        res.append((os.path.join("lib", path[4:]), l))


def list_lib_files():
    res = []
    os.path.walk("lib", _walk_lib_files, res)
    return res


def _walk_share_files(res, path, files):
    if ".git" in path:
        return
    tl = []
    for i in files:
        if os.path.isfile(os.path.join(path, i)):
            if i[-1] != "~" and i[-4:] != ".bak":
                tl.append(os.path.join(path, i))
    if tl != []:
        res.append((os.path.join("share", path[6:]), l))


def list_share_files():
    res = []
    os.path.walk("share", _walk_share_files, res)
    return res


setup(name="torrent-search",
      version="0.11.2",
      author="Gwendal Le Bihan",
      author_email="gwendal.lebihan.dev@gmail.com",
      maintainer="Gwendal Le Bihan",
      maintainer_email="gwendal.lebihan.dev@gmail.com",
      description="Search for torrents on different websites",
      scripts=["torrent-search", "torrent-search-gnomeapplet"],
      packages=["TorrentSearch", "TorrentSearch.exceptions"],
      data_files=list_share_files()+list_lib_files(),
      url="http://torrent-search.sourceforge.net",
      download_url="http://sourceforge.net/projects/torrent-search/files/",
      )
