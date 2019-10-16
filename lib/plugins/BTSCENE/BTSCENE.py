#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import libxml2
import httplib2
import urllib.request
import urllib.parse
import urllib.error
import time
import datetime


class BTSCENETorrentPlugin:

    def __init__(self, api):
        self.api = api

    def run_search(self, pattern, param, page=1, href=None):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        if href is None:
            href = "http://www.btscene.net/verified-search/torrent/%s/" % urllib.parse.quote_plus(
                pattern)
        c = httplib2.Http()
        resp, content = c.request(href)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        try:
            data = self.api.find_elements(tree.getRootElement(
            ), "div", **{'class': 'index_t'})[0].getContent().rstrip().lstrip()[:-8]
            i = len(data)-1
            while data[i] in "0123456789":
                i -= 1
            api_notify_results_total_count(int(data[i+1:]))
        except:
            pass
        restable = self.api.find_elements(
            tree.getRootElement(), "table", **{'class': 'tor'})[0]
        lines = self.api.find_elements(restable, "tr")[1:]
        for i in lines:
            try:
                if i.prop('id') and i.prop('id')[0] == "_":
                    link, size, seeders, leechers, updated = self.api.find_elements(
                        i, "td")
                    date = self._parseDate(self.api.find_elements(
                        link, "div", **{'class': 'subinfo'})[0].getContent().rstrip().lstrip())
                    details_link = self.api.find_elements(link, "a")[0]
                    label = details_link.prop('title')
                    link = urllib.basejoin(
                        href, self.api.find_elements(link, "a")[0].prop('href'))
                    size = size.getContent()
                    resp, content = c.request(urllib.basejoin(
                        href, details_link.prop('href')))
                    itemtree = libxml2.htmlParseDoc(content, "utf-8")
                    try:
                        data = self.api.find_elements(self.api.find_elements(
                            itemtree.getRootElement(), "ul", **{'class': 'tabbernav'})[0], "li")[3].getContent()
                        j = data.index('(')+1
                        data = data[j:]
                        j = data.index(')')
                        data = data[:j]
                        nb_comments = int(data)
                    except:
                        nb_comments = 0
                    filelist = []
                    try:
                        ul = self.api.find_elements(self.api.find_elements(
                            itemtree.getRootElement(), "div", **{'class': 'files_view'})[0], "ul")[0]
                        for item in self.api.find_elements(ul, "li"):
                            if item.prop("class") != "folder":
                                data = item.getContent()
                                j = len(data)-1
                                while data[j] != " ":
                                    j -= 1
                                j -= 1
                                while data[j] != " ":
                                    j -= 1
                                filename = data[:j].rstrip().lstrip()
                                filesize = data[j:].rstrip().lstrip()
                                filelist.append({
                                    "filename": filename,
                                    "size": filesize,
                                })
                    except:
                        pass
                    try:
                        seeders = eval(seeders.getContent())
                    except:
                        seeders = 0
                    try:
                        leechers = eval(leechers.getContent())
                    except:
                        leechers = 0

                    api_notify_one_result({
                        "id": "",
                        "label": label,
                        "date": date,
                        "size": size,
                        "seeders": seeders,
                        "leechers": leechers,
                        "link": link,
                        # "magnet_link": magnet,
                        "orig_link": link,
                        "bn_comments": nb_comments,
                        "filelist": filelist,
                    })
            except:
                pass
            if self.stop_search:
                return
        if not self.stop_search:
            try:
                try:
                    pager = self.api.find_elements(
                        tree.getRootElement(), id="f")[0].parent
                except:
                    pager = None
                if pager:
                    pages = self.api.find_elements(pager, "a")
                    i = 0
                    must_continue = False
                    while i < len(pages) and not must_continue:
                        p = pages[i]
                        try:
                            pn = eval(pages[i].getContent())
                            if pn > page:
                                must_continue = True
                            else:
                                i += 1
                        except:
                            i += 1
                    if must_continue:
                        self.run_search(pattern, pn, urllib.basejoin(
                            href, pages[i].prop('href')))
            except:
                pass

    def _parseDate(self, data):
        count, unit = data.split(" ")[:2]
        count = int(count)
        year = int(time.strftime('%Y'))
        month = int(time.strftime('%m'))
        day = int(time.strftime('%d'))
        res = datetime.date(year, month, day)
        if unit == 'day' or unit == 'days':
            while count > 0:
                res = res-datetime.timedelta(1)
                count -= 1
        elif unit == 'week' or unit == 'weeks':
            while count > 0:
                res = res-datetime.timedelta(7)
                count -= 1
        elif unit == 'month' or unit == 'months':
            while count > 0:
                month -= 1
                if month == 0:
                    month = 12
                    year -= 1
                count -= 1
            res = datetime.date(year, month, day)
        else:
            while count > 0:
                year -= 1
                count -= 1
            res = datetime.date(year, month, day)
        return res

    def _parseLinks(self, url):
        c = httplib2.Http()
        resp, content = c.request(url)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        links = self.api.find_elements(tree.getRootElement(), "a")
        reflink = ""
        magnet = None
        for i in links:
            if i.getContent().lstrip().rstrip().lower() == "download torrent":
                reflink = urllib.basejoin(url, i.prop('href'))
            if i.getContent().lstrip().rstrip() == "magnet link":
                magnet = urllib.basejoin(url, i.prop('href'))
                if "&" in magnet:
                    j = magnet.index("&")
                    magnet = magnet[:j]
        return reflink, magnet
