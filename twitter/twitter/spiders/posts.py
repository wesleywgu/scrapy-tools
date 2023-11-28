from queue import Queue
from random import randint
from datetime import datetime, timezone, timedelta
from random import randint
from time import sleep

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from twitter.items import twitterItem

from misc.db import MySQLUtil

try:
    from scrapy.spiders import Spider
except:
    from scrapy.spiders import BaseSpider as Spider

from misc.requests import SeleniumRequest
from scrapy.utils.project import get_project_settings

from misc.env import CookerHelper


class twitterSpider(Spider):
    name = "posts"
    allowed_domains = ["twitter.com"]
    env = get_project_settings()['MACHINE_ENV']

    cookie_dict = CookerHelper().get_cookie_dict('.twitter.com')

    dev_urls = [
        'https://twitter.com/flanker_hqd',
        'https://twitter.com/ResearchGrizzly',
    ]

    all_urls = Queue(maxsize=0)

    def start_requests(self):
        if self.env == 'online':
            db = MySQLUtil('192.168.1.2', 3366, 'root', 'gw201221', 'pdd')
            self.logger.debug("execute start_requests start query sql")
            results = db.execute(
                "select channel_url from pdd_monitor_source where channel='Twitter' and name <> 'Twitter' and url_grade between 1 and 2")
            self.logger.debug("execute start_requests finish query sql")
            for row in results:
                url = row[0]
                self.logger.info(url)
                self.all_urls.put(url)

            yield SeleniumRequest(url=self.all_urls.get(), callback=self.parse_result, cookies=self.cookie_dict)
        else:
            yield SeleniumRequest(url=self.dev_urls[0], callback=self.parse_result, cookies=self.cookie_dict)

    def parse_result(self, response):
        browser = response.meta['driver']

        final_tweets = {}
        # 模拟多次滚动
        for _ in range(10):
            # 等待动态内容加载
            sleep(2)
            part_tweets = self.get_tweets(browser)
            final_tweets.update(part_tweets)

            self.scroll_down(browser, response.request.url)

        for i in final_tweets.values():
            yield i

        if self.env == 'online':
            if not self.all_urls.empty():
                url = self.all_urls.get()
                yield SeleniumRequest(url=url, callback=self.parse_result, cookies=self.cookie_dict)
        else:
            yield SeleniumRequest(url=self.dev_urls[1], callback=self.parse_result, cookies=self.cookie_dict)

    def scroll_down(self, browser, url) -> None:
        """Helps to scroll down web page"""
        try:
            body = browser.find_element(By.CSS_SELECTOR, 'body')
            for _ in range(randint(1, 3)):
                body.send_keys(Keys.PAGE_DOWN)
                self.logger.debug("process_request scroll_down, url= %s" % url)
        except Exception as ex:
            self.logger.error("Error at scroll_down method {}".format(ex))

    def get_tweets(self, browser):
        # 提取数据
        tweets = {}
        page_cards = browser.find_elements(by=By.XPATH, value='//div[@data-testid="cellInnerDiv"]')
        for card in page_cards:
            tweet = twitterItem()
            try:
                tweet['url'] = card.find_element(by=By.XPATH, value='.//a[contains(@href, "/status/")]').get_attribute(
                    'href')
                try:
                    retweet_words = card.find_element(by=By.XPATH,
                                                      value='.//span[@data-testid="socialContext"]').text
                except Exception as ex:
                    retweet_words = ''

                if 'reposted' in retweet_words:
                    tweet['author'] = card.find_element(by=By.XPATH,
                                                        value='//span[@data-testid="socialContext"]/span/span').text
                    tweet['url'] = tweet['url'] + "&retweet=" + tweet['author']
                else:
                    tweet['author'] = card.find_element(by=By.XPATH, value='.//a/div/div[@dir="ltr"]/span/span').text

                utc_time_str = card.find_element(by=By.XPATH, value='.//time').get_attribute('datetime')
                # 将UTC时间字符串转换为datetime对象
                utc_time = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                # 创建时区对象，表示中国的时区为东八区
                china_timezone = timezone(timedelta(hours=8))
                # 将UTC时间转换为中国本地时间
                china_time = utc_time.replace(tzinfo=timezone.utc).astimezone(china_timezone)
                # 格式化为指定格式的字符串
                tweet['pub_time'] = china_time.strftime("%Y-%m-%d %H:%M:%S")

                text_parts = card.find_elements(by=By.XPATH, value='.//div[@dir="auto"]/*')
                tweet['content'] = ''
                for i in text_parts:
                    tweet['content'] = tweet['content'] + i.text

                time_now = datetime.now()
                current_time = time_now.strftime("%Y-%m-%d %H:%M:%S")
                tweet['craw_time'] = current_time
                tweet['source_url'] = browser.current_url

                tweets[tweet['url']] = tweet
            except:
                pass
        return tweets
