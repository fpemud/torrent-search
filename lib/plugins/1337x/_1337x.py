#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import TorrentSearch
import urllib.request
import urllib.parse
import urllib.error
import libxml2
import os
import datetime
import time
import httplib2
import TorrentSearch.htmltools


class _1337XPluginResult(TorrentSearch.Plugin.PluginResult):

    def __init__(self, label, date, size, seeders, leechers, torrent_url, magnet_url, category, nb_comments, details_page_url, comments, poster, filelist):
        TorrentSearch.Plugin.PluginResult.__init__(self, label, date, size, seeders, leechers, magnet_url, category=category, nb_comments=nb_comments)
        self.torrent_url = torrent_url
        self.details_page_url = details_page_url
        self.comments = comments
        self.comments_loaded = True
        self.poster = poster
        self.poster_loaded = True
        self.filelist = filelist
        self.filelist_loaded = True

    def _do_get_link(self):
        return self.torrent_url


class _1337XPlugin(TorrentSearch.Plugin.Plugin):

    def _parseCommentsDiv(self, div):
        res = []
        for comment in TorrentSearch.htmltools.find_elements(div, "div", **{'class': 'comment'}):
            date = TorrentSearch.htmltools.find_elements(TorrentSearch.htmltools.find_elements(
                comment, "h5")[0], "span")[0].next.getContent().rstrip().lstrip()
            username = TorrentSearch.htmltools.find_elements(TorrentSearch.htmltools.find_elements(
                comment, "dt", **{'class': 'author'})[0], "a")[0].getContent()
            content = TorrentSearch.htmltools.find_elements(
                comment, "div", **{'class': 'postright round'})[0].getContent()
            res.insert(0, TorrentSearch.Plugin.TorrentResultComment(
                content, date, username))
        return res

    def _parseFileList(self, ul, path=""):
        res = []
        for li in TorrentSearch.htmltools.find_elements(ul, "li", 1):
            if li.prop("class") == "pft-directory":
                pathname = li.getContent().rstrip().lstrip()
                res += self._parseFileList(li.next, path+pathname+"/")
            else:
                data = li.getContent().rstrip().lstrip()
                i = len(data)-1
                while data[i] != "(":
                    i -= 1
                filename = data[:i].rstrip().lstrip()
                size = data[i+1:-1].rstrip().lstrip().upper()
                res.append((path+filename, size))
        return res

    def plugin_run_search(self, pattern, page_url=""):
        if page_url == "":
            page_url = "http://1337x.org/search/%s/0/" % urllib.parse.quote_plus(
                pattern)
        resp, content = self.api_http_queue_request(page_url)
        tree = libxml2.htmlParseDoc(content, "utf-8")

        pager = None
        try:
            pager = TorrentSearch.htmltools.find_elements(TorrentSearch.htmltools.find_elements(
                tree.getRootElement(), "div", **{'class': 'pagination'})[0], "ul")[0]
            data = TorrentSearch.htmltools.find_elements(TorrentSearch.htmltools.find_elements(
                tree.getRootElement(), "div", **{'class': 'featuredTorrentHead'})[1], "h2")[0].getContent()[:-10]
            i = len(data)-1
            while data[i] in "0123456789":
                i -= 1
            self.results_count = int(data[i+1:])
        except:
            pass

        results_table = TorrentSearch.htmltools.find_elements(
            tree.getRootElement(), "div", **{'class': 'featuredTorrent'})
        if len(results_table) > 1:
            results_table = results_table[1]
        else:
            results_table = results_table[0]

        for result in TorrentSearch.htmltools.find_elements(results_table, "li"):
            try:
                seeders = int(TorrentSearch.htmltools.find_elements(
                    result, "span", **{'class': 'seed'})[0].getContent())
                leechers = int(TorrentSearch.htmltools.find_elements(
                    result, "span", **{'class': 'leech'})[0].getContent())
                size = TorrentSearch.htmltools.find_elements(
                    result, "span", **{'class': 'size'})[0].getContent()
                label = TorrentSearch.htmltools.find_elements(TorrentSearch.htmltools.find_elements(
                    result, "h3", **{'class': 'org'})[0], "a")[0].getContent()
                details_link = urllib.basejoin(page_url, TorrentSearch.htmltools.find_elements(
                    TorrentSearch.htmltools.find_elements(result, "h3", **{'class': 'org'})[0], "a")[0].prop("href"))
                resp, content = self.api_http_queue_request(details_link)
                itemtree = libxml2.htmlParseDoc(content, "utf-8")
                infobox = TorrentSearch.htmltools.find_elements(
                    itemtree.getRootElement(), "div", **{'class': 'torrentInfolf'})[0]
                itemdata = {}
                for li in TorrentSearch.htmltools.find_elements(infobox, "li"):
                    try:
                        key = TorrentSearch.htmltools.find_elements(
                            li, "span", **{'class': 'col01'})[0].getContent()
                        value = TorrentSearch.htmltools.find_elements(
                            li, "span", **{'class': 'col02'})[0].getContent()
                        itemdata[key] = value
                    except:
                        pass
                    try:
                        key = TorrentSearch.htmltools.find_elements(
                            li, "span", **{'class': 'col03'})[0].getContent()
                        value = TorrentSearch.htmltools.find_elements(
                            li, "span", **{'class': 'col04'})[0].getContent()
                        itemdata[key] = value
                    except:
                        pass
                # MISSING DATE
                date = None
                # MISSING CATEGORY
                # MISSING COMMENTS
                nb_comments = 0
                res_comments = None
                poster = None
                # MISSING FILELIST
                res_filelist = None
                torrent_link = TorrentSearch.htmltools.find_elements(
                    itemtree.getRootElement(), "a", **{'class': 'torrentDw'})[0].prop("href")
                magnet_link = TorrentSearch.htmltools.find_elements(
                    itemtree.getRootElement(), "a", **{'class': 'magnetDw'})[0].prop("href")
                self.api_add_result(_1337XPluginResult(label, date, size, seeders, leechers, torrent_link,
                                                   magnet_link, "", nb_comments, details_link, res_comments, poster, res_filelist))
            except:
                pass
            if self.stop_search:
                return

        if pager and not self.stop_search:
            url = urllib.basejoin(page_url, TorrentSearch.htmltools.find_elements(TorrentSearch.htmltools.find_elements(
                pager, "a", **{'class': 'active'})[0].parent.__next__, "a")[0].prop("href"))
            self.plugin_run_search(pattern, url)
