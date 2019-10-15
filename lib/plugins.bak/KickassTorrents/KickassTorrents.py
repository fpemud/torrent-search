#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import TorrentSearch
import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import os
import httplib2
from TorrentSearch import htmltools


class KickassTorrentsPluginResult(TorrentSearch.Plugin.PluginResult):
    def __init__(self, label, date, size, seeders, leechers, torrent, magnet):
        self.torrent = torrent
        TorrentSearch.Plugin.PluginResult.__init__(
            self, label, date, size, seeders, leechers, magnet)

    def _do_get_link(self):
        return self.torrent


class KickassTorrentsPlugin(TorrentSearch.Plugin.Plugin):
    def plugin_run_search(self, pattern, page=1, href=None):
        if href == None:
            href = "https://kickass.to/usearch/%s/" % urllib.parse.quote(
                pattern)
        c = httplib2.Http()
        resp, content = c.request(href)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        div = htmltools.find_elements(
            tree.getRootElement(), "div", **{'class': 'mainpart'})[0]
        try:
            self.results_count = int(htmltools.find_elements(htmltools.find_elements(
                tree.getRootElement(), "h1")[0], "span")[0].getContent().split(" ")[-1])
        except:
            pass
        table = htmltools.find_elements(
            tree.getRootElement(), "table", **{'class': 'data'})[0]
        lines = htmltools.find_elements(table, "tr")[1:]
        for i in lines:
            try:
                links, size, nbfiles, date, seeders, leechers = htmltools.find_elements(
                    i, "td")
                size = size.getContent().rstrip().lstrip()
                seeders = int(seeders.getContent())
                leechers = int(leechers.getContent())
                div = htmltools.find_elements(
                    links, "div", **{'class': 'torrentname'})[0]
                link = htmltools.find_elements(div, "a")[1]
                label = ""
                for j in link.getContent().splitlines():
                    label += j
                link = urllib.basejoin(href, link.prop('href'))
                c = httplib2.Http()
                resp, content = c.request(
                    link, headers={'Cookie': 'country_code=en'})
                itemtree = libxml2.htmlParseDoc(content, "utf-8")
                div = htmltools.find_elements(itemtree.getRootElement(
                ), "div", **{"class": "buttonsline downloadButtonGroup clearleft novertpad"})[0]
                magnet, torrent = htmltools.find_elements(div, "a")[:2]
                torrent = urllib.basejoin(link, torrent.prop('href'))
                magnet = magnet.prop('href')
                if "&" in magnet:
                    i = magnet.index('&')
                    magnet = magnet[:i]
                try:
                    data = htmltools.find_elements(itemtree.getRootElement(
                    ), "time", itemprop="publishDate")[0].getContent().split(" ")
                    day, month, year = data
                    day = int(day)
                    month = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
                             'August', 'September', 'October', 'November', 'December'].index(month)+1
                    year = int(year)
                except:
                    data = htmltools.find_elements(itemtree.getRootElement(
                    ), "div", **{'class': 'font11px lightgrey line160perc'})[0].children.getContent().rstrip().lstrip()[9:-3]
                    while "  " in data:
                        data = data.replace("  ", " ")
                    monthday, year = data.split(", ")
                    month, day = monthday.split(" ")
                    year = int(year)
                    day = int(day)
                    month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
                             'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].index(month)+1
                date = datetime.date(year, month, day)
                self.api.notify_one_result(KickassTorrentsPluginResult(
                    label, date, size, seeders, leechers, torrent, magnet))
            except:
                pass
            if self.stop_search:
                return
        if not self.stop_search:
            try:
                try:
                    pager = htmltools.find_elements(
                        tree.getRootElement(), "div", **{'class': 'pages'})[0]
                except:
                    pager = None
                if pager:
                    pages = htmltools.find_elements(pager, "a")
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
                        self.plugin_run_search(pattern, pn, urllib.basejoin(
                            href, pages[i].prop('href')))
            except:
                pass
