#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-


import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import time


class TorrentDownloadsPlugin:

    def __init__(self, api):
        self.api = api

    def run_search(self, pattern, param, page_url=""):
        self.api_notify_results_total_count = param["notify-results-total-count"]
        self.api_notify_one_result = param["notify-one-result"]

        if page_url == "":
            page_url = "http://www.torrentdownloads.net/search/?search=" + \
                urllib.parse.quote_plus(pattern)
        resp, content = self.api.http_queue_request(page_url)
        tree = libxml2.htmlParseDoc(content, "utf-8")

        try:
            title_bar = self.api.find_elements(
                tree.getRootElement(), "div", **{'class': 'title_bar1'})[0]
            count = int(self.api.find_elements(
                title_bar, "span", **{'class': 'num'})[0].getContent().rstrip().lstrip())
            self.api_notify_results_total_count(count)
        except:
            pass

        results_list = title_bar.parent
        results = self.api.find_elements(results_list, "div", 1)
        i = 0
        while i < len(results):
            if results[i].prop("class").startswith("grey_bar3"):
                i += 1
            else:
                del results[i]
        results = results[1:]

        for result in results:
            try:
                self._parse_result(result)
            except:
                pass
            if self.stop_search:
                return

        pagination_box = self.api.find_elements(
            results_list, "div", **{'class': 'pagination_box'})[0]
        pager_links = self.api.find_elements(
            pagination_box, "a")
        for i in pager_links:
            if i.getContent() == ">>":
                self.run_search(pattern, i.prop('href'))
                return

    def _parse_result(self, result_line):
        link = self.api.find_elements(result_line, "a")[0]
        label = link.getContent()
        link = link.prop('href')
        if not link.startswith("http://www.torrentdownloads.net"):
            return
        health, leechers, seeders, size = self.api.find_elements(
            result_line, "span", 1)[:4]
        seeders = eval(seeders.getContent())
        leechers = eval(leechers.getContent())
        size = size.getContent().replace(chr(194)+chr(160), " ")

        resp, content = self.api.http_queue_request(link)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        for i in self.api.find_elements(tree.getRootElement(), "div", **{'class': 'grey_bar1'})+self.api.find_elements(tree.getRootElement(), "div", **{'class': 'grey_bar1 back_none'}):
            span = self.api.find_elements(i, "span")
            if span:
                span = span[0]
                key = span.getContent()
                value = span.next.getContent().rstrip().lstrip()
                if key == "Torrent added:":
                    date = value
        date = time.strptime(date, "%Y-%m-%d %H:%M:%S")
        date = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)

        torrent_url = self.api.find_elements(self.api.find_elements(tree.getRootElement(
        ), "ul", **{'class': 'download'})[0], "img", src="/templates/new//images/download_button1.jpg")[0].parent.prop("href")

        self.api_notify_one_result({
            "id": "",
            "label": label,
            "date": date,
            "size": size,
            "seeders": seeders,
            "leechers": leechers,
            "link": torrent_url,
        })
