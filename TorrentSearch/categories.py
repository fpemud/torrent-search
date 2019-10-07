#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import libxml2


class Category(object):

    def __init__(self, cid, desc, subcats):
        self.id = cid
        self._desc = desc
        self._subcats = subcats
        self._parent = None
        for i in subcats:
            i.setParent(self)

    def setParent(self, parent):
        self._parent = parent

    def __str__(self):
        return repr(self)

    def __repr__(self):
        if self._parent:
            res = repr(self._parent)+"/"+self._desc
        else:
            res = self._desc
        return res

    def __getitem__(self, path):
        if not path:
            return self
        for i in self._subcats:
            if i.id == path[0]:
                return i[path[1:]]
        return self

    def all(self):
        res = [self]
        for i in self._subcats:
            res += i.all()
        return res

    def contains(self, cat):
        return cat in self.all()


CATEGORY_OTHER = Category("null", _("CATEGORY_OTHER"), [])


class CategoriesList(object):

    def __init__(self, categories_file):
        self._load(categories_file)

    def all(self):
        res = []
        for i in self._categories:
            res += i.all()
        return res

    def _load_categories(self, node):
        res = []
        child = node.children
        while child:
            if child.name == "category":
                res.append(Category(child.prop('id'), _(child.prop(
                    'description')), self._load_categories(child)))
            child = child.__next__       # FIXME
        return res

    def _load(self, filename):
        d = libxml2.parseFile(filename)
        r = d.getRootElement()
        self._categories = self._load_categories(r)

    def __iter__(self):
        return iter(self._categories)

    def __repr__(self):
        res = ""
        for i in self._categories:
            if res:
                res += ", "
            res += repr(i)
        return "["+res+"]"

    def __getitem__(self, path):
        if not path:
            return CATEGORY_OTHER
        path = path.split("/")
        for i in self._categories:
            if i.id == path[0]:
                return i[path[1:]]
        return CATEGORY_OTHER
