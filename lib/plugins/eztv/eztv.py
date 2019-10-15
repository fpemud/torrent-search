#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime


class EZTVPlugin:

    def __init__(self, api):
        self.api = api

    def run_search(self, pattern, param):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        # TODO; Retrieve number of seeders and leechers when available
        href = "http://eztv.it/search/"
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        data = urllib.parse.urlencode(
            {'SearchString1': pattern, 'SearchString': '', "search": "Search"})
        resp, content = self.api.http_queue_request(href, "POST", data, headers)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        div = self.api.find_elements(tree.getRootElement(), "div", id="tooltip")[0]
        restable = div.nextElementSibling()
        try:
            count = len(self.api.find_elements(restable, "tr", 1, **{'class': 'forum_header_border'}))
            api_notify_results_total_count(count)
        except:
            pass
        lines = self.api.find_elements(restable, "tr", 1, **{'class': 'forum_header_border'})
        for i in lines:
            try:
                link = self.api.find_elements(
                    self.api.find_elements(i, "td")[1], "a")[0]
                label = link.getContent()
                link = urllib.basejoin(href, link.prop('href'))
                resp, content = self.api.http_queue_request(link)
                itemtree = libxml2.htmlParseDoc(content, "utf-8")
                torrent_link = self.api.find_elements(
                    itemtree.getRootElement(), "a", **{'class': 'download_1'})[0].prop('href')
                magnet_link = self.api.find_elements(
                    itemtree.getRootElement(), "a", **{'class': 'magnet'})[0].prop('href')
                data = str(itemtree)
                j = data.index("Filesize:")
                data = data[j:]
                j = data.index(" ")+1
                data = data[j:]
                j = data.index("B")+1
                size = data[:j]
                data = str(itemtree)
                j = data.index("Released:")
                data = data[j:]
                j = data.index(" ")+1
                data = data[j:]
                j = data.index("<")
                date = data[:j]
                day, month, year = date.split(" ")
                day = eval(day[:-2])
                month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
                         "Aug", "Sep", "Oct", "Nov", "Dec"].index(month)+1
                year = eval(year)
                date = datetime.date(year, month, day)
                api_notify_one_result({
                    "id": "",
                    "label": label,
                    "date": date,
                    "size": size,
                    "link": torrent_link,
                    "magnet_link": magnet_link,
                })
            except:
                pass
            if self.stop_search:
                return
