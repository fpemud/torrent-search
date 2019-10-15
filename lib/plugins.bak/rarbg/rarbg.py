#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-



import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import time
import os
import httplib2




class RARBGTorrentPluginResult:

    def __init__(self, label, date, size, seeders, leechers, reflink, hashvalue, category, nb_comments):

        TorrentSearch.Plugin.PluginResult.__init__(
            self, label, date, size, seeders, leechers, hashvalue=hashvalue, category=category, nb_comments=nb_comments)

        self.reflink = reflink

    def _do_get_details(self):

        c = httplib2.Http()

        resp, content = c.request(self.reflink)

        tree = libxml2.htmlParseDoc(content, "utf-8")

        self._link = urllib.basejoin(self.reflink, self.api.find_elements(tree.getRootElement(
        ), "a", onmouseover="return overlib('Click here to download torrent')")[0].prop('href'))

        img = self.api.find_elements(
            tree.getRootElement(), "img", alt=self.label)

        if img:

            self.poster = img[0].prop('src')

        else:

            self.poster = None

        self.poster_loaded = True

        files_div = self.api.find_elements(
            tree.getRootElement(), "div", id="files")

        filelist = TorrentSearch.Plugin.FileList()

        if len(files_div) == 1:

            files_div = files_div[0]

            for i in self.api.find_elements(files_div, "tr")[1:]:

                filename, size = self.api.find_elements(i, "td")

                filename = filename.getContent()

                size = size.getContent()

                filelist.append(filename, size)

        self.filelist = filelist

        self.filelist_loaded = True

        comments_link = self.api.find_elements(
            tree.getRootElement(), "a", name="comments")

        comments = TorrentSearch.Plugin.CommentsList()

        try:

            if len(comments_link) == 1:

                node = comments_link[0]

                while node.name != "table":

                    node = node.__next__

                comments_lines = self.api.find_elements(node, "tr")

                for i in range(len(comments_lines)/2):

                    username, date = self.api.find_elements(
                        comments_lines[2*i], "td")

                    username = username.getContent()

                    try:

                        date_str = date.getContent()

                        date, hour = date_str.split(" ")

                        day, month, year = date.split("/")

                        hour, minute, second = hour.split(":")

                        while day[0] == "0":

                            day = day[1:]

                        while month[0] == "0":

                            month = month[1:]

                        while hour[0] == "0":

                            hour = hour[1:]

                        while minute[0] == "0":

                            minute = minute[1:]

                        while second[0] == "0":

                            second = second[1:]

                        day = int(day)

                        month = int(month)

                        year = int(year)

                        hour = int(hour)

                        minute = int(minute)

                        second = int(second)

                        date = datetime.datetime(
                            year, month, day, hour, minute, second)

                    except:

                        date = None

                    content = self.api.find_elements(
                        comments_lines[2*i+1], "td")[1].getContent()

                    comments.append(TorrentSearch.Plugin.TorrentResultComment(
                        content, date, username))

        except:

            pass

        self.comments = comments

        self.comments_loaded = True

    def _do_load_poster(self):

        if not self.poster_loaded:

            self._do_get_details()

        return self.poster

    def _do_load_filelist(self):

        if not self.filelist_loaded:

            self._do_get_details()

        return self.filelist

    def _do_load_comments(self):

        if not self.comments_loaded:

            self._do_get_details()

        return self.comments

    def _do_get_link(self):

        if not hasattr(self, "_link"):

            self._do_get_details()

        return self._link


class RARBGTorrentPlugin:

    def __init__(self, api):
        self.api = api

    def _parseDate(self, data):
        res = time.strptime(data, "%Y-%m-%d %H:%M:%S")
        return datetime.date(res.tm_year, res.tm_mon, res.tm_mday)

    def _parseCat(self, cat):
        catsmap = {
            "XXX (18+)": "video/xxx",
            "Music/MP3": "audio/music",
            "Music/FLAC": "audio/music",
            "Movies/DVD-R": "video/movie",
            "Movies/XVID": "video/movie",
            "Movies/Anime&Manga": "video/manga",
            "Movies/HDTV": "video/tv",
            "Sports": "video/sports",
            "Movies/TV-episodes": "video/tv",
            "Music/Video": "video/music",
            "Music/DVD": "video/music",
            "Software/PC ISO": "software/pc",
            "Software/PDA/Smartphone": "software/pda",
            "Movies/x264": "video/movie",
            "Movies/Documentaries": "video/documentary",
            "BG TV": "video/tv",
            "Games/PS2": "software/game/ps2",
            "Games/PC ISO": "software/game/pc",
            "Games/PC RIP": "software/game/pc",
            "Games/PSP": "software/game/psp",
            "Games/XBOX-360": "software/game/xbox360",
            "Games/XBOX": "software/game/xbox",
            "e-Books": "ebooks",
            "Movies/TV-Boxset": "video/tv",
            "Movies/VCD/SVCD": "video/movie",
        }
        if cat in catsmap:
            return catsmap[cat]
        else:
            return ""

    def run_search(self, pattern, param, page=1, href=None):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        if href == None:

            href = "http://rarbg.com/torrents.php?search=" + \
                urllib.parse.quote_plus(pattern)

        resp, content = self.api.http_queue_request(href)

        tree = libxml2.htmlParseDoc(content, "utf-8")

        try:

            div = self.api.find_elements(
                tree.getRootElement(), "div", **{'class': 'wp-pagenavi'})[0]

            data = self.api.find_elements(div, "a")[-1].getContent()

            i = len(data)-1

            while data[i] in "0123456789":

                i -= 1

            api_notify_results_total_count(eval(data[i+1:]))

        except:

            pass

        cats = self.api.find_elements(
            tree.getRootElement(), "select", name="category")[0]

        categories = {}

        for i in self.api.find_elements(cats, "option"):

            categories[i.prop('value')] = i.getContent()

        lines = self.api.find_elements(
            tree.getRootElement(), "tr", **{'class': 'lista2'})

        for i in lines:

            try:

                cat, link, date, size, seeders, leechers, comments, c = self.api.find_elements(
                    i, "td")

                cat = self.api.find_elements(cat, "a")[0].prop('href')

                j = cat.index('=')

                cat = cat[j+1:]

                if cat in categories:

                    cat = categories[cat]

                else:

                    cat = ""

                cat = self._parseCat(cat)

                link = self.api.find_elements(link, "a")[0]

                label = link.getContent()

                link = urllib.basejoin(href, link.prop('href'))

                hashvalue = link.split('/')[-2]

                date = self._parseDate(date.getContent())

                size = size.getContent()

                seeders = eval(seeders.getContent())

                leechers = eval(leechers.getContent())

                nb_comments = eval(comments.getContent())

                self.api.notify_one_result(RARBGTorrentPluginResult(
                    label, date, size, seeders, leechers, link, hashvalue, cat, nb_comments))

            except:

                pass

            if self.stop_search:

                return

        if not self.stop_search:

            try:

                div = self.api.find_elements(
                    tree.getRootElement(), "div", **{'class': 'wp-pagenavi'})[0]

                cspan = self.api.find_elements(
                    div, "span", **{"class": "current"})[0]

                a = cspan.next.__next__

                if a.name == "a":

                    self.run_search(
                        pattern, 0, urllib.basejoin(href, a.prop('href')))

            except:

                pass

        del tree
