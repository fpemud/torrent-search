#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-


import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import httplib2
import http.client


class SUMOTorrentPlugin:

    def __init__(self, api):
        self.api = api

    def run_search(self, pattern, param, page=1, href=None):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        if href is None:
            href = "http://www.sumotorrent.com/searchResult.php?search=" + \
                urllib.parse.quote_plus(pattern)
        try:
            resp, content = self.api.http_queue_request(href)
        except httplib2.FailedToDecompressContent:
            if not self.api.stop_search:
                self.run_search(pattern, param, page, href)
            return
        tree = libxml2.htmlParseDoc(content, "utf-8")
        try:
            count_div = self.api.find_elements(self.api.find_elements(
                tree.getRootElement(), id="trait")[0].parent, "div")[0]
            data = count_div.getContent()
            i = data.index("(")+1
            data = data[i:]
            i = data.index(" ")
            data = data[:i]
            api_notify_results_total_count(eval(data))
        except:
            pass
        restable = self.api.find_elements(
            tree.getRootElement(), id="panel")[0].__next__
        while restable and restable.type != "element":
            restable = restable.__next__
        lines = self.api.find_elements(restable, "tr", 1)
        for i in lines[1:]:
            try:
                if i.hasProp('class') and not i.hasProp('id'):
                    cells = self.api.find_elements(i, "td", 1)
                    date, typ, name, comments, links, size, seeds, leeches, more = cells
                    date = self._parseDate(date.getContent().lstrip().rstrip())
                    refmagnet = urllib.basejoin(
                        href, self.api.find_elements(name, "a")[0].prop('href'))
                    name_link = self.api.find_elements(name, "a")[0]
                    details_url = urllib.basejoin(href, name_link.prop("href"))
                    name = name_link.getContent().lstrip().rstrip()
                    nb_comments_zone = self.api.find_elements(
                        comments, "strong")
                    nb_comments = 0
                    try:
                        if len(nb_comments_zone) == 1:
                            nb_comments = int(
                                nb_comments_zone[0].getContent().rstrip().lstrip())
                    except:
                        pass
                    size = size.getContent().lstrip().rstrip()
                    seeds = eval(seeds.getContent().lstrip().rstrip())
                    leeches = eval(leeches.getContent().lstrip().rstrip())

                    reflink = self.api.find_elements(links, "a")[0].prop('href')

                    self.api.notify_one_result({
                        "id": details_url,
                        "label": name,
                        "date": date,
                        "size": size,
                        "seeders": seeds,
                        "leechers": leechs,
                        "link": self._do_get_link(reflink),
                        "magnet_link": self._get_magnet(refmagnet),
                        "nb_comments": nb_comments,
                    })

            except:
                pass
            if self.api.stop_search:
                return
        if not self.api.stop_search:
            try:
                pager = self.api.find_elements(
                    tree.getRootElement(), id="pager")
                if pager:
                    pages = self.api.find_elements(pager[0], "a")
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
                        self.run_search(pattern, param, pn, pages[i].prop('href'))
            except:
                pass

    def load_filelist(self, result_id):
        details_url = result_id

        i = len(details_url)-1
        while details_url[i] != '/':
            i -= 1
        url = details_url[:i+1] + \
            urllib.parse.quote_plus(details_url[i+1:])
        res = []
        c = httplib2.Http()
        resp, content = c.request(url)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        try:
            table = self.api.find_elements(self.api.find_elements(
                tree.getRootElement(), "div", **{'class': 'torrentFiles'})[0], "tbody")[0]
            for i in self.api.find_elements(table, "tr", 1)[1:]:
                filename, size = self.api.find_elements(i, "td")
                filename = filename.getContent()
                size = size.getContent().replace('Bytes', 'B')
                res.append({
                    "filename": filename,
                    "size": size,
                })
        except:
            pass
        return res

    def load_comments(self, result_id):
        details_url = result_id

        i = len(details_url)-1
        while details_url[i] != '/':
            i -= 1
        url = details_url[:i+1] + \
            urllib.parse.quote_plus(details_url[i+1:])
        res = []
        c = httplib2.Http()
        resp, content = c.request(url)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        try:
            comments_div = self.api.find_elements(
                tree.getRootElement(), "div", id="comments")[0]
            comments_table = self.api.find_elements(self.api.find_elements(
                comments_div, "table", **{'class': 'commentsTable'})[0], "table", width="750px")[0]
            lines = self.api.find_elements(comments_table, "tr", 1)
            for i in range(len(lines)/3):
                try:
                    title_line = lines[3*i]
                    content_line = lines[3*i+1]
                    username_node = self.api.find_elements(
                        title_line, "strong")[0]
                    username = username_node.getContent()
                    date_data = username_node.next.getContent().rstrip().lstrip()[
                        3:]
                    try:
                        date = self._parseCommentDate(date_data)
                    except:
                        date = ""
                    content = content_line.getContent()
                    res.append({
                        "content": content,
                        "date": date,
                        "user_name": username,
                    })
                except:
                    pass
        except:
            pass
        return res

    def _parseDate(self, data):
        day, month, year = data.split(" ")
        while day[0] == "0":
            day = day[1:]
        month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
                 "Aug", "Sep", "Oct", "Nov", "Dec"].index(month)+1
        return datetime.date(eval(year), month, eval(day))

    def _parseCommentDate(self, date):
        i = date.index(",")+2
        date = date[i:]
        date, hour = date.split(" at ")
        day, month, year = date.split(" ")
        hour, minute, second = hour.split(":")
        hour = int(hour)
        minute = int(minute)
        second = int(second)
        day = int(day)
        year = int(year)
        month = ["January", "February", "March", "April", "May", "June", "July",
                 "August", "September", "October", "November", "December"].index(month)+1
        return datetime.datetime(year, month, day, hour, minute, second)

    def _do_get_link(self, reflink):
        i = len(reflink)-1
        while reflink[i] != '/':
            i -= 1
        url = reflink[:i+1]+urllib.parse.quote_plus(reflink[i+1:])
        utype, path = urllib.parse.splittype(url)
        host, path = urllib.parse.splithost(path)
        c = http.client.HTTPConnection(host)
        c.request('GET', path)
        resp = c.getresponse()
        content = resp.read()
        tree = libxml2.htmlParseDoc(content, "utf-8")
        link = self.api.find_elements(
            tree.getRootElement(), id="downloadLink")[0]
        return link.prop('href')

    def _get_magnet(self, url):
        i = len(url)-1
        while url[i] != '/':
            i -= 1
        url = url[:i+1]+urllib.parse.quote_plus(url[i+1:])
        c = httplib2.Http()
        resp, content = c.request(url)
        if "set-cookie" in resp:
            cookie = resp['set-cookie']
        else:
            cookie = None
        tree = libxml2.htmlParseDoc(content, "utf-8")
        form = self.api.find_elements(tree.getRootElement(), "form", id="frmAdultDisclaimer")
        if form:
            form = form[0]
            inputs = self.api.find_elements(form, "input")
            body = {}
            for i in inputs:
                body[i.prop('name')] = i.prop('value')
            del body['btn_Decline']
            body = urllib.parse.urlencode(body)
            headers = {'Content-type': "application/x-www-form-urlencoded"}
            if cookie:
                headers['Cookie'] = cookie
            url = urllib.basejoin(url, form.prop('action'))
            resp, content = c.request(url, "POST", body, headers)
            if "set-cookie" in resp:
                cookie = resp['set-cookie']
            if cookie:
                headers['Cookie'] = cookie
            url = urllib.basejoin(url, resp["location"])
            resp, content = c.request(url, headers=headers)
            tree = libxml2.htmlParseDoc(content, "utf-8")
        return self.api.find_elements(tree.getRootElement(), "a", **{'class': 'dwld_links'})[0].prop('href')
