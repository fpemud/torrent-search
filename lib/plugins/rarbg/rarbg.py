#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import time
import urllib.parse
import selenium
from selenium.webdriver.support import wait as swait


class RARBGTorrentPlugin:

    def __init__(self):
        self.WEBSITE_URL = "https://rarbgprx.org"

    def run_search(self, param, pattern, href=None):
        driver = param["selenium-driver"]
        api_notify_results_total_count = param["notify-results-total-count"]
        api_notify_one_result = param["notify-one-result"]
        api_is_stopping = param["is-stopping"]

        if href is None:
            # load a dummy page so that we can set cookies before we load the main page, selenium sucks
            driver.get(self.WEBSITE_URL + "/index10.html")
            driver.add_cookie({"name": "skt", "value": "na5cocrnzk"})
            driver.add_cookie({"name": "gaDts48g", "value": "q8h5pp9t"})
            driver.add_cookie({"name": "aby", "value": "2"})
            driver.add_cookie({"name": "ppu_main_9ef78edf998c4df1e1636c9a474d9f47", "value": "1"})
            driver.add_cookie({"name": "ppu_sub_9ef78edf998c4df1e1636c9a474d9f47", "value": "1"})
            driver.add_cookie({"name": "expla", "value": "1"})

            # do search
            driver.get(self.WEBSITE_URL + "/torrents.php?search=" + urllib.parse.quote_plus(pattern))
        else:
            # continue search
            driver.get(self.WEBSITE_URL + href)

        # click fullscreen ads and close popup window
        while True:
            wh = driver.current_window_handle
            action = selenium.webdriver.common.action_chains.ActionChains(driver)
            action.move_by_offset(1, 1)     # move cursor from default (0,0)
            action.click()
            action.perform()
            if not _seleniumClosePopupIfExists(driver, wh):
                break

        # get categories
        categories = {}
        driver.find_element_by_id("shadvbutton").click()            # make categories visible
        for cat in driver.find_elements_by_xpath("//input[@name='category[]']"):
            atag = cat.find_element_by_xpath("following-sibling::*[1]")
            swait.WebDriverWait(driver, 60).until(lambda x: atag.text != "")
            categories[cat.get_attribute('value')] = atag.text
        print(categories)

        # get results total count
        if True:
            div = driver.find_element_by_xpath("//div[@id='pager_links']")
            btag = div.find_element_by_tag_name("b")
            curPage = int(btag.text)

            itemList = driver.find_elements_by_xpath("//tr[@class='lista2']")
            curPageCount = len(itemList)

            cur_total_count = (curPage - 1) * 25 + curPageCount
            api_notify_results_total_count(cur_total_count)
        print(cur_total_count)

        # get results
        for item in driver.find_elements_by_xpath("//tr[@class='lista2']"):
            ilist = item.find_elements_by_tag_name("td")
            assert len(ilist) == 8
            cat = ilist[0]
            link = ilist[1]
            date = ilist[2]
            size = ilist[3]
            seeders = ilist[4]
            leechers = ilist[5]
            comments = ilist[6]
            c = ilist[7]

            print(cat.text)
            print(link.text)
            print(date.text)
            print(size.text)
            print(seeders.text)
            print(leechers.text)
            print(comments.text)
            print(c.text)

            if api_is_stopping():
                return

        #     cat = cat.find_element_by_tag_name("a").get_attribute('href')
        #     j = cat.index('=')
        #     cat = cat[j+1:]
        #     if cat in categories:
        #         cat = categories[cat]
        #     else:
        #         cat = ""
        #     cat = self._parseCat(cat)
        #     link = self.api.find_elements(link, "a")[0]
        #     label = link.getContent()
        #     link = urllib.basejoin(href, link.prop('href'))
        #     hashvalue = link.split('/')[-2]
        #     date = self._parseDate(date.getContent())
        #     size = size.getContent()
        #     seeders = eval(seeders.getContent())
        #     leechers = eval(leechers.getContent())
        #     nb_comments = eval(comments.getContent())

        #     api_notify_one_result({
        #         "id": reflink + " " + label,
        #         "label": label,
        #         "date": date,
        #         "size": size,
        #         "seeders": seeders,
        #         "leechers": leechers,
        #         "link": link,
        #         "hashvalue": hashvalue,
        #         "category": cat,
        #         "nb_comments": nb_comments,
        #     })

        # next page
        div = driver.find_element_by_xpath("//div[@id='pager_links']")
        btag = div.find_element_by_tag_name("b")
        try:
            atag = btag.find_element_by_xpath("following-sibling::*[1]")
            href = atag.get_attribute('href').replace(self.WEBSITE_URL, "")     # it's really sucks that selenium auto converts relative href in html to absolute url!
            self.run_search(param, pattern, href)
        except selenium.common.exceptions.NoSuchElementException:
            # it's the last page
            pass

    def load_poster(self, result_id):
        return self._do_get_details(result_id, "poster")

    def load_filelist(self, result_id):
        return self._do_get_details(result_id, "filelist")

    def load_comments(self, result_id):
        return self._do_get_details(result_id, "comments")

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

    def _do_get_details(self, result_id, which):
        tl = result_id.split(" ")
        reflink = tl[0]
        label = tl[1]

        c = httplib2.Http()
        resp, content = c.request(reflink)
        tree = libxml2.htmlParseDoc(content, "utf-8")
        self._link = urllib.basejoin(reflink, self.api.find_elements(tree.getRootElement(
        ), "a", onmouseover="return overlib('Click here to download torrent')")[0].prop('href'))

        if which == "poster":
            img = self.api.find_elements(tree.getRootElement(), "img", alt=label)
            if img:
                return img[0].prop('src')
            else:
                return None

        if which == "filelist":
            files_div = self.api.find_elements(tree.getRootElement(), "div", id="files")
            filelist = []
            if len(files_div) == 1:
                files_div = files_div[0]
                for item in self.api.find_elements(files_div, "tr")[1:]:
                    filename, size = self.api.find_elements(item, "td")
                    filename = filename.getContent()
                    size = size.getContent()
                    filelist.append({
                        "filename": filename,
                        "size": size
                    })
            return filelist

        if which == "comments":
            comments_link = self.api.find_elements(tree.getRootElement(), "a", name="comments")
            comments = []
            try:
                if len(comments_link) == 1:
                    node = comments_link[0]
                    while node.name != "table":
                        node = node.__next__
                    comments_lines = self.api.find_elements(node, "tr")
                    for item in range(len(comments_lines)/2):
                        username, date = self.api.find_elements(
                            comments_lines[2*item], "td")
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
                            comments_lines[2*item+1], "td")[1].getContent()

                        comments.append({
                            "content": content,
                            "date": date,
                            "user_name": username,
                        })
            except:
                pass
            return comments


        # def _cond_threat_defence(drv):
        #     return drv.current_url == "https://rarbgprx.org/threat_defence.php?defence=nojc" and \
        #            drv.find_element_by_link_text("Click here") is not None

        # def _cond_normal(drv):
        #     return drv.current_url.startswith("https://rarbgprx.org/torrents.php?r=69298267")

        # W_WAIT(driver, 60).until(lambda x: _cond_threat_defence(x) or _cond_normal(x))
        # if _cond_threat_defence(driver):
        #     time.sleep(1.0)
        #     driver.find_element_by_link_text("Click here").click()

        #     W_WAIT(driver, 10).until(lambda x: x.find_element_by_id("solve_string") is not None and x.find_element_by_xpath("//img[start-with(@src,'/threat_captcha.php')]") is not None)

        #     time.sleep(1.0)
        #     driver.find_element_by_id("solve_string").send_keys("123456")

        # elif _cond_normal(driver):
        #     pass
        # else:
        #     assert False

        # return



def _seleniumClosePopupIfExists(driver, originalWindowHandle):
    """len(driver.window_handles) must be 1 before calling this function"""

    # wait popup window comes up
    try:
        W = selenium.webdriver.support.wait.WebDriverWait
        W(driver, 1).until(lambda x: len(x.window_handles) > 1)
    except selenium.common.exceptions.TimeoutException:
        # no popup, do nothing
        return False

    # swith to it and close
    # selenium should support close speicifed window...
    handles = list(driver.window_handles)
    handles.remove(originalWindowHandle)
    driver.switch_to.window(handles[0])
    driver.close()

    # switch back to original window
    driver.switch_to.window(originalWindowHandle)

    return True
