#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime


class NyaaTorrentsPlugin:

    def __init__(self, api):
        self.api = api

    def run_search(self, pattern, param, href=None):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        if href is None:
            href = "http://www.nyaatorrents.org/?page=search&term=" + \
                urllib.parse.quote_plus(pattern)
        resp, content = self.api.http_queue_request(href)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        try:
            span = self.api.find_elements(
                tree.getRootElement(), "span", **{'class': 'notice'})[0]
            data = span.getContent()
            i = data.index(" ")
            api_notify_results_total_count(eval(data[:i]))
        except:
            pass
        restable = self.api.find_elements(
            tree.getRootElement(), "table", **{'class': 'tlist'})[0]
        lines = self.api.find_elements(restable, "tr")[1:]
        for i in lines:
            try:
                cells = self.api.find_elements(i, "td")
                name = cells[1]
                torrent_link = cells[2]
                size = cells[3]
                link = self.api.find_elements(name, "a")[0]
                label = link.getContent().rstrip().lstrip()
                link = link.prop('href')
                torrent_link = self.api.find_elements(
                    torrent_link, "a")[0].prop('href')
                size = size.getContent().replace('i', '')
                try:
                    seeders = eval(cells[4].getContent())
                except:
                    seeders = -1
                try:
                    leechers = eval(cells[5].getContent())
                except:
                    leechers = -1
                resp, content = self.api.http_queue_request(link)
                itemtree = libxml2.htmlParseDoc(content, "utf-8")
                tds = self.api.find_elements(itemtree.getRootElement(), "td")
                date = ""
                for j in tds:
                    if j.getContent() == "Date:":
                        date = j.next.getContent()
                j = date.index(",")
                date = date[:j]
                month, day, year = date.split(" ")
                month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
                         "Aug", "Sep", "Oct", "Nov", "Dec"].index(month)+1
                while day[0] == "0":
                    day = day[1:]
                day = eval(day)
                year = eval(year)
                date = datetime.date(year, month, day)
                api_notify_one_result({
                    "id": "",
                    "label": label,
                    "date": date,
                    "size": size,
                    "seeders": seeders,
                    "leechers": leechers,
                    "link": torrent_link,
                })
            except:
                pass
            if self.api.stop_search:
                return
        if not self.api.stop_search:
            try:
                pager = self.api.find_elements(
                    tree.getRootElement(), "table", **{'class': 'tlistpages'})[0]
                links = self.api.find_elements(
                    pager, "a", **{'class': 'page'})
                next_link = None
                for i in links:
                    if i.getContent() == ">":
                        next_link = i
                        break
                url = next_link.prop('href')
                self.run_search(pattern, param, url)
            except:
                pass
