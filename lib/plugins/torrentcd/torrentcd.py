#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import TorrentSearch
import urllib.request
import urllib.parse
import urllib.error
import libxml2
import os
import datetime
import time
import httplib2
import TorrentSearch.htmltools


class TorrentCDPluginResult(TorrentSearch.Plugin.PluginResult):

    def __init__(self, label, date, size, seeders, leechers, category, details_page_url):
        TorrentSearch.Plugin.PluginResult.__init__(
            self, label, date, size, seeders, leechers, category=category)
        self.details_page_url = details_page_url

    def _do_get_link(self):
        c = httplib2.Http()
        resp, content = c.request(self.details_page_url)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        for link in TorrentSearch.htmltools.find_elements(tree.getRootElement(), "a", title="Download"):
            if link.prop("href").startswith("/torrents/") and link.prop("href").endswith(".torrent"):
                return urllib.basejoin(self.details_page_url, link.prop("href"))


class TorrentCDPlugin(TorrentSearch.Plugin.Plugin):

    def plugin_run_search(self, pattern, page_url=""):
        if page_url == "":
            page_url = "http://torrent.cd/torrents/search/?q=" + \
                urllib.parse.quote_plus(pattern)
        resp, content = self.api_http_queue_request(page_url)
        tree = libxml2.htmlParseDoc(content, "utf-8")

        titles = TorrentSearch.htmltools.find_elements(
            tree.getRootElement(), "h2")
        i = 0
        while "site results" not in titles[i].getContent():
            i += 1
        header = titles[i]
        self.results_count = int(header.getContent().split(" ")[0])
        pager = header.__next__
        table = pager.__next__

        results = TorrentSearch.htmltools.find_elements(table, "tr")[1:]

        for result in results:
            try:
                self._parse_result(page_url, result)
            except:
                pass
            if self.stop_search:
                return

        cur_page = TorrentSearch.htmltools.find_elements(
            pager, "li", **{'class': 'page selected'})[0]
        next_page_link_li = cur_page.next.__next__
        if next_page_link_li.prop("class") == "page":
            next_page_link = urllib.basejoin(page_url, TorrentSearch.htmltools.find_elements(
                next_page_link_li, "a")[0].prop("href"))
            self.plugin_run_search(pattern, next_page_link)

    def _parseCat(self, cat):
        return ""

    def _parse_result(self, base_url, result_line):
        date_cell, desc_cell, empty_cell, size_cell, seeders_cell, leechers_cell, category_cell = TorrentSearch.htmltools.find_elements(
            result_line, "td")
        day, month, year = date_cell.getContent().split(".")
        day = int(day)
        month = int(month)
        year = int("20"+year)
        date = datetime.date(year, month, day)
        link = TorrentSearch.htmltools.find_elements(desc_cell, "a")[0]
        title = link.getContent()
        details_page_url = urllib.basejoin(base_url, link.prop("href"))
        size = size_cell.getContent().upper()
        seeders = int(seeders_cell.getContent())
        leechers = int(leechers_cell.getContent())
        cat = self._parseCat(category_cell.getContent())

        self.api_add_result(TorrentCDPluginResult(title, date, size,
                                              seeders, leechers, cat, details_page_url))
