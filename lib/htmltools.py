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


def find_elements(node, elname=None, maxdepth=-1, **params):
    res = []
    if elname is None or node.name == elname:
        add = True
        for i in params:
            if node.prop(i) != params[i]:
                add = False
                break
        if add:
            res.append(node)
    if maxdepth != 0:
        child = node.children
        while child:
            res += find_elements(child, elname, maxdepth-1, **params)
            child = child.next
    return res


def parse_cookie(set_cookie):
    """Format a received cookie correctly in order for it to be sent back to the server

    Parameters:
        * set_cookie : cookie to parse (str)

    Return value : formatted cookie (str)"""

    cookies = []
    cur = ""
    for i in range(len(set_cookie)):
        if set_cookie[i] == "," and not re.match("expires=(Mon|Tue|Wed|Thu|Fri|Sat|Sun)", set_cookie[i-11:i]):
            cookies.append(cur)
            cur = ""
        else:
            cur += set_cookie[i]
    if cur:
        cookies.append(cur)
    d = {}
    for i in cookies:
        params = i.rstrip().lstrip().split(";")
        for p in params:
            try:
                key, value = p.rstrip().lstrip().split("=")
                if key not in ["expires", "path"] and value != 'deleted':
                    d[key] = value
                    if cookie:
                        cookie += "; "
                    cookie += key+"="+value
            except:
                pass
    cookie = ""
    for key in d:
        value = d[key]
        if cookie:
            cookie += "; "
        cookie += key+"="+value
    return cookie
