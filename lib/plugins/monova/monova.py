#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import libxml2
import datetime
import urllib.request
import urllib.parse
import urllib.error


class MonovaPlugin:

    def __init__(self, api):
        self.api = api

    def _formatSize(self, data):
        data = eval(data)
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        ui = 0
        while data >= 1024:
            ui += 1
            data /= 1024.
        return "%.1f %s" % (data, units[ui])

    def run_search(self, pattern, param):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        url = "http://www.monova.org/rss.php?search=" + \
            urllib.parse.quote(pattern)+"&order=added"
        resp, content = self.api.http_queue_request(url)
        tree = libxml2.parseDoc(content)
        results = self.api.find_elements(tree.getRootElement(), "item")
        api_notify_results_total_count(len(results))
        for i in results:
            title = self.api.find_elements(i, "title")[0].getContent()
            date = self.api.find_elements(i, "pubDate")[0].getContent()
            day, month, year = date.split(" ")[1:4]
            while day[0] == "0":
                day = day[1:]
            day = eval(day)
            year = eval(year)
            month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
                     'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].index(month)+1
            date = datetime.date(year, month, day)
            link = self.api.find_elements(i, "enclosure")[0]
            size = self._formatSize(link.prop('length'))
            torrent_link = link.prop('url')
            api_notify_one_result({
                "id": "",
                "label": title,
                "date": date,
                "size": size,
                "link": torrent_link,
            })
            if self.stop_search:
                return
