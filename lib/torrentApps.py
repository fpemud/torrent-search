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


def mime_get_all_applications(mimetype):
    paths = os.getenv("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    paths += os.getenv("XDG_DATA_HOME", "~/.local/share").split(":")
    list_files = []
    for i in paths:
        path = os.path.join(os.path.realpath(
            i.replace("~", os.getenv('HOME'))), "applications")
        mimeinfo = os.path.join(path, "mimeinfo.cache")
        if os.path.exists(mimeinfo) and os.access(mimeinfo, os.R_OK):
            list_files.append(mimeinfo)
    desktops = {}
    for i in list_files:
        f = open(i)
        lines = f.read().splitlines()
        f.close()
        for j in lines:
            try:
                mtype, ds = j.split("=")
                if mtype == mimetype:
                    for k in ds.split(";"):
                        if k and k not in desktops:
                            if k not in desktops:
                                filename = os.path.join(os.path.split(i)[0], k)
                                if os.path.exists(filename):
                                    desktops[k] = filename
                                elif "-" in k:
                                    tl = k.index("-")
                                    filename = os.path.join(
                                        os.path.split(i)[0], k[:tl], k[tl+1:])
                                    if os.path.exists(filename):
                                        desktops[k] = filename
            except:
                pass
    res = []
    for i in desktops:
        try:
            command = None
            title = None
            f = open(desktops[i])
            lines = f.read().splitlines()
            f.close()
            for j in lines:
                try:
                    k = j.index("=")
                    key = j[:k]
                    value = j[k+1:]
                    if key == "Exec":
                        command = value
                    if key == "Name":
                        title = value
                except:
                    pass
            if command and title:
                res.append((i, title, command))
        except:
            pass
    return res


def listApps():
    try:
        res = []
        for i in mime_get_all_applications("application/x-bittorrent"):
            res.append(i[:3])
        return res
    except:
        return []
