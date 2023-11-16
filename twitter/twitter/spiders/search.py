import os
import re
import sys
import time
from time import sleep

from selenium.webdriver.common.by import By

from twitter.items import twitterItem

try:
    from scrapy.spiders import Spider
except:
    from scrapy.spiders import BaseSpider as Spider

from misc.Requests import SeleniumRequest


class twitterSpider(Spider):
    name = "search"
    allowed_domains = ["twitter.com"]
    start_urls = [
        "https://twitter.com/search?q=%E6%8B%BC%E5%A4%9A%E5%A4%9A&src=typed_query",
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
        # 模拟多次滚动
        for _ in range(5):
            # 提取数据
            page_cards = browser.find_elements(by=By.XPATH, value='//article[@data-testid="tweet"]')
            for card in page_cards:
                tweet = self.get_data(card)

                if tweet:
                    i = twitterItem()
                    i['user_name'] = tweet['user_name']
                    i['pub_time'] = tweet['pub_time']
                    i['text'] = tweet['text']
                    i['post_url'] = tweet['post_url']
                    yield i

            browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            # 等待动态内容加载
            self.wait_for_content_to_load(browser)
            # waiting 2 seconds for the products to load
            time.sleep(2)



    def wait_for_content_to_load(self, browser):
        # 自定义等待条件，确保内容加载完毕
        sleep(5)

    def get_data(self, card):
        """Extract data from tweet card"""
        image_links = []

        try:
            username = card.find_element(by=By.XPATH, value='.//span').text
        except:
            return

        try:
            handle = card.find_element(by=By.XPATH, value='.//span[contains(text(), "@")]').text
        except:
            return

        try:
            postdate = card.find_element(by=By.XPATH, value='.//time').get_attribute('datetime')
        except:
            return

        try:
            text = card.find_element(by=By.XPATH, value='.//div[2]/div[2]/div[1]').text
        except:
            text = ""

        try:
            embedded = card.find_element(by=By.XPATH, value='.//div[2]/div[2]/div[2]').text
        except:
            embedded = ""

        # text = comment + embedded

        try:
            reply_cnt = card.find_element(by=By.XPATH, value='.//div[@data-testid="reply"]').text
        except:
            reply_cnt = 0

        try:
            retweet_cnt = card.find_element(by=By.XPATH, value='.//div[@data-testid="retweet"]').text
        except:
            retweet_cnt = 0

        try:
            like_cnt = card.find_element(by=By.XPATH, value='.//div[@data-testid="like"]').text
        except:
            like_cnt = 0

        try:
            elements = card.find_elements(by=By.XPATH,
                                          value='.//div[2]/div[2]//img[contains(@src, "https://pbs.twimg.com/")]')
            for element in elements:
                image_links.append(element.get_attribute('src'))
        except:
            image_links = []

        # if save_images == True:
        #	for image_url in image_links:
        #		save_image(image_url, image_url, save_dir)
        # handle promoted tweets

        try:
            promoted = card.find_element(by=By.XPATH, value='.//div[2]/div[2]/[last()]//span').text == "Promoted"
        except:
            promoted = False
        if promoted:
            return

        # get a string of all emojis contained in the tweet
        try:
            emoji_tags = card.find_elements(by=By.XPATH, value='.//img[contains(@src, "emoji")]')
        except:
            return
        emoji_list = []
        for tag in emoji_tags:
            try:
                filename = tag.get_attribute('src')
                emoji = chr(int(re.search(r'svg\/([a-z0-9]+)\.svg', filename).group(1), base=16))
            except AttributeError:
                continue
            if emoji:
                emoji_list.append(emoji)
        emojis = ' '.join(emoji_list)

        # tweet url
        try:
            element = card.find_element(by=By.XPATH, value='.//a[contains(@href, "/status/")]')
            tweet_url = element.get_attribute('href')
        except:
            return

        tweet = {
            'user_name': username
            , 'user_id': handle
            , 'pub_time': postdate
            , 'text': text
            , 'post_url': tweet_url
        }
        # username, handle, postdate, text, embedded, emojis, reply_cnt, retweet_cnt, like_cnt, image_links,
        # tweet_url)
        return tweet

    # def parse(self, response):
    #     page_cards = response.xpath('//article[@data-testid="tweet"]')
    #
    #     for card in page_cards:
    #         username = card.xpath('.//span/text()').get()
    #         user_id = card.xpath('.//span[contains(text(), "@")]/text()').get()
    #         postdate = card.xpath('.//time/@datetime').get()
    #         spans = card.xpath('.//div[@class="css-1dbjc4n"]/div/span/text()')
    #         text = ''.join(spans.get())
    #         tweet_url = 'https://twitter.com' + card.xpath('.//a[contains(@href, "/status/")]/@href').get()
    #
    #         i = twitterItem()
    #         i['user_name'] = username
    #         i['user_id'] = user_id
    #         i['pub_time'] = postdate
    #         i['text'] = text
    #         i['post_url'] = tweet_url
    #         yield i
