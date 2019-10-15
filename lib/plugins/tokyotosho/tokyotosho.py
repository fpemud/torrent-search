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


class TokyoToshokanPlugin:

    def __init__(self, api):
        self.api = api

    def run_search(self, pattern, param, page_url=""):
        self.api_notify_results_total_count = param["notify-results-total-count"]
        self.api_notify_one_result = param["notify-one-result"]

        if page_url == "":
            page_url = "http://tokyotosho.info/search.php?terms=" + \
                urllib.parse.quote_plus(pattern)
        resp, content = self.api.http_queue_request(page_url)
        tree = libxml2.htmlParseDoc(content, "utf-8")

        results_table = self.api.find_elements(
            tree.getRootElement(), "table", **{'class': 'listing'})[0]
        results = self.api.find_elements(
            results_table, "a", **{'type': "application/x-bittorrent"})
        results = self.api.find_elements(results_table, "tr", 1)
        self.api_notify_results_total_count(len(results) / 2)

        for i in range(len(results)/2):
            try:
                self._parse_result(page_url, results[2*i+(len(results) % 2)])
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

    def _parse_result(self, url, result):
        links = self.api.find_elements(result, "a")
        if len(links) == 3:
            category, result_link, details_link = links
        else:
            category, result_link, website, details_link = links
        label = result_link.getContent()
        details_link = urllib.basejoin(url, details_link.prop('href'))
        resp, content = self.api.http_queue_request(details_link)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        infotable = self.api.find_elements(
            tree.getRootElement(), "div", **{'class': 'details'})[0]
        infolines = self.api.find_elements(infotable, "li")
        infodic = {}
        for i in range(len(infolines)/2):
            try:
                lab = infolines[2*i].getContent().rstrip().lstrip()
                val = infolines[2*i+1].getContent()
                infodic[lab] = val
            except:
                pass
        try:
            seeders = eval(infodic['Seeders:'])
        except:
            seeders = 1
        try:
            leechers = eval(infodic['Leechers:'])
        except:
            leechers = -1
        date = infodic['Date Submitted:']
        date = date.split(' ')[0]
        year, month, day = date.split('-')
        if day.startswith('0'):
            day = day[1:]
        if month.startswith('0'):
            month = month[1:]
        day = eval(day)
        month = eval(month)
        year = eval(year)
        date = datetime.date(year, month, day)
        size = infodic['Filesize:']
        i = 0
        while size[i] in "0123456789.":
            i += 1
        size = size[:i]+' '+size[i:]
        torrent_link = urllib.basejoin(url, result_link.prop('href'))

        self.api_notify_one_result({
            "id": "",
            "label": label,
            "date": date,
            "size": size,
            "seeders": seeders,
            "leechers": leechers,
            "link": torrent_link,
        })
