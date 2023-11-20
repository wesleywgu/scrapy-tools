from urllib.parse import urlparse

import scrapy

from github.items import CommitItem
from datetime import datetime, timezone, timedelta

from scrapy import Request

try:
    from scrapy.spiders import Spider
except:
    from scrapy.spiders import BaseSpider as Spider
from github.items import *
from misc.db import MySQLUtil


class githubSpider(Spider):
    name = "commits"
    allowed_domains = ["github.com"]
    start_urls = [
        "https://github.com/easychen/github-action-server-chan/commits?author=easychen&since=2023-11-31&until=2023-11-16",
    ]


    db = MySQLUtil('192.168.1.2', 3366, 'root', 'gw201221', 'pdd')

    def start_requests(self):
        self.logger.debug("execute start_requests start query sql")
        results = self.db.execute("select channel_url from pdd_monitor_source where name='Github'")
        self.logger.debug("execute start_requests finish query sql")
        for row in results:
            url = row[0]
            self.logger.debug(url)
            yield Request(url=url, callback=self.parse)

    def parse(self, response):
        cards = response.xpath('//*[@id="repo-content-pjax-container"]/div/div[3]/div')
        for card in cards:
            commit = CommitItem()
            commit['url'] = 'https://github.com/' + card.xpath('./div[2]/ol/li[1]/div[1]/p/a[3]/@href').get()
            commit['title'] = card.css('p.mb-1 a:nth-of-type(3)::text').get()
            commit['author'] = card.css('a.commit-author.user-mention::text').get()

            utc_time_str = card.xpath('//relative-time/@datetime').get()
            # 将UTC时间字符串转换为datetime对象
            utc_time = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")
            # 创建时区对象，表示中国的时区为东八区
            china_timezone = timezone(timedelta(hours=8))
            # 将UTC时间转换为中国本地时间
            china_time = utc_time.replace(tzinfo=timezone.utc).astimezone(china_timezone)
            # 格式化为指定格式的字符串
            commit['pub_time'] = china_time.strftime("%Y-%m-%d %H:%M:%S")

            time_now = datetime.now()
            current_time = time_now.strftime("%Y-%m-%d %H:%M:%S")
            commit['craw_time'] = current_time
            commit['source_url'] = response.request.url

            yield commit
