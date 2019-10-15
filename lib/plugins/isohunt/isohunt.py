#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import os
import httplib2
import time
import http.client


class isoHuntPlugin(TorrentSearch.Plugin.Plugin):

    def __init__(self, api):
        self.api = api

    def _parseDate(self, data):
        year, month, day = data.split("-")
        while month[0] == "0":
            month = month[1:]
        while day[0] == "0":
            day = day[1:]
        return datetime.date(eval(year), eval(month), eval(day))

    def run_search(self, pattern, param, href=None):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        if href == None:
            href = "http://isohunt.com/torrents/?ihq=" + \
                urllib.parse.quote_plus(pattern)
        resp, content = self.api.http_queue_request(href)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        pager = self.api.find_elements(
            tree.getRootElement(), "table", **{'class': 'pager'})[0]
        try:
            b = self.api.find_elements(pager, "b")[0]
            api_notify_results_total_count(eval(b.getContent()))
        except:
            pass
        restable = self.api.find_elements(
            tree.getRootElement(), "table", id="serps")[0]
        lines = self.api.find_elements(restable, "tr")[1:]
        for i in lines:
            try:
                category, age, links, size, seeders, leechers = self.api.find_elements(
                    i, "td")
                size = size.getContent()
                try:
                    seeders = eval(seeders.getContent())
                except:
                    seeders = 0
                try:
                    leechers = eval(leechers.getContent())
                except:
                    leechers = 0
                links = self.api.find_elements(links, "a")
                link = links[1]
                br = self.api.find_elements(link, "br")
                if br:
                    label = ""
                    node = br[0].__next__
                    while node:
                        label += node.getContent()
                        node = node.__next__
                else:
                    label = link.getContent()
                link = urllib.basejoin(href, link.prop('href'))
                if len(links) == 3:
                    link = link.replace('/download/', '/torrent_details/')
                age = age.getContent()
                unit = age[-1]
                value = eval(age[:-1])
                if unit == "w":
                    value *= 7
                date = datetime.date.today()-datetime.timedelta(value)
                resp, content = self.api.http_queue_request(link)
                itemtree = libxml2.htmlParseDoc(content, "utf-8")
                torrent_link = None
                for i in self.api.find_elements(itemtree.getRootElement(), "a"):
                    if i.getContent() == " Download .torrent":
                        torrent_link = i
                torrent_link = urllib.basejoin(link, torrent_link.prop('href'))
                span = self.api.find_elements(
                    itemtree.getRootElement(), "span", id="SL_desc")[0]
                data = span.getContent()[11:]
                j = data.index(" ")
                hashvalue = data[:j]
                api_notify_one_result({
                    "id": "",
                    "label": label,
                    "date": date,
                    "size": size,
                    "seeders": seeders,
                    "leechers": leechers,
                    "link": torrent_link,
                    "hashvalue": hashvalue,
                })
            except:
                pass
            if self.stop_search:
                return
        if not self.stop_search:
            try:
                link = self.api.find_elements(pager, "a", title="Next page")
                if link:
                    self.run_search(pattern, param, urllib.basejoin(
                        href, link[0].prop('href')))
            except:
                pass
