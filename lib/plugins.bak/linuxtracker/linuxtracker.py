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


class linuxTRACKERPluginResult(TorrentSearch.Plugin.PluginResult):
    def __init__(self, label, date, size, seeders, leechers, torrent_link, magnet_link):
        self.torrent_link = torrent_link
        TorrentSearch.Plugin.PluginResult.__init__(
            self, label, date, size, seeders, leechers, magnet_link=magnet_link)

    def _do_get_link(self):
        itemtree = libxml2.htmlParseFile(self.torrent_link, "utf-8")
        return urllib.basejoin(self.torrent_link, htmltools.find_elements(itemtree.getRootElement(), "img", src="images/download.gif")[0].parent.prop("href"))


class linuxTRACKERPlugin(TorrentSearch.Plugin.Plugin):
    def run_search(self, pattern, href=None):
        if href == None:
            href = "http://linuxtracker.org/index.php?page=torrents&search=" + \
                urllib.parse.quote_plus(pattern)
        resp, content = self.api.http_queue_request(href)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        try:
            pager = htmltools.find_elements(
                tree.getRootElement(), "form", name="change_pagepages")[0]
            options = htmltools.find_elements(pager, "option")
            self.results_count = 50*len(options)
        except:
            pager = None
            self.results_count = 50
        restable = htmltools.find_elements(htmltools.find_elements(tree.getRootElement(
        ), "form", name="deltorrent")[0].parent, "table", **{'class': 'lista'})[0]
        lines = htmltools.find_elements(restable, "tr", 1)[1:]
        for i in lines:
            try:
                infobox = htmltools.find_elements(i, "td", 1)[1]
                link = htmltools.find_elements(infobox, "a")[0]
                label = link.getContent()
                link = urllib.basejoin(
                    href, htmltools.find_elements(link, "a")[0].prop('href'))
                infotable = htmltools.find_elements(infobox, "table")[0]
                torrent_link = urllib.basejoin(href, htmltools.find_elements(
                    infotable, "img", **{'alt': 'torrent'})[0].parent.prop("href"))
                magnet_link = urllib.basejoin(href, htmltools.find_elements(
                    infotable, "img", **{'alt': 'Magnet Link'})[0].parent.prop("href"))
                data = {}
                for data_line in htmltools.find_elements(infotable, "tr"):
                    try:
                        cell = htmltools.find_elements(data_line, "td")[0]
                        key_cell = htmltools.find_elements(cell, "strong")[0]
                        key = key_cell.getContent().rstrip().lstrip()
                        value = key_cell.next.getContent().rstrip().lstrip()
                        data[key] = value
                    except:
                        pass
                date = time.strptime(data["Added On:"], "%d/%m/%Y")
                date = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
                seeders = int(data["Seeds"])
                leechers = int(data["Leechers"])
                size = data["Size:"]
                self.api.notify_one_result(linuxTRACKERPluginResult(
                    label, date, size, seeders, leechers, torrent_link, magnet_link))
            except:
                pass
            if self.stop_search:
                return
        if not self.stop_search:
            try:
                if pager:
                    spans = htmltools.find_elements(pager, "span")
                    i = 0
                    while i < len(spans) and spans[i].prop('class') != 'pagercurrent':
                        i += 1
                    i += 1
                    if i < len(spans):
                        link = htmltools.find_elements(spans[i], "a")[0]
                        link = urllib.basejoin(href, link.prop('href'))
                        self.run_search(pattern, link)
            except:
                pass
