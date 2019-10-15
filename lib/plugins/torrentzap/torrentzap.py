#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-


import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import httplib2


class TorrentzapPlugin:

    def __init__(self, api):
        self.api = api

    def _parseDate(self, data):
        day, month, year = data.split(" ")
        while day[0] == "0":
            day = day[1:]
        day = eval(day)
        month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
                 "Aug", "Sep", "Oct", "Nov", "Dec"].index(month)+1
        year = eval(year)
        return datetime.date(year, month, day)

    def run_search(self, pattern, param, page=1, href=None):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        if href == None:
            href = "http://www.torrentzap.com/search.php?q=" + \
                urllib.parse.quote_plus(pattern)
        c = httplib2.Http()
        resp, content = c.request(href)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        try:
            td = self.api.find_elements(
                tree.getRootElement(), "td", id="content_cap_tab_cont")[0]
            data = td.getContent()
            i = data.index('(')
            data = data[i+1:]
            i = data.index(' ')
            api_notify_results_total_count(max(eval(data[:i])-5, 0))
        except:
            pass
        restable = self.api.find_elements(self.api.find_elements(
            tree.getRootElement(), "div", **{'class': 'listing'})[0], "table")[0]
        lines = self.api.find_elements(restable, "tr")[1:]
        for i in lines:
            try:
                date, label, links, size, seeders, leechers, health = self.api.find_elements(
                    i, "td", 1)
                date = self._parseDate(date.getContent())
                link = self.api.find_elements(label, "a")[0]
                label = label.getContent().rstrip().lstrip()
                link = urllib.basejoin(href, link.prop('href'))
                size = size.getContent().upper()
                j = 0
                while j < len(size) and size[j] in "0123456789.":
                    j += 1
                if j < len(size):
                    size = size[:j]+" "+size[j:]
                seeders = eval(seeders.getContent())
                leechers = eval(leechers.getContent())

                reflink, magnet = self._parseLinks(link)

                api_notify_one_result({
                    "id": "",
                    "label": label,
                    "date": date,
                    "size": size,
                    "seeders": seeders,
                    "leechers": leechers,
                    "link": reflink,
                    "magnet_link": magnet,
                })
            except:
                pass
            if self.stop_search:
                return
        if not self.stop_search:
            try:
                div = self.api.find_elements(
                    tree.getRootElement(), "div", **{'class': 'search_stat'})[0]
                link = div.lastElementChild()
                if link.name == "a":
                    url = urllib.basejoin(href, link.prop('href'))
                    self.run_search(pattern, 0, url)
            except:
                pass

    def _parseLinks(self, url):
        c = httplib2.Http()
        resp, content = c.request(url)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        reflink = urllib.basejoin(url, self.api.find_elements(tree.getRootElement(
        ), "img", src="http://static.torrentzap.com/images/b_down.png")[0].parent.prop("href"))
        try:
            magnet = self.api.find_elements(self.api.find_elements(
                tree.getRootElement(), "span", id="magnet")[0], "a")[0].prop('href')
            if "&" in magnet:
                magnet = magnet[:magnet.index("&")]
        except:
            magnet = None
        return reflink, magnet
