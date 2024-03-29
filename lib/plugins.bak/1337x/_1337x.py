#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import urllib.request
import urllib.parse
import urllib.error
import libxml2


class _1337XPlugin:

    def __init__(self, api):
        self.api = api

    def run_search(self, pattern, param, page_url=None):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        if page_url is None:
            page_url = "http://1337x.org/search/%s/0/" % (urllib.parse.quote_plus(pattern))
        resp, content = self.api.http_queue_request(page_url)
        tree = libxml2.htmlParseDoc(content, "utf-8")

        pager = None
        try:
            pager = self.api.find_elements(self.api.find_elements(tree.getRootElement(), "div", **{'class': 'pagination'})[0], "ul")[0]
            data = self.api.find_elements(self.api.find_elements(tree.getRootElement(), "div", **{'class': 'featuredTorrentHead'})[1], "h2")[0].getContent()[:-10]
            i = len(data) - 1
            while data[i] in "0123456789":
                i -= 1
            api_notify_results_total_count(int(data[i+1:]))
        except:
            pass

        results_table = self.api.find_elements(tree.getRootElement(), "div", **{'class': 'featuredTorrent'})
        if len(results_table) > 1:
            results_table = results_table[1]
        else:
            results_table = results_table[0]

        for result in self.api.find_elements(results_table, "li"):
            try:
                seeders = int(self.api.find_elements(result, "span", **{'class': 'seed'})[0].getContent())
                leechers = int(self.api.find_elements(result, "span", **{'class': 'leech'})[0].getContent())
                size = self.api.find_elements(result, "span", **{'class': 'size'})[0].getContent()
                label = self.api.find_elements(self.api.find_elements(result, "h3", **{'class': 'org'})[0], "a")[0].getContent()
                details_link = urllib.basejoin(page_url, self.api.find_elements(self.api.find_elements(result, "h3", **{'class': 'org'})[0], "a")[0].prop("href"))
                resp, content = self.api.http_queue_request(details_link)
                itemtree = libxml2.htmlParseDoc(content, "utf-8")
                infobox = self.api.find_elements(itemtree.getRootElement(), "div", **{'class': 'torrentInfolf'})[0]
                itemdata = {}
                for li in self.api.find_elements(infobox, "li"):
                    try:
                        key = self.api.find_elements(li, "span", **{'class': 'col01'})[0].getContent()
                        value = self.api.find_elements(li, "span", **{'class': 'col02'})[0].getContent()
                        itemdata[key] = value
                    except:
                        pass
                    try:
                        key = self.api.find_elements(li, "span", **{'class': 'col03'})[0].getContent()
                        value = self.api.find_elements(li, "span", **{'class': 'col04'})[0].getContent()
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
                torrent_link = self.api.find_elements(itemtree.getRootElement(), "a", **{'class': 'torrentDw'})[0].prop("href")
                magnet_link = self.api.find_elements(itemtree.getRootElement(), "a", **{'class': 'magnetDw'})[0].prop("href")

                api_notify_one_result({
                    "id": "",
                    "label": label,
                    "date": date,
                    "size": size,
                    "seeders": seeders,
                    "leechers": leechers,
                    "link": torrent_link,
                    "magnet_link": magnet_link,
                    "nb_comments": nb_comments,
                    "orig_url": details_link,
                })
            except:
                pass
            if self.api.stop_search:
                return

        if pager and not self.api.stop_search:
            url = urllib.basejoin(page_url, self.api.find_elements(self.api.find_elements(
                pager, "a", **{'class': 'active'})[0].parent.__next__, "a")[0].prop("href"))
            self.run_search(pattern, param, url)

    def _parseCommentsDiv(self, div):
        res = []
        for comment in self.api.find_elements(div, "div", **{'class': 'comment'}):
            date = self.api.find_elements(self.api.find_elements(
                comment, "h5")[0], "span")[0].next.getContent().rstrip().lstrip()
            username = self.api.find_elements(self.api.find_elements(
                comment, "dt", **{'class': 'author'})[0], "a")[0].getContent()
            content = self.api.find_elements(
                comment, "div", **{'class': 'postright round'})[0].getContent()
            res.insert(0, {
                "content": content,
                "date": date,
                "user_name": username,
            })
        return res

    def _parseFileList(self, ul, path=""):
        res = []
        for li in self.api.find_elements(ul, "li", 1):
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
