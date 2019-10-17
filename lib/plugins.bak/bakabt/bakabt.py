#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import httplib2


class BakaBTPlugin:

    def __init__(self, api):
        self.api = api

    def try_login(self):
        c = httplib2.Http()
        username, password = self.api.get_credential
        resp, content = c.request('http://www.bakabt.com/login.php')
        data = urllib.parse.urlencode(
            {'username': username, 'password': password, 'returnto': '/index.php'})
        headers = {'Content-type': 'application/x-www-form-urlencoded',
                   'Cookie': resp['set-cookie']}
        resp, content = c.request("http://www.bakabt.com/login.php", "POST", data, headers)
        if 'set-cookie' in resp and 'uid=' in resp['set-cookie']:
            return self.api.parse_cookie(resp['set-cookie'])
        else:
            return None

    def run_search(self, pattern, param, page_url=''):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        http = httplib2.Http()
        headers = {'Cookie': self.api.get_login_cookie}
        if page_url == "":
            page_url = "http://www.bakabt.com/browse.php?q=" + \
                urllib.parse.quote(pattern)
        resp, content = http.request(page_url, headers=headers)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        try:
            data = self.api.find_elements(self.api.find_elements(
                tree.getRootElement(), "div", **{'class': 'pager'})[0], "a")[-2].getContent()
            i = len(data)-1
            while i >= 0 and data[i] in "0123456789":
                i -= 1
            api_notify_results_total_count(eval(data[i+1:]))
        except:
            pass
        results_table = self.api.find_elements(
            tree.getRootElement(), "table", **{'class': 'torrents'})[0]
        lines = self.api.find_elements(results_table, "tr")[1:]
        is_alt = False
        for i in range(len(lines)):
            try:
                line = lines[i]
                if "torrent_alt" in line.prop('class') and not is_alt:
                    is_alt = True
                    continue
                if "torrent_alt" not in line.prop('class'):
                    is_alt = False

                cells = self.api.find_elements(line, "td")
                if len(cells) == 6:
                    category, details, comments, date, size, transfers = cells
                else:
                    details, comments, date, size, transfers = cells
                day, month, year = date.getContent().replace("'", "").split(" ")
                day = eval(day)
                year = eval("20"+year)
                month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
                         'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].index(month)+1
                date = datetime.date(year, month, day)
                seeders, leechers = self.api.find_elements(transfers, "a")
                seeders = eval(seeders.getContent())
                leechers = eval(leechers.getContent())
                size = size.getContent()
                link = self.api.find_elements(details, "a")[0]
                label = link.getContent()
                link = urllib.basejoin(page_url, link.prop('href'))
                api_notify_one_result({
                    "id": "",
                    "label": label,
                    "date": date,
                    "size": size,
                    "seeders": seeders,
                    "leechers": leechers,
                    "link": self._do_get_link(link),
                })
            except:
                pass
            if self.api.stop_search:
                return
        if not self.api.stop_search:
            link = self.api.find_elements(self.api.find_elements(
                tree.getRootElement(), "div", **{'class': 'pager'})[0], "a")[-1]
            if link.prop('class') != 'selected':
                self.run_search(pattern, param, urllib.basejoin(
                    page_url, link.prop('href')))

    def _do_get_link(self, reflink):
        c = httplib2.Http()
        headers = {'Cookie': self.api.get_login_cookie()}
        resp, content = c.request(reflink, headers=headers)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        return urllib.basejoin(reflink, self.api.find_elements(tree.getRootElement(), "a", **{'class': 'download_link'})[0].prop('href'))
