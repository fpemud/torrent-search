#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-


import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import time
import httplib2


class xtremespeedsPlugin:

    def __init__(self, api):
        self.api = api

    def try_login(self):
        c = httplib2.Http()
        resp, content = c.request("http://xtremespeeds.net/")
        init_cookie = self.api.parse_cookie(resp['set-cookie'])
        username, password = self.api.get_credential
        data = urllib.parse.urlencode(
            {'username': username, 'password': password})
        headers = {'Content-type': 'application/x-www-form-urlencoded',
                   'Cookie': resp['set-cookie'], "User-Agent": "Python-httplib2/$Rev$"}
        resp, content = c.request(
            "http://xtremespeeds.net/takelogin.php", "POST", data, headers)
        if resp.status == 302 and 'set-cookie' in resp:
            return init_cookie+"; "+self.api.parse_cookie(resp['set-cookie'])+"; ts_username="+username
        else:
            return None

    def run_search(self, pattern, param, href=None):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        http = httplib2.Http()
        if href == None:
            href = "http://xtremespeeds.net/browse.php"
            headers = {'Content-type': 'application/x-www-form-urlencoded',
                       'Cookie': self.api.get_login_cookie, "User-Agent": "Python-httplib2/$Rev$"}
            data = urllib.parse.urlencode(
                {'do': 'search', 'keywords': pattern, 'search_type': 't_name', 'category': '0'})
            resp, content = http.request(href, 'POST', data, headers)
        else:
            headers = {'Cookie': self.api.get_login_cookie,
                       "User-Agent": "Python-httplib2/$Rev$"}
            resp, content = http.request(href, 'POST', headers=headers)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        try:
            a = self.api.find_elements(
                tree.getRootElement(), "a", **{'class': 'current'})[0]
            data = a.prop('title')
            i = len(data)-1
            while data[i] in "0123456789":
                i -= 1
            api_notify_results_total_count(eval(data[i+1:]))
        except:
            pass
        restable = self.api.find_elements(
            tree.getRootElement(), "table", id="sortabletable")[0]
        lines = self.api.find_elements(restable, "tr")[1:]
        for i in lines:
            try:
                category, name, torrent_link, comments, size, snatched, seeders, leechers, uploader = self.api.find_elements(
                    i, "td")
                label = self.api.find_elements(name, "a")[0].getContent()
                date = self.api.find_elements(
                    name, "div")[0].getContent().rstrip().lstrip().split(' ')[0]
                date = time.strptime(date, "%m-%d-%Y")
                date = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
                torrent_link = self.api.find_elements(
                    torrent_link, "a")[0].prop('href')
                size = size.getContent().rstrip().lstrip()
                seeders = eval(seeders.getContent().rstrip().lstrip())
                leechers = eval(leechers.getContent().rstrip().lstrip())
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
            if self.stop_search:
                return
        if not self.stop_search:
            try:
                next_link = None
                pager = self.api.find_elements(
                    tree.getRootElement(), "div", id="navcontainer_f")[0]
                links = self.api.find_elements(pager, "a")
                for i in links:
                    if i.getContent() == ">":
                        next_link = i
                        break
                if next_link:
                    self.run_search(pattern, param, urllib.basejoin(
                        href, next_link.prop('href')))
            except:
                pass
