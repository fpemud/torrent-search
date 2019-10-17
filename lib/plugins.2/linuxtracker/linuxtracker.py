#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import time
import httplib2


class linuxTRACKERPlugin:

    def __init__(self, api):
        self.api = api

    def run_search(self, pattern, param, href=None):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        if href is None:
            href = "http://linuxtracker.org/index.php?page=torrents&search=" + urllib.parse.quote_plus(pattern)
        self.api.log("start")
        resp, content = httplib2.Http().request(href)
        content = content.decode("utf-8")
        self.api.log("start2")
        tree = libxml2.htmlParseDoc(content, "utf-8")
        self.api.log("start3")
        try:
            pager = self.api.find_elements(tree.getRootElement(), "form", name="change_pagepages")[0]
            options = self.api.find_elements(pager, "option")
            api_notify_results_total_count(50*len(options))
        except:
            pager = None
            api_notify_results_total_count(50)

        self.api.log("start4")

        restable = self.api.find_elements(
            self.api.find_elements(tree.getRootElement(), "form", name="deltorrent")[0].parent,
            "table",
            **{'class': 'lista'})[0]
        lines = self.api.find_elements(restable, "tr", 1)[1:]
        for i in lines:
            try:
                infobox = self.api.find_elements(i, "td", 1)[1]
                link = self.api.find_elements(infobox, "a")[0]
                label = link.getContent()
                link = urllib.basejoin(
                    href, self.api.find_elements(link, "a")[0].prop('href'))
                infotable = self.api.find_elements(infobox, "table")[0]
                torrent_link = urllib.basejoin(href, self.api.find_elements(
                    infotable, "img", **{'alt': 'torrent'})[0].parent.prop("href"))
                magnet_link = urllib.basejoin(href, self.api.find_elements(
                    infotable, "img", **{'alt': 'Magnet Link'})[0].parent.prop("href"))
                data = {}
                for data_line in self.api.find_elements(infotable, "tr"):
                    try:
                        cell = self.api.find_elements(data_line, "td")[0]
                        key_cell = self.api.find_elements(cell, "strong")[0]
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
                api_notify_one_result({
                    "id": "",
                    "label": label,
                    "date": date,
                    "size": size,
                    "seeders": seeders,
                    "leechers": leechers,
                    "link": self._do_get_link(torrent_link),
                    "magnet_link": magnet_link,
                })
            except:
                pass
            if self.api.stop_search:
                return

        self.api.log("start5")

        if not self.api.stop_search:
            try:
                if pager:
                    spans = self.api.find_elements(pager, "span")
                    i = 0
                    while i < len(spans) and spans[i].prop('class') != 'pagercurrent':
                        i += 1
                    i += 1
                    if i < len(spans):
                        link = self.api.find_elements(spans[i], "a")[0]
                        link = urllib.basejoin(href, link.prop('href'))
                        self.run_search(pattern, param, link)
            except:
                pass

        self.api.log("start6")

    def _do_get_link(self, torrent_link):
        itemtree = libxml2.htmlParseFile(torrent_link, "utf-8")
        return urllib.basejoin(torrent_link, self.api.find_elements(itemtree.getRootElement(), "img", src="images/download.gif")[0].parent.prop("href"))
