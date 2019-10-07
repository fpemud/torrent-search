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
    if elname == None or node.name == elname:
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
            child = child.__next__    # FIXME
    return res
