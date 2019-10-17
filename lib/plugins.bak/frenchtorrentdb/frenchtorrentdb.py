#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import urllib.request
import urllib.parse
import urllib.error
import libxml2
import datetime
import os
import time
import httplib2
import http.client
import tempfile
import math
from PIL import Image


def buildvector(im):
    d1 = {}
    count = 0
    for i in im.getdata():
        d1[count] = i
        count += 1
    return d1


ICONSET = ['2', '3', '4', '5', '6', '7', '8', '9', 'b', 'c', 'd', 'f', 'g',
           'h', 'j', 'k', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z']
IMAGESET = []

CAPTCHA_LETTERS_PATH = os.path.join(
    os.path.split(__file__)[0], 'captcha_letters_0.1.0')
if not os.path.exists(CAPTCHA_LETTERS_PATH):
    os.mkdir(CAPTCHA_LETTERS_PATH)


class VectorCompare:

    def magnitude(self, concordance):
        total = 0
        for word, count in concordance.items():
            total += count ** 2
        return math.sqrt(total)

    def relation(self, concordance1, concordance2):
        relevance = 0
        topvalue = 0
        for word, count in concordance1.items():
            if word in concordance2:
                topvalue += count * concordance2[word]
        return topvalue / (self.magnitude(concordance1) * self.magnitude(concordance2))


class FrenchTorrentDBPlugin:
    vector_compare = VectorCompare()

    def __init__(self, api):
        self.api = api

    def try_login(self):
        if len(IMAGESET) == 0:
            for letter in ICONSET:
                letter_filename = os.path.join(
                    CAPTCHA_LETTERS_PATH, '%s.png' % letter)
                if not os.path.exists(letter_filename):
                    filename, msg = urllib.request.urlretrieve(
                        'http://torrent-search.sourceforge.net/captcha_letters/000029_frenchtorrentdb/0.1.0/%s.png' % letter, letter_filename)
                    if msg['content-type'] != 'image/png' and os.path.exists(letter_filename):
                        os.unlink(letter_filename)
                if not os.path.exists(letter_filename):
                    continue
                im = Image.open(letter_filename)
                IMAGESET.append({letter: [buildvector(im)]})
        username, password = self.api.get_credential
        c = http.client.HTTPConnection('www2.frenchtorrentdb.com')
        c.request('GET', '/')
        resp = c.getresponse()
        resp.read()
        cookie = self.api.parse_cookie(
            resp.getheader('set-cookie')).split(';')[0]
        c.request('GET', '/?check_cookie=1', headers={'Cookie': cookie})
        resp = c.getresponse()
        resp.read()
        c.request('GET', '/?section=LOGIN&Func=access_denied&access_needed1',
                  headers={'Cookie': cookie})
        resp = c.getresponse()
        resp.read()
        c.request('GET', '/?section=LOGIN&getimg=1&ajax=1&mod_ajax=1',
                  headers={'Cookie': cookie})
        resp = c.getresponse()
        captcha_data = resp.read()
        fd, filename = tempfile.mkstemp('.jpg')
        os.write(fd, captcha_data)
        os.close(fd)
        data = urllib.parse.urlencode({'username': username, 'password': password,
                                       'code': self._decode_captcha(filename), 'submit': 'Connexion'})
        headers = {
            'Content-type': 'application/x-www-form-urlencoded', 'Cookie': cookie}
        for i in range(5):
            c.request('POST', '/?section=LOGIN', data, headers)
            resp = c.getresponse()
            resp_data = resp.read()
            if resp.status == 302 and resp.getheader('location') == '/?section=INDEX':
                return cookie
            else:
                c.request(
                    'GET', '/?section=LOGIN&Func=access_denied&access_needed1', headers={'Cookie': cookie})
                resp = c.getresponse()
                resp.read()
                c.request(
                    'GET', '/?section=LOGIN&getimg=1&ajax=1&mod_ajax=1', headers={'Cookie': cookie})
                resp = c.getresponse()
                captcha_data = resp.read()
                fd, filename = tempfile.mkstemp('.jpg')
                os.write(fd, captcha_data)
                os.close(fd)
                data = urllib.parse.urlencode(
                    {'username': username, 'password': password, 'code': self._decode_captcha(filename), 'submit': 'Connexion'})
        return None

    def load_filelist(self, result_id):
        res = []
        http = httplib2.Http()
        headers = {'Cookie': self.plugin.api.get_login_cookie}
        resp, content = http.request(
            "http://www2.frenchtorrentdb.com/?section=INFOS&id="+self._get_site_id(result_id)+"&type=1", headers=headers)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        div = self.api.find_elements(
            tree.getRootElement(), "div", id="mod_infos")[0]
        pre = self.api.find_elements(div, "pre")[0]
        files = self.api.find_elements(pre, "p")
        cur_folder = ""
        for i in files:
            if self.api.find_elements(i, "img")[0].prop("src") == "/themes/images/files/folder.gif":
                cur_folder = i.getContent().strip().lstrip()
                continue
            data = i.getContent().strip().lstrip()
            j = len(data)-1
            while data[j] != '(':
                j -= 1
            filename, size = data[:j], data[j+1:-1]
            filename = filename.strip().lstrip()
            if cur_folder:
                filename = cur_folder+"/"+filename
            size = size.strip().lstrip()
            res.append({
                "filename": filename,
                "size": size,
            })
        return res

    def _get_site_id(self, reflink):
        i = len(reflink)-1
        while reflink[i] != "=":
            i -= 1
        return reflink[i+1:]

    def _parseDate(self, date, year, prev_month):
        i = date.index('à')
        hour = date[i+2:].rstrip().lstrip()
        date = date[:i].rstrip().lstrip()
        res = ''
        try:
            if date == "Aujourd'hui" or date == "Hier":
                year = int(time.strftime('%Y'))
                month = int(time.strftime('%m'))
                day = int(time.strftime('%d'))
                res = datetime.date(year, month, day)
                if date == "Hier":
                    res = res-datetime.timedelta(1)
                prev_month = res.month
            else:
                day, month = date.split(' ')
                month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
                         'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].index(month)+1
                day = int(day)
                res = datetime.date(year, month, day)
                if month > prev_month:
                    year -= 1
                    res = datetime.date(year, month, day)
                prev_month = month
        except:
            print(date, hour)
        return res, year, prev_month

    def _decode_captcha(self, filename):
        im = Image.open(filename)
        im = im.convert("P")
        im2 = Image.new("P", im.size, 255)
        temp = {}
        for x in range(im.size[1]):
            for y in range(im.size[0]):
                pix = im.getpixel((y, x))
                temp[pix] = pix
                if pix in [82, 88, 89, 52, 90, 53, 83, 125, 46, 47]:  # these are the numbers to get
                    im2.putpixel((y, x), 0)

        inletter = False
        foundletter = False
        start = 0
        end = 0
        letters = []
        for y in range(im2.size[0]):  # slice across
            for x in range(im2.size[1]):  # slice down
                pix = im2.getpixel((y, x))
                if pix != 255:
                    inletter = True
            if not foundletter and inletter:
                foundletter = True
                start = y
            if foundletter and not inletter:
                foundletter = False
                end = y
                letters.append((start, end))
            inletter = False

        guessword = ""
        for letter in letters:
            im3 = im2.crop((letter[0], 0, letter[1], im2.size[1]))
            guess = []
            for image in IMAGESET:
                for x, y in image.items():
                    if len(y) != 0:
                        guess.append(
                            (self.vector_compare.relation(y[0], buildvector(im3)), x))
            guess.sort(reverse=True)
            guessword = "%s%s" % (guessword, guess[0][1])
        if len(guessword) == 7 and guessword[0] == 'j':
            guessword = guessword[1:]
        return guessword

    def run_search(self, pattern, param, page_url='', year=None, prev_month=13):
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]

        http = httplib2.Http()
        headers = {'Cookie': self.api.get_login_cookie}
        if page_url == "":
            page_url = "http://www2.frenchtorrentdb.com/?name=%s&parent_cat_id=&section=TORRENTS&last_adv_cat_selected=&order_by=added&order=DESC&Rechercher=Rechercher" % urllib.parse.quote(
                pattern)
        resp, content = http.request(page_url, headers=headers)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        try:
            count = int(self.api.find_elements(self.api.find_elements(
                tree.getRootElement(), "div", **{'class': 'results'})[0], "b")[0].getContent())
            api_notify_results_total_count(count)
        except:
            pass
        results_table = self.api.find_elements(
            tree.getRootElement(), "div", **{'class': 'DataGrid'})[0]
        lines = self.api.find_elements(results_table, "ul")
        if year is None:
            year = int(time.strftime("%Y"))
        for i in range(len(lines)):
            try:
                sub_cat, cat, name, size, seeders, leechers, health = self.api.find_elements(
                    lines[i], 'li')
                alink = self.api.find_elements(name, "a")[0]
                link = urllib.basejoin(page_url, alink.prop('href'))
                label = alink.getContent().rstrip().lstrip()
                size = size.getContent()
                seeders = int(seeders.getContent())
                leechers = int(leechers.getContent())
                itemresp, itemcontent = http.request(link, headers=headers)
                itemtree = libxml2.htmlParseDoc(itemcontent, "utf-8")
                try:
                    posters = self.api.find_elements(
                        itemtree.getRootElement(), "img", **{'class': 'bbcode_img'})
                    if posters:
                        poster = posters[0].prop('src')
                except:
                    poster = None
                links = self.api.find_elements(self.api.find_elements(
                    itemtree.getRootElement(), "div", id="mod_infos_menu")[0], "a")
                torrent_link = ''
                for j in links:
                    if j.prop('href').startswith('/?section=DOWNLOAD'):
                        torrent_link = urllib.basejoin(link, j.prop('href'))
                divs = self.api.find_elements(self.api.find_elements(
                    itemtree.getRootElement(), "div", id="mod_infos_menu")[0], "div")
                date = ''
                for j in divs:
                    tl = self.api.find_elements(j, "label")
                    if tl and tl[0].getContent() == "Date d'ajout:":
                        date = self.api.find_elements(
                            j, "span")[0].getContent()
                if date:
                    date, year, prev_month = self._parseDate(
                        date, year, prev_month)
                comments = []
                comment_year = int(time.strftime("%Y"))
                comment_prev_month = 13
                try:
                    comments_div = self.api.find_elements(
                        itemtree.getRootElement(), "div", id="mod_comments_torrent")[0]
                    comments_list = []
                    for tl in self.api.find_elements(comments_div, "ul"):
                        comments_list.insert(0, tl)
                    for comment in comments_list:
                        username = self.api.find_elements(self.api.find_elements(
                            comment, "li", **{'class': 'username'})[0], "a")[0].getContent()
                        comment_txt = ""
                        comment_date = ""
                        for line in self.api.find_elements(self.api.find_elements(comment, "li", **{'class': 'text'})[0], "p"):
                            if line.prop("class") == "date":
                                d = line.getContent()
                                k = d.index(':')
                                d = d[k+2:]
                                comment_date, comment_year, comment_prev_month = self._parseDate(
                                    d, comment_year, comment_prev_month)
                            if line.prop('class') is None:
                                comment_txt += line.getContent()+"n"
                        comments.append({
                            "content": comment_txt[:-1],
                            "date": comment_date,
                            "user_name": username,
                        })
                except:
                    pass
                api_notify_one_result({
                    "id": "",
                    "label": label,
                    "date": date,
                    "size": size,
                    "seeders": seeders,
                    "leechers": leechers,
                    "link": torrent_link,
                    "poster": poster,
                    "comments": comments,
                })
            except:
                pass
            if self.api.stop_search:
                return
        if not self.api.stop_search:
            nav = self.api.find_elements(
                tree.getRootElement(), "div", id="nav_mod_torrents")
            if nav:
                nav = self.api.find_elements(
                    nav[0], "div", **{'class': 'right'})
                if nav and nav[0].prop('style') != 'visibility: hidden':
                    self.run_search(pattern, param, urllib.basejoin(page_url, self.api.find_elements(
                        nav[0], "a")[0].prop('href')), year, prev_month)
