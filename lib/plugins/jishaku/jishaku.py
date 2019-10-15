#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import time


class JishakuPlugin:

    def __init__(self, api):
        self.api = api

    def run_search(self, pattern, param, page_url=""):
        self.api_notify_results_total_count = param["notify-results-total-count"]
        self.api_notify_one_result = param["notify-one-result"]

        if page_url == "":
            page_url = "http://www.jishaku.net/?q=" + \
                urllib.parse.quote_plus(pattern)+"&limit=150"
        resp, content = self.api.http_queue_request(page_url)
        tree = libxml2.htmlParseDoc(content, "utf-8")

        results_table = self.api.find_elements(
            tree.getRootElement(), "table", id="main-index")[0]
        results = self.api.find_elements(results_table, "tr")

        for result in results:
            try:
                self._parse_result(result)
            except:
                pass
            if self.stop_search:
                return

        pager = self.api.find_elements(
            tree.getRootElement(), "ul", **{'class': 'main-pagination'})[0]
        next_page_link = self.api.find_elements(
            self.api.find_elements(pager, "li")[-2], "a")[0]
        if next_page_link.getContent() == ">":
            url = urllib.basejoin(page_url, next_page_link.prop('href'))
            self.run_search(pattern, url)

    def _parse_result(self, result_line):
        category, infos, details = self.api.find_elements(
            result_line, "td")
        name, other = self.api.find_elements(infos, "div")
        magnet, torrent = self.api.find_elements(name, "a")
        label = magnet.getContent()
        magnet_link = magnet.prop('href')
        torrent_link = torrent.prop('href')
        size, date = self.api.find_elements(other, "abbr")
        size = size.getContent().replace('i', '')
        date = time.strptime(date.prop('title').split(' ')[0], "%Y-%m-%d")
        date = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
        self.api_notify_one_result({
            "id": "",
            "label": label,
            "date": date,
            "size": size,
            "link": torrent_link,
            "magnet_link": magnet_link,
        })
