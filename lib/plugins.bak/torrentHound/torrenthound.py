#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-


import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import time
import httplib2


class TorrentHoundTorrentPlugin:

    def __init__(self, api):
        self.api = api

    def run_search(self, pattern, param, page=1, href=None):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        if href is None:
            href = "http://www.torrenthound.com/search/" + \
                urllib.parse.quote_plus(pattern)
        resp, content = self.api.http_queue_request(href)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        try:
            count_div = self.api.find_elements(
                tree.getRootElement(), "span", id="subsearch")[0]
            data = count_div.getContent()
            i = data.index(' ')
            api_notify_results_total_count(eval(data[:i]))
        except:
            pass
        restable = self.api.find_elements(self.api.find_elements(
            tree.getRootElement(), "div", id="maindiv")[0], "table")[1]
        lines = self.api.find_elements(restable, "tr")[1:]
        for i in lines:
            try:
                link, date, size, seeders, leechers, health = self.api.find_elements(
                    i, "td")
                link = self.api.find_elements(link, "a")[0]
                label = ""
                j = link.children
                while j and j.name != "br":
                    label += j.getContent()
                    j = j.__next__
                label_lines = label.splitlines()
                label = ""
                for j in label_lines:
                    if j:
                        label += j
                label = label.rstrip().lstrip()
                link = urllib.basejoin(href, link.prop('href'))
                date = self._parseDate(self.api.find_elements(date, "span")[
                                       0].children.getContent().rstrip().lstrip())
                size = size.getContent().upper()
                data = self.api.find_elements(seeders, "span")[
                    0].getContent().lstrip().rstrip()
                j = 0
                while j < len(data) and data[j] in "0123456789":
                    j += 1
                seeders = eval(data[:j])
                data = self.api.find_elements(leechers, "span")[
                    0].getContent().lstrip().rstrip()
                j = 0
                while j < len(data) and data[j] in "0123456789":
                    j += 1
                leechers = eval(data[:j])
                resp, content = self.api.http_queue_request(link)
                itemtree = libxml2.htmlParseDoc(content, "utf-8")
                div = self.api.find_elements(
                    itemtree.getRootElement(), "div", id="torrent")[0]
                link = urllib.basejoin(
                    href, self.api.find_elements(div, "a")[0].prop('href'))
                try:
                    infotable = self.api.find_elements(
                        itemtree.getRootElement(), "table", **{'class': 'infotable'})[0]
                    hashline = self.api.find_elements(
                        itemtree.getRootElement(), "tr")[8]
                    hashvalue = self.api.find_elements(
                        hashline, "td")[1].getContent()
                except:
                    hashvalue = None
                try:
                    tmenu = self.api.find_elements(
                        itemtree.getRootElement(), "ul", id="tmenu")[0]
                    nb_comments_cell = self.api.find_elements(tmenu, "li")[2]
                    data = nb_comments_cell.getContent()
                    j = data.index("(")+1
                    data = data[j:]
                    j = data.index(")")
                    nb_comments = int(data[:j])
                except:
                    nb_comments = 0
                api_notify_one_result({
                    "id": "",
                    "label": label,
                    "date": date,
                    "size": size,
                    "seeders": seeders,
                    "leechers": leechers,
                    "link": link,
                    "hashvalue": hashvalue,
                    "nb_comments": nb_comments,
                })
            except:
                pass
            if self.api.stop_search:
                return
        if not self.api.stop_search:
            try:
                try:
                    pager = restable.parent.next.__next__
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
                        self.run_search(pattern, param, pn, urllib.basejoin(
                            href, pages[i].prop('href')))
            except:
                pass

    def load_comments(self, result_id):
        hashvalue = result_id

        res = []
        url = "http://www.torrenthound.com/hash/%s/comments" % hashvalue
        c = httplib2.Http()
        resp, content = c.request(url)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        comments_list = []
        for i in self.api.find_elements(self.api.find_elements(tree.getRootElement(), "div", id="pcontent")[0], "div", **{'class': 'c'})[:-1]:
            comments_list.insert(0, i)
        for i in comments_list:
            content = self.api.find_elements(
                i, "div", **{'class': 'middle'})[0].getContent()
            date = self._parseCommentDate(self.api.find_elements(self.api.find_elements(
                i, "div", **{'class': 'top'})[0], "p")[0].children.getContent()[7:-6])
            res.append({
                "content": content,
                "date": date,
            })
        return res

    def _do_load_filelist(self, result_id):
        hashvalue = result_id

        res = []
        url = "http://www.torrenthound.com/hash/%s/files" % hashvalue
        c = httplib2.Http()
        resp, content = c.request(url)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        for i in self.api.find_elements(self.api.find_elements(tree.getRootElement(), "div", id="pcontent")[0], "tr", **{'class': 'filename'}):
            filename, size = self.api.find_elements(i, "td")
            filename = filename.getContent()
            size = size.getContent()
            res.append({
                "filename": filename,
                "size": size.upper()
            })
        return res

    def _parseCommentDate(self, date):
        try:
            days_str = ["Monday", "Tuesday", "Wednesday",
                        "Thursday", "Friday", "Saturday", "Sunday"]
            if date in days_str:
                days_int = days_str.index(date)+1
                cur_day = int(time.strftime("%u"))
                diff_days = 0
                while days_int != cur_day:
                    diff_days += 1
                    days_int += 1
                    if days_int == 8:
                        days_int = 1
                year = int(time.strftime('%Y'))
                month = int(time.strftime('%m'))
                day = int(time.strftime('%d'))
                res = datetime.date(year, month, day)
                res = res-datetime.timedelta(diff_days)
            else:
                res = self.plugin._parseDate(date)
        except:
            print("Failed converting date: "+date)
            res = None
        return res

    def _parseDate(self, data):
        day, month, year = data.split(' ')
        i = 0
        while i < len(day) and day[i] in "0123456789":
            i += 1
        day = eval(day[:i])
        month = ["Jan,", "Feb,", "Mar,", "Apr,", "May,", "Jun,",
                 "Jul,", "Aug,", "Sep,", "Oct,", "Nov,", "Dec,"].index(month)+1
        year = eval("20"+year)
        return datetime.date(year, month, day)
