#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import TorrentSearch
import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import os
import time
import httplib2
from TorrentSearch import htmltools


class MononokeBTPluginResult(TorrentSearch.Plugin.PluginResult):
    def __init__(self, label, date, size, seeders, leechers, torrent_link, hashvalue):
        self.torrent_link = torrent_link
        TorrentSearch.Plugin.PluginResult.__init__(
            self, label, date, size, seeders, leechers, hashvalue=hashvalue)

    def _do_get_link(self):
        return self.torrent_link


class MononokeBTPlugin(TorrentSearch.Plugin.Plugin):
    def try_login(self):
        c = httplib2.Http()
        username, password = self.api.get_credential
        data = urllib.parse.urlencode(
            {'username': username, 'password': password, 'returnto': '/'})
        headers = {'Content-type': 'application/x-www-form-urlencoded',
                   'User-Agent': 'torrent-search'}
        resp, content = c.request(
            "http://mononoke-bt.org/takelogin.php", "POST", data, headers)
        if resp.status == 302:
            return resp["set-cookie"]
        else:
            return None

    def run_search(self, pattern, href=None, page=0):
        if href == None:
            href = "http://mononoke-bt.org/browse2.php?search=" + \
                urllib.parse.quote_plus(pattern)
        resp, content = self.api.http_queue_request(
            href, headers={'Cookie': self.api.parse_cookie(self.api.get_login_cookie)})
        tree = libxml2.htmlParseDoc(content, "utf-8")
        pager = htmltools.find_elements(tree.getRootElement(
        ), "div", **{'class': 'animecoversfan'})[0].parent.__next__
        try:
            data = htmltools.find_elements(pager, "b")[-1].getContent()
            i = len(data)-1
            while data[i] in "0123456789":
                i -= 1
            self.results_count = eval(data[i+1:])
        except:
            pass
        restable = pager.next.__next__
        lines = htmltools.find_elements(restable, "tr", 1)[1:-2]
        for i in lines:
            try:
                cells = htmltools.find_elements(i, "td")
                team, show, stype, name, torrent_link, nbfiles, nbcmt, rate, date, size, views, dl, seeders, leechers, ratio = cells
                link = htmltools.find_elements(name, "a")[0]
                label = link.getContent()
                link = urllib.basejoin(href, link.prop('href'))
                torrent_link = urllib.basejoin(href, htmltools.find_elements(
                    torrent_link, "a")[0].prop('href'))+"&r=1"
                date = htmltools.find_elements(date, "nobr")[
                    0].children.getContent()
                date = time.strptime(date, "%Y-%m-%d")
                date = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
                strsize = ""
                cell = size.children
                while cell:
                    if cell.name == "text":
                        if strsize:
                            strsize += " "
                        strsize += cell.getContent().upper()
                    cell = cell.__next__
                size = strsize.replace('O', 'B')
                seeders = eval(seeders.getContent())
                leechers = eval(leechers.getContent())
                resp, content = self.api.http_queue_request(
                    link, headers={'Cookie': self.api.parse_cookie(self.api.get_login_cookie)})
                itemtree = libxml2.htmlParseDoc(content, "utf-8")
                tds = htmltools.find_elements(itemtree.getRootElement(), "td")
                hashvalue = None
                for j in tds:
                    if j.getContent() == "Info hash":
                        hashvalue = j.next.next.getContent()
                self.api.notify_one_result(MononokeBTPluginResult(
                    label, date, size, seeders, leechers, torrent_link, hashvalue))
            except:
                pass
            if self.stop_search:
                return
        if not self.stop_search:
            try:
                b = htmltools.find_elements(pager, "b")[-1]
                if b.parent.name == "a":
                    url = "http://mononoke-bt.org/browse2.php?search=%s&page=%d" % (
                        urllib.parse.quote_plus(pattern), page+1)
                    self.run_search(pattern, url, page+1)
            except:
                pass
