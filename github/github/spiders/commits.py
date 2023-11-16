from urllib.parse import urlparse

import scrapy

from github.items import CommitItem
from datetime import datetime, timezone, timedelta

try:
    from scrapy.spiders import Spider
except:
    from scrapy.spiders import BaseSpider as Spider
from github.items import *


class githubSpider(Spider):
    name = "commits"
    allowed_domains = ["github.com"]
    start_urls = [
        "https://github.com/easychen/github-action-server-chan/commits?author=easychen&since=2023-11-31&until=2023-11-16",
    ]

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
            commit['time'] = china_time.strftime("%Y-%m-%d %H:%M:%S")
            yield commit
