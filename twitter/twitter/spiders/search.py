from queue import Queue
from random import randint
from datetime import datetime, timezone, timedelta
from random import randint
from time import sleep

from scrapy import Request
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from twitter.items import twitterItem

from misc.db import MySQLUtil

try:
    from scrapy.spiders import Spider
except:
    from scrapy.spiders import BaseSpider as Spider

from misc.reqs import SeleniumRequest
from scrapy.utils.project import get_project_settings

from misc.env import CookerHelper

# 解决could not get source code的问题
import scrapy.utils.misc
import scrapy.core.scraper


def warn_on_generator_with_return_value_stub(spider, callable):
    pass


scrapy.utils.misc.warn_on_generator_with_return_value = warn_on_generator_with_return_value_stub
scrapy.core.scraper.warn_on_generator_with_return_value = warn_on_generator_with_return_value_stub


class twitterSpider(Spider):
    name = "search"
    allowed_domains = ["twitter.com"]
    env = get_project_settings()['MACHINE_ENV']
    cookie_dict = CookerHelper().get_cookie_dict('.twitter.com')
    all_urls = Queue(maxsize=0)

    dev_urls = [
        'https://twitter.com/search?q=%23pdd&src=typed_query&f=top',
        'https://twitter.com/search?q=%23pinduoduo&src=typed_query&f=top',
        # 'https://twitter.com/search?q=%23temu&src=typed_query&f=top',
        # 'https://twitter.com/search?q=%23拼多多&src=typed_query&f=top',
        # 'https://twitter.com/search?q=%23pdd&src=typed_query&f=media',
        # 'https://twitter.com/search?q=%23pinduoduo&src=typed_query&f=media',
        # 'https://twitter.com/search?q=%23temu&src=typed_query&f=media',
        # 'https://twitter.com/search?q=%23拼多多&src=typed_query&f=media',
        # 'https://twitter.com/search?q=%23pdd&src=typed_query&f=live',
        # 'https://twitter.com/search?q=%23pinduoduo&src=typed_query&f=live',
        # 'https://twitter.com/search?q=%23temu&src=typed_query&f=live',
        # 'https://twitter.com/search?q=%23拼多多&src=typed_query&f=live',
        # 'https://twitter.com/search?q=pdd&src=typed_query',
        # 'https://twitter.com/search?q=pinduoduo&src=typed_query',
        # 'https://twitter.com/search?q=temu&src=typed_query',
        # 'https://twitter.com/search?q=拼多多&src=typed_query',
    ]

    def start_requests(self):
        if self.env == 'online':
            db = MySQLUtil('192.168.1.253', 3366, 'root', 'gw201221', 'pdd')
            self.logger.debug("execute start_requests start query sql")
            results = db.execute(
                "select channel_url from pdd_monitor_source where name='Twitter' and url_grade between 1 and 2")
            self.logger.debug("execute start_requests finish query sql")
            for row in results:
                url = row[0]
                self.logger.info(url)

            for row in results:
                url = row[0]
                self.all_urls.put(url)

            yield SeleniumRequest(url=self.all_urls.get(), callback=self.parse_result, cookies=self.cookie_dict)
        else:
            yield SeleniumRequest(url=self.dev_urls[0], callback=self.parse_result, cookies=cookie_dict)

    def parse_result(self, response):
        browser = response.meta['driver']

        final_tweets = {}

        # 模拟多次滚动
        for _ in range(10):
            sleep(2)

            part_tweets = self.get_tweets(browser)
            final_tweets.update(part_tweets)

            self.scroll_down(browser)

        for i in final_tweets.values():
            yield i

        if self.env == 'online':
            if not self.all_urls.empty():
                url = self.all_urls.get()
                yield SeleniumRequest(url=url, callback=self.parse_result, cookies=self.cookie_dict)
        else:
            yield SeleniumRequest(url=self.dev_urls[1], callback=self.parse_result, cookies=self.cookie_dict)

    def scroll_down(self, browser) -> None:
        """Helps to scroll down web page"""
        try:
            body = browser.find_element(By.CSS_SELECTOR, 'body')
            for _ in range(randint(1, 3)):
                body.send_keys(Keys.PAGE_DOWN)
        except Exception as ex:
            print("Error at scroll_down method {}".format(ex))

    def get_tweets(self, browser):
        # 提取数据
        tweets = {}
        page_cards = browser.find_elements(by=By.XPATH, value='//article[@data-testid="tweet"]')
        for card in page_cards:
            tweet = twitterItem()
            try:
                tweet['author'] = card.find_element(by=By.XPATH, value='.//span').text

                utc_time_str = card.find_element(by=By.XPATH, value='.//time').get_attribute('datetime')
                # 将UTC时间字符串转换为datetime对象
                utc_time = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                # 创建时区对象，表示中国的时区为东八区
                china_timezone = timezone(timedelta(hours=8))
                # 将UTC时间转换为中国本地时间
                china_time = utc_time.replace(tzinfo=timezone.utc).astimezone(china_timezone)
                # 格式化为指定格式的字符串
                tweet['pub_time'] = china_time.strftime("%Y-%m-%d %H:%M:%S")

                tweet['content'] = card.find_element(by=By.XPATH, value='.//div[@dir="auto"]').text.replace('\n', '')
                tweet['url'] = card.find_element(by=By.XPATH, value='.//a[contains(@href, "/status/")]').get_attribute(
                    'href')

                time_now = datetime.now()
                current_time = time_now.strftime("%Y-%m-%d %H:%M:%S")
                tweet['craw_time'] = current_time
                tweet['source_url'] = browser.current_url

                tweets[tweet['url']] = tweet
            except:
                pass
        return tweets
