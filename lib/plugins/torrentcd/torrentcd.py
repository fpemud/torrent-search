#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import urllib.request
import urllib.parse
import urllib.error
import libxml2
import os
import datetime
import time
import httplib2


class TorrentCDPlugin:

    def __init__(self, api):
        self.api = api

    def run_search(self, pattern, param, page_url=""):
        self.api_notify_results_total_count = param["notify-results-total-count"]
        self.api_notify_one_result = param["notify-one-result"]

        if page_url == "":
            page_url = "http://torrent.cd/torrents/search/?q=" + \
                urllib.parse.quote_plus(pattern)
        resp, content = self.api.http_queue_request(page_url)
        tree = libxml2.htmlParseDoc(content, "utf-8")

        titles = self.api.find_elements(tree.getRootElement(), "h2")
        i = 0
        while "site results" not in titles[i].getContent():
            i += 1
        header = titles[i]
        self.api_notify_results_total_count(int(header.getContent().split(" ")[0]))
        pager = header.__next__
        table = pager.__next__

        results = self.api.find_elements(table, "tr")[1:]

        for result in results:
            try:
                self._parse_result(page_url, result)
            except:
                pass
            if self.stop_search:
                return

        cur_page = self.api.find_elements(
            pager, "li", **{'class': 'page selected'})[0]
        next_page_link_li = cur_page.next.__next__
        if next_page_link_li.prop("class") == "page":
            next_page_link = urllib.basejoin(page_url, self.api.find_elements(
                next_page_link_li, "a")[0].prop("href"))
            self.run_search(pattern, next_page_link)

    def _parseCat(self, cat):
        return ""

    def _parse_result(self, base_url, result_line):
        date_cell, desc_cell, empty_cell, size_cell, seeders_cell, leechers_cell, category_cell = self.api.find_elements(
            result_line, "td")
        day, month, year = date_cell.getContent().split(".")
        day = int(day)
        month = int(month)
        year = int("20"+year)
        date = datetime.date(year, month, day)
        link = self.api.find_elements(desc_cell, "a")[0]
        title = link.getContent()
        details_page_url = urllib.basejoin(base_url, link.prop("href"))
        size = size_cell.getContent().upper()
        seeders = int(seeders_cell.getContent())
        leechers = int(leechers_cell.getContent())
        cat = self._parseCat(category_cell.getContent())

        self.api_notify_one_result({
            "id": "",
            "label": title,
            "date": date,
            "size": size,
            "seeders": seeders,
            "leechers": leechers,
            "link": self._do_get_link(details_page_url),
            "category": cat,
        })

    def _do_get_link(self, details_page_url):
        c = httplib2.Http()
        resp, content = c.request(details_page_url)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        for link in self.api.find_elements(tree.getRootElement(), "a", title="Download"):
            if link.prop("href").startswith("/torrents/") and link.prop("href").endswith(".torrent"):
                return urllib.basejoin(details_page_url, link.prop("href"))
