#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import time


class NipponseiPlugin:

    def __init__(self, api):
        self.api = api

    def run_search(self, pattern, param, page_url=""):
        self.api_notify_results_total_count = param["notify-results-total-count"]
        self.api_notify_one_result = param["notify-one-result"]

        if page_url == "":
            page_url = "https://nipponsei.minglong.org/index.php?section=Tracker&search=" + \
                urllib.parse.quote_plus(pattern)
        resp, content = self.api.http_queue_request(page_url)
        tree = libxml2.htmlParseDoc(content, "utf-8")

        results = self.api.find_elements(self.api.find_elements(
            tree.getRootElement(), "td", id="main")[0], "a", **{'class': 'download'})
        self.api_notify_results_total_count(len(results))
        for i in range(len(results)):
            results[i] = results[i].parent.parent

        for result in results:
            try:
                self._parse_result(result)
            except:
                pass
            if self.stop_search:
                return

    def _parse_result(self, result_line):
        link, date, size, seeders, leechers, downloads, transferred = self.api.find_elements(
            result_line, "td")
        link = self.api.find_elements(link, "a")[0]
        label = link.getContent()
        torrent_url = link.prop('href')
        size = size.getContent()
        seeders = eval(seeders.getContent())
        leechers = eval(leechers.getContent())
        date = time.strptime(date.getContent().split(" ")[0], "%Y-%m-%d")
        date = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)

        self.api_notify_one_result({
            "id": "",
            "label": label,
            "date": date,
            "size": size,
            "seeders": seeders,
            "leechers": leechers,
            "link": torrent_url,
        })
