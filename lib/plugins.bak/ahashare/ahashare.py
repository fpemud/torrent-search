#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import time


class AhaSharePlugin:

    def __init__(self, api):
        self.api = api

    def run_search(self, pattern, param, page_url=""):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        if page_url == "":
            page_url = "http://www.ahashare.com/torrents-search.php?search=" + \
                urllib.parse.quote_plus(pattern)

        resp, content = self.api.http_queue_request(page_url)

        tree = libxml2.htmlParseDoc(content, "utf-8")

        results_table = self.api.find_elements(
            tree.getRootElement(), "table", **{'class': 'ttable_headinner'})[0]

        next_page_link = None

        try:

            elem = results_table.__next__

            while elem.name != "center":

                elem = elem.__next__

            count_elem = None

            for i in self.api.find_elements(elem, "b"):

                if "-" in i.getContent():

                    count_elem = i

                elif i.getContent().startswith("Next"):

                    next_page_link = urllib.basejoin(
                        page_url, i.parent.parent.prop("href"))

            data = count_elem.getContent()

            i = len(data)-1

            while data[i] in "0123456789":
                i -= 1
            api_notify_results_total_count(int(data[i+1:]))

        except:

            pass

        for result in self.api.find_elements(results_table, "tr")[1:]:

            try:

                category, name, dl_link, uploader, size, seeders, leechers, health = self.api.find_elements(
                    result, "td")

                title = name.getContent().rstrip().lstrip()[2:].replace(
                    chr(226)+chr(150)+chr(136), "")

                details_link = urllib.basejoin(
                    page_url, self.api.find_elements(name, "a")[0].prop('href'))

                dl_link = urllib.basejoin(
                    page_url, self.api.find_elements(dl_link, "a")[0].prop('href'))

                size = size.getContent().rstrip().lstrip()

                seeders = int(seeders.getContent().rstrip().lstrip())

                leechers = int(leechers.getContent().rstrip().lstrip())

                resp, content = self.api.http_queue_request(details_link)

                itemtree = libxml2.htmlParseDoc(content, "utf-8")

                details_table = self.api.find_elements(
                    itemtree.getRootElement(), "table", width="95%", cellpadding="3", border="0")[1]

                details = {}

                for i in self.api.find_elements(details_table, "tr"):

                    try:

                        key, value = self.api.find_elements(
                            i, "td")

                        details[key.getContent()] = value.getContent()

                    except:

                        pass

                try:

                    date = time.strptime(
                        details['Date Added:'], "%d-%m-%Y %H:%M:%S")

                    date = datetime.date(
                        date.tm_year, date.tm_mon, date.tm_mday)

                except:

                    date = None

                api_notify_one_result({
                    "id": "",
                    "label": title,
                    "date": date,
                    "size": size,
                    "seeders": seeders,
                    "leechers": leechers,
                    "link": dl_link,
                    "orig_url": details_link,
                })
            except:
                pass

        if next_page_link and next_page_link != page_url and not self.api.stop_search:

            self.run_search(pattern, param, next_page_link)
