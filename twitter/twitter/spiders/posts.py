import os
import re
import sys
import time
from random import randint
from time import sleep

from selenium.webdriver.common.by import By

from twitter.items import twitterItem
from selenium.webdriver import ActionChains, Keys
from datetime import datetime, timezone, timedelta

try:
    from scrapy.spiders import Spider
except:
    from scrapy.spiders import BaseSpider as Spider

from misc.requests import SeleniumRequest


class twitterSpider(Spider):
    name = "posts"
    allowed_domains = ["twitter.com"]
    start_urls = [
        'https://twitter.com/oldamnnt',
    ]

    def start_requests(self):
        cookie = 'guest_id=v1%3A169968367202280499;g_state={"i_l":0};att=1-dzYe81dA9PL6dptTn3sZpKUJk31cu6339OVFBLgO;_ga=GA1.2.1319796421.1699597109;_gid=GA1.2.2130692126.1699597109;_twitter_sess=BAh7CSIKZmxhc2hJQzonQWN0aW9uQ29udHJvbGxlcjo6Rmxhc2g6OkZsYXNo%250ASGFzaHsABjoKQHVzZWR7ADoPY3JlYXRlZF9hdGwrCIilCr2LAToMY3NyZl9p%250AZCIlOGVhNmZiZjUxYmE4YTE3OTRkZDE5NTY2ZmFhZjNlY2E6B2lkIiVkZjYz%250AMjJhMmE2NTY1YWNmZWYxZWRhNGNhZDYzMDZkMg%253D%253D--24df1129995c212d72d70c6d6bf5a727e95e8b2a;auth_token=efe92a784d7aa0d935a4e165ec4c3bab101b8076;ct0=fb069b093d3e476ea39a67904407e8ee28797b2b676f1893ff58ec4f42f2484e3231ad7f447cb068fbd82d5c5dc8e9752c8f553ef467dc9d97e0d7a7db83d0a370e5508af6e25d83dbb3f8e9c38a3297;external_referer=8e8t2xd8A2w%3D|0|GlWr2u5wzZipnVja1ZbglPkPMjOgQE2KgmAMWWfTCXhp0%2FHSfkOhmd2TJyvExtBN%2F%2Fijlay3pIcy7kTdifa%2FvLWqgGPAyxd2cO5nc7nz8Hg%3D;gt=1723231481634697629;guest_id_ads=v1%3A169968367202280499;guest_id_marketing=v1%3A169968367202280499;kdt=23e1xveFWder6tur8CAqZUHOSvgOXpLHYvAeYXjw;lang=en;personalization_id="v1_+0NoU2o1Kh26meEnQAjj+w==";twid=u%3D1405533540540813314'

        cookie_dict = {}
        for cookie_pair in cookie.split(';'):
            key = cookie_pair.split('=')[0]
            value = cookie_pair.split('=')[1]
            cookie_dict[key] = value

        for url in self.start_urls:
            yield SeleniumRequest(url=url, callback=self.parse_result, cookies=cookie_dict)

    def parse_result(self, response):
        browser = response.meta['driver']

        final_tweets = {}
        # 模拟多次滚动
        for _ in range(10):
            # 等待动态内容加载
            sleep(2)
            part_tweets = self.get_tweets(browser)
            final_tweets.update(part_tweets)

            self.scroll_down(browser)

        for i in final_tweets.values():
            yield i

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
        page_cards = browser.find_elements(by=By.XPATH, value='//div[@data-testid="cellInnerDiv"]')
        for card in page_cards:
            tweet = twitterItem()
            try:
                tweet['user_name'] = card.find_element(by=By.XPATH, value='.//a/div/div[@dir="ltr"]/span/span').text

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
                tweet['text'] = ''
                for i in text_parts:
                    tweet['text'] = tweet['text'] + i.text

                tweet['url'] = card.find_element(by=By.XPATH,value='.//a[contains(@href, "/status/")]').get_attribute('href')

                time_now = datetime.now()
                current_time = time_now.strftime("%Y-%m-%d %H:%M:%S")
                tweet['craw_time'] = current_time
                tweet['source_url'] = browser.current_url

                tweets[tweet['url']] = tweet
            except:
                pass
        return tweets
