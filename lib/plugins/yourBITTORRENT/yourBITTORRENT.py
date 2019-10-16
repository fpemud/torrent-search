#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-


import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import httplib2


class yourBITTORRENTTorrentPlugin:

    def __init__(self, api):
        self.api = api

    def _parseDate(self, data):
        if data == "Yesterday":
            data = 1
        else:
            try:
                i = data.index("d")
                data = eval(data[:i])
            except:
                data = 0
        return datetime.date.today()-datetime.timedelta(data)

    def run_search(self, pattern, param, page=1, href=None):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        if href is None:
            href = "http://www.yourbittorrent.com/?q=" + \
                urllib.parse.quote_plus(pattern)
        c = httplib2.Http()
        resp, content = c.request(href)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        try:
            count = int(self.api.find_elements(self.api.find_elements(tree.getRootElement(
            ), "div", style="float:right;margin-top:15px")[0], "b")[2].getContent().rstrip().lstrip())
            api_notify_results_total_count(count)
        except:
            pass
        lines = []
        for i in self.api.find_elements(tree.getRootElement(), "td", id="n"):
            lines.append(i.parent)
        for i in lines:
            try:
                links, date, size, seeders, leechers, health = self.api.find_elements(
                    i, "td")
                dlink, ulink = self.api.find_elements(links, "a")
                filelist = []
                poster = None
                try:
                    c = httplib2.Http()
                    resp, content = c.request(
                        urllib.basejoin(href, ulink.prop('href')))
                    itemtree = libxml2.htmlParseDoc(content, "utf-8")
                    table = self.api.find_elements(self.api.find_elements(
                        itemtree.getRootElement(), "div", id="content")[0], "table")[0]
                    line = self.api.find_elements(table, "tr")[1]
                    cell = self.api.find_elements(line, "td")[3]
                    hashvalue = cell.getContent()
                    h3s = self.api.find_elements(
                        itemtree.getRootElement(), "h3")
                    files_h3 = None
                    for h3 in h3s:
                        if h3.getContent() == "Files":
                            files_h3 = h3
                    if files_h3:
                        for file_line in self.api.find_elements(files_h3.__next__, "tr")[1:]:
                            try:
                                filepix, filename, filesize = self.api.find_elements(
                                    file_line, "td")
                                filename = filename.getContent()
                                filesize = filesize.getContent()
                                filelist.append({
                                    "filename": filename,
                                    "size": filesize,
                                })
                            except:
                                pass
                    h1s = self.api.find_elements(
                        itemtree.getRootElement(), "h1")
                    cover_h1 = None
                    for h1 in h1s:
                        if h1.getContent() == "Cover Art":
                            cover_h1 = h1
                    if cover_h1:
                        try:
                            poster = self.api.find_elements(
                                cover_h1.parent, "img")[0].prop("src")
                        except:
                            pass
                except:
                    hashvalue = None

                label = ulink.getContent()
                link = urllib.basejoin(href, dlink.prop('href'))
                size = size.getContent().upper()
                seeders = eval(seeders.getContent())
                leechers = eval(leechers.getContent())
                date = self._parseDate(date.getContent())
                api_notify_one_result({
                    "id": "",
                    "label": label,
                    "date": date,
                    "size": size,
                    "seeders": seeders,
                    "leechers": leechers,
                    "link": link,
                    "hashvalue": hashvalue,
                    "filelist": filelist,
                    "poster": poster,
                })
            except:
                pass
            if self.stop_search:
                return
        if not self.stop_search:
            try:
                try:
                    pager = self.api.find_elements(
                        tree.getRootElement(), "div", **{"class": "pagnation_l"})[0]
                except:
                    pager = None
                if pager:
                    pages = self.api.find_elements(pager, "a")
                    i = 0
                    must_continue = False
                    while i < len(pages) and not must_continue:
                        p = pages[i]
                        try:
                            pn = eval(pages[i].getContent())
                            if pn > page:
                                must_continue = True
                            else:
                                i += 1
                        except:
                            i += 1
                    if must_continue:
                        url = "http://www.yourbittorrent.com/?q=%s&page=%d" % (
                            urllib.parse.quote_plus(pattern), pn)
                        self.run_search(pattern, param, pn, url)
            except:
                pass
