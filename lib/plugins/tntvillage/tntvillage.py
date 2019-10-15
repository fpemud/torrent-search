#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-


import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import httplib2


class TNTVillagePlugin:

    def __init__(self, api):
        self.api = api

    def try_login(self):
        c = httplib2.Http()
        username, password = self.api.get_credential
        resp, content = c.request(
            'http://forum.tntvillage.scambioetico.org/tntforum/index.php?act=Login&CODE=00')
        data = urllib.parse.urlencode(
            {'UserName': username, 'PassWord': password, 'CookieDate': '1', 'referer': ''})
        headers = {'Content-type': 'application/x-www-form-urlencoded',
                   'Cookie': resp['set-cookie']}
        resp, content = c.request(
            "http://forum.tntvillage.scambioetico.org/tntforum/index.php?act=Login&CODE=01", "POST", data, headers)
        if 'set-cookie' in resp and 'member_id' in resp['set-cookie']:
            cookie = self.api.parse_cookie(resp['set-cookie'])
        else:
            return None
        tree = libxml2.htmlParseDoc(content, "utf-8")
        url = self.api.find_elements(tree.getRootElement(), "a")[
            0].prop('href')
        headers = {'Cookie': cookie}
        resp, content = c.request(url, 'GET', headers=headers)
        return cookie

    def run_search(self, pattern, param, stp=0, stn=20, first_page=True):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        headers = {'Content-type': 'application/x-www-form-urlencoded',
                   'Cookie': self.api.get_login_cookie}
        data = {'sb': '0', 'sd': '0', 'cat': '0',
                'stn': str(stn), 'filter': pattern}
        if first_page:
            data['set'] = 'Imposta filtro'
        else:
            data['next'] = "Pagine successive >>"
            data['stp'] = str(stp)
        data = urllib.parse.urlencode(data)
        resp, content = self.api.http_queue_request(
            "http://forum.tntvillage.scambioetico.org/tntforum/index.php?act=allreleases", 'POST', data, headers)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        ucpcontent = self.api.find_elements(
            tree.getRootElement(), "div", id="ucpcontent")[0]
        try:
            data = self.api.find_elements(self.api.find_elements(
                ucpcontent, "table")[1], "td")[1].getContent()
            i = 0
            while data[i] not in "0123456789":
                i += 1
            j = i
            while data[j] in "0123456789":
                j += 1
            api_notify_results_total_count(eval(data[i:j]))
        except:
            pass
        restable = self.api.find_elements(ucpcontent, "table")[3]
        lines = self.api.find_elements(restable, "tr", **{'class': 'row4'})
        for i in lines:
            try:
                category_link, title, releaser, group, leechers, seeders, complete, dim, peers = self.api.find_elements(
                    i, "td")
                link = self.api.find_elements(category_link, "a")[0]
                label = link.getContent()
                link = link.prop('href')
                leechers = eval(leechers.getContent()[1:-1].rstrip().lstrip())
                seeders = eval(seeders.getContent()[1:-1].rstrip().lstrip())
                resp, content = self.api.http_queue_request(link, headers=headers)
                itemtree = libxml2.htmlParseDoc(content, "utf-8")
                date = self.api.find_elements(self.api.find_elements(itemtree.getRootElement(
                ), "span", **{'class': 'postdetails'})[0], "b")[0].next.getContent()
                j = date.index(',')
                date = date[:j].rstrip().lstrip()
                month, day, year = date.split(' ')
                month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
                         'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].index(month)+1
                day = eval(day)
                year = eval(year)
                date = datetime.date(year, month, day)
                torrent_link = self.api.find_elements(
                    itemtree.getRootElement(), "a", title="Scarica allegato")[0]
                details_table = torrent_link.parent.parent.parent
                details = self.api.find_elements(details_table, "tr")[1:]
                hashvalue = None
                for i in details:
                    try:
                        key = self.api.find_elements(
                            i, "td")[0].getContent().rstrip().lstrip()
                        value = self.api.find_elements(
                            i, "td")[1].getContent().rstrip().lstrip()
                        if key == "Dimensione:":
                            size = value.upper()
                        if key == "info_hash:":
                            hashvalue = value
                    except:
                        pass
                api_notify_one_result({
                    "id": "",
                    "label": label,
                    "date": date,
                    "size": size,
                    "seeders": seeders,
                    "leechers": leechers,
                    "link": torrent_link.prop('href'),
                    "hashvalue": hashvalue,
                })
            except:
                pass
            if self.stop_search:
                return
        if not self.stop_search:
            if self.api.find_elements(tree.getRootElement(), "input", name="next"):
                stn = eval(self.api.find_elements(
                    tree.getRootElement(), "input", name="stn")[0].prop('value'))
                try:
                    stp = eval(self.api.find_elements(
                        tree.getRootElement(), "input", name="stp")[0].prop('value'))
                except:
                    stp = 0
                self.run_search(pattern, param, stp, stn, False)
