#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-


import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import time
import httplib2


class Torrent411Plugin:

    def __init__(self, api):
        self.api = api

    def try_login(self):
        c = httplib2.Http()
        username, password = self.api.get_credential
        username = username
        data = urllib.parse.urlencode(
            {'username': username, 'password': password})
        headers = {'Content-type': 'application/x-www-form-urlencoded',
                   'User-Agent': 'torrent-search'}
        resp, content = c.request(
            "http://www.torrent411.com/account-login.php", "POST", data, headers)
        if "set-cookie" in resp and 'pass=null;' not in resp['set-cookie']:
            return resp["set-cookie"]
        else:
            return None

    def run_search(self, pattern, param, href=None):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        if href == None:
            href = "http://www.torrent411.com/search/" + \
                urllib.parse.quote_plus(pattern)
        resp, content = self.api.http_queue_request(href)
        content = content.decode("latin-1")[0].decode("utf-8")[0]
        tree = libxml2.htmlParseDoc(content, "utf-8")
        pager = self.api.find_elements(self.api.find_elements(
            tree.getRootElement(), "table", **{'class': 'NB-frame'})[1], "p")[0]
        try:
            b = self.api.find_elements(pager, "b")[-1]
            data = b.getContent()
            i = len(data)-1
            while data[i] in "012346789":
                i -= 1
            api_notify_results_total_count(eval(data[i+1:]))
        except:
            pass
        restable = self.api.find_elements(pager.next.__next__, "table")[0]
        restable = self.api.find_elements(restable, "table")[1]
        body = self.api.find_elements(restable, "tbody")[0]
        lines = self.api.find_elements(body, "tr", 1)
        for i in lines:
            try:
                cat, link, a, date, b, c, d, e, f, g, h, i, size, j, seeders, leechers = self.api.find_elements(
                    i, "td")
                date = date.getContent().replace(chr(194)+chr(160)+"at"+chr(194)+chr(160), " ")
                date = time.strptime(date, "%Y-%m-%d %H:%M:%S")
                date = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
                size = size.getContent().replace(chr(194)+chr(160), " ")
                seeders = eval(seeders.getContent())
                leechers = eval(leechers.getContent())
                link = self.api.find_elements(link, "a")[0]
                label = link.prop('title')
                link = urllib.basejoin(
                    "http://www.torrent411.com", link.prop('href'))
                resp, content = self.api.http_queue_request(link)
                content = content.decode("latin-1")[0].decode("utf-8")[0]
                itemtree = libxml2.htmlParseDoc(content, "utf-8")
                table = self.api.find_elements(
                    itemtree.getRootElement(), "table", **{'cellpadding': '3'})[1]
                desc, name, torrent, cat, siz, hashvalue = self.api.find_elements(table, "tr")[
                    :6]
                torrent = self.api.find_elements(torrent, "a")[0].prop('href')
                hashvalue = self.api.find_elements(
                    hashvalue, "td")[1].getContent()
                api_notify_one_result({
                    "id": "",
                    "label": label,
                    "date": date,
                    "size": size,
                    "seeders": seeders,
                    "leechers": leechers,
                    "link": torrent,
                    "hashvalue": hashvalue,
                })
            except:
                pass
            if self.stop_search:
                return
        if not self.stop_search:
            try:
                links = self.api.find_elements(pager, "a")
                next_link = None
                for i in links:
                    if i.getContent() == "Next"+chr(194)+chr(160)+">>":
                        next_link = i
                if next_link:
                    link = urllib.basejoin(
                        "http://www.torrent411.com", next_link.prop('href'))
                    self.run_search(pattern, param, link)
            except:
                pass
