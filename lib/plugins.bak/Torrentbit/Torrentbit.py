#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import TorrentSearch
import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import os
import time
import httplib2
from TorrentSearch import htmltools


class TorrentbitPluginResult(TorrentSearch.Plugin.PluginResult):
    def __init__(self, label, date, size, seeders, leechers, torrent, magnet):
        self.torrent = torrent
        TorrentSearch.Plugin.PluginResult.__init__(
            self, label, date, size, seeders, leechers, magnet)

    def _do_get_link(self):
        return self.torrent


class TorrentbitPlugin(TorrentSearch.Plugin.Plugin):
    def run_search(self, pattern, page=1, href=None):
        if href is None:
            href = "http://www.torrentbit.net/search/?torrent=" + urllib.parse.quote_plus(pattern)
        resp, content = self.api.http_queue_request(href)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        td = htmltools.find_elements(tree.getRootElement(), "td", id="main")[0]
        try:
            h = htmltools.find_elements(td, "h1")[0]
            data = h.getContent().rstrip().lstrip()
            i = len(data)-1
            while i >= 0 and data[i] not in "0123456789":
                i -= 1
            j = i
            while j >= 0 and data[j] in "0123456789":
                j -= 1
            self.results_count = eval(data[j+1:i+1])
        except:
            pass
        div = htmltools.find_elements(htmltools.find_elements(
            td, "div", **{'class': 't_list'})[0], "tbody")[0]
        lines = htmltools.find_elements(div, "tr")
        for i in lines:
            try:
                date, descr, title, size, rts, seeders, leechers, dl, cat = htmltools.find_elements(
                    i, "td")
                date = date.getContent().replace(chr(194)+chr(160), " ")
                day, month, year = date.split(" ")
                while day[0] == "0":
                    day = day[1:]
                day = eval(day)
                month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
                         "Aug", "Sep", "Oct", "Nov", "Dec"].index(month)+1
                year = eval(year)
                date = datetime.date(year, month, day)
                link = htmltools.find_elements(title, "a")[0]
                label = link.getContent()
                link = urllib.basejoin(
                    href, urllib.parse.quote(link.prop('href')))
                size = size.getContent().replace(chr(194)+chr(160), " ")
                seeders = eval(seeders.getContent())
                leechers = eval(leechers.getContent())
                resp, content = self.api.http_queue_request(link)
                itemtree = libxml2.htmlParseDoc(content, "utf-8")
                table = htmltools.find_elements(
                    itemtree.getRootElement(), "table", **{'class': 'tor_item'})[0]
                thislines = htmltools.find_elements(table, "tr")
                for j in thislines:
                    if htmltools.find_elements(j, "th")[0].getContent() == "Download torrent:":
                        itemlink = urllib.basejoin(
                            link, htmltools.find_elements(j, "a")[0].prop('href'))
                        break
                hashvalue = htmltools.find_elements(
                    lines[4], "td")[0].getContent()
                magnet = "magnet:?xt=urn:btih:"+hashvalue
                self.api.notify_one_result(TorrentbitPluginResult(
                    label, date, size, seeders, leechers, itemlink, magnet))
            except:
                pass
            if self.stop_search:
                return
        if not self.stop_search:
            try:
                try:
                    pager = htmltools.find_elements(
                        tree.getRootElement(), "div", id="pagination")[0]
                except:
                    pager = None
                if pager:
                    nextlink = htmltools.find_elements(
                        pager, "a", title="Next page")
                    if nextlink:
                        nextlink = urllib.basejoin(
                            href, nextlink[0].prop('href'))
                        self.run_search(pattern, 1, nextlink)
            except:
                pass