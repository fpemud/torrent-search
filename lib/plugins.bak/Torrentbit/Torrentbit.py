#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-


import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime


class TorrentbitPlugin:

    def __init__(self, api):
        self.api = api

    def run_search(self, pattern, param, page=1, href=None):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        if href is None:
            href = "http://www.torrentbit.net/search/?torrent=" + urllib.parse.quote_plus(pattern)
        resp, content = self.api.http_queue_request(href)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        td = self.api.find_elements(tree.getRootElement(), "td", id="main")[0]
        try:
            h = self.api.find_elements(td, "h1")[0]
            data = h.getContent().rstrip().lstrip()
            i = len(data)-1
            while i >= 0 and data[i] not in "0123456789":
                i -= 1
            j = i
            while j >= 0 and data[j] in "0123456789":
                j -= 1
            api_notify_results_total_count(eval(data[j+1:i+1]))
        except:
            pass
        div = self.api.find_elements(self.api.find_elements(
            td, "div", **{'class': 't_list'})[0], "tbody")[0]
        lines = self.api.find_elements(div, "tr")
        for i in lines:
            try:
                date, descr, title, size, rts, seeders, leechers, dl, cat = self.api.find_elements(
                    i, "td")
                date = date.getContent().replace(chr(194)+chr(160), " ")
                day, month, year = date.split(" ")
                while day[0] == "0":
                    day = day[1:]
                day = eval(day)
                month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
                         "Aug", "Sep", "Oct", "Nov", "Dec"].index(month)+1
                year = eval(year)
                date = datetime.date(year, month, day)
                link = self.api.find_elements(title, "a")[0]
                label = link.getContent()
                link = urllib.basejoin(
                    href, urllib.parse.quote(link.prop('href')))
                size = size.getContent().replace(chr(194)+chr(160), " ")
                seeders = eval(seeders.getContent())
                leechers = eval(leechers.getContent())
                resp, content = self.api.http_queue_request(link)
                itemtree = libxml2.htmlParseDoc(content, "utf-8")
                table = self.api.find_elements(
                    itemtree.getRootElement(), "table", **{'class': 'tor_item'})[0]
                thislines = self.api.find_elements(table, "tr")
                for j in thislines:
                    if self.api.find_elements(j, "th")[0].getContent() == "Download torrent:":
                        itemlink = urllib.basejoin(
                            link, self.api.find_elements(j, "a")[0].prop('href'))
                        break
                hashvalue = self.api.find_elements(
                    lines[4], "td")[0].getContent()
                magnet = "magnet:?xt=urn:btih:"+hashvalue
                api_notify_one_result({
                    "id": "",
                    "label": label,
                    "date": date,
                    "size": size,
                    "seeders": seeders,
                    "leechers": leechers,
                    "link": itemlink,
                    "magnet_link": magnet,
                })
            except:
                pass
            if self.api.stop_search:
                return
        if not self.api.stop_search:
            try:
                try:
                    pager = self.api.find_elements(
                        tree.getRootElement(), "div", id="pagination")[0]
                except:
                    pager = None
                if pager:
                    nextlink = self.api.find_elements(
                        pager, "a", title="Next page")
                    if nextlink:
                        nextlink = urllib.basejoin(
                            href, nextlink[0].prop('href'))
                        self.run_search(pattern, param, 1, nextlink)
            except:
                pass
