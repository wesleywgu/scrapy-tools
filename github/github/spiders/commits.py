from datetime import datetime, timezone, timedelta

import scrapy
from github.items import CommitItem

try:
    from scrapy.spiders import Spider, Rule
except:
    from scrapy.spiders import BaseSpider as Spider
from github.items import *
from misc.db import MySQLUtil
from scrapy.utils.project import get_project_settings


class githubCommitsSpider(Spider):
    name = "commits"
    allowed_domains = ["github.com"]
    env = get_project_settings()['MACHINE_ENV']

    def start_requests(self):
        if self.env == 'online':
            db = MySQLUtil('192.168.1.2', 3366, 'root', 'gw201221', 'pdd')
            results = db.execute(
                "select channel_url from pdd_monitor_source where name<>'Github' and channel='Github' and url_grade between 1 and 3")

            for row in results:
                today = datetime.now().date()
                today_str = today.strftime("%Y-%m-%d")
                yesterday_str = (today - timedelta(days=30)).strftime("%Y-%m-%d")
                url = row[0] + "?tab=overview&from={from_date}&to={to_date}".format(from_date=yesterday_str,
                                                                                    to_date=today_str)
                self.logger.debug(url)
                yield scrapy.Request(url=url, callback=self.parse_link_urls)
        else:
            urls = [
                # "https://github.com/flankerhqd?tab=overview&from=2023-10-23&to=2023-11-22",
                "https://github.com/easychen?tab=overview&from=2023-10-23&to=2023-11-22",
            ]
            for url in urls:
                yield scrapy.Request(url=url, callback=self.parse_link_urls)

    def parse_link_urls(self, response):
        cards = response.css('span.width-fit')
        for card in cards:
            repository = card.xpath('//a[@data-hovercard-type="repository"]/@href').get()
            url = 'https://github.com' + repository + '/commits'
            yield scrapy.Request(url=url, callback=self.parse)

        cards = response.css('li.ml-0.py-1.d-flex')
        for card in cards:
            repository = card.xpath('//a[@data-hovercard-type="repository"]/@href').get()
            url = 'https://github.com' + repository + '/commits'
            yield scrapy.Request(url=url, callback=self.parse2)

    def parse(self, response):
        cards = response.css('div.flex-auto.min-width-0.js-details-container.Details')
        for card in cards:
            commit = CommitItem()
            url = card.css('p.mb-1 a::attr(href)').get()
            commit['url'] = 'https://github.com' + url

            commit['content'] = card.css('p.mb-1 a::text').get()
            commit['author'] = card.css('span.commit-author.user-mention::text').get()

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

    def parse2(self, response):
        cards = response.xpath('//*[@id="repo-content-pjax-container"]/div/div[3]/div')
        for card in cards:
            commit = CommitItem()
            url = card.xpath('./div[2]/ol/li[1]/div[1]/p/a[3]/@href').get()
            if not url:
                url = card.xpath('./div[2]/ol/li/div[1]/p/a/@href').get()
            commit['url'] = 'https://github.com' + url

            commit['content'] = card.css('p.mb-1 a::text').get()
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
