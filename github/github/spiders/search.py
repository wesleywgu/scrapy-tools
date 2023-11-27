from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta

import scrapy
from scrapy import Request

try:
    from scrapy.spiders import Spider
except:
    from scrapy.spiders import BaseSpider as Spider
from github.items import *
from bs4 import BeautifulSoup

from misc.db import MySQLUtil
from scrapy.utils.project import get_project_settings


class githubSearchSpider(Spider):
    name = "search"
    allowed_domains = ["github.com"]
    env = get_project_settings()['MACHINE_ENV']

    def start_requests(self):
        if self.env == 'online':
            db = MySQLUtil('192.168.1.2', 3366, 'root', 'gw201221', 'pdd')
            self.logger.debug("execute start_requests start query sql")
            results = db.execute(
                "select channel_url from pdd_monitor_source where name='Github' and url_grade between 1 and 2")
            self.logger.debug("execute start_requests finish query sql")
            for row in results:
                url = row[0]
                self.logger.info(url)
                yield Request(url=url, callback=self.parse)
        else:
            urls = [
                'https://github.com/search?q=pdd&type=repositories&s=updated&o=desc',
                'https://github.com/search?q=pinduoduo&type=repositories&s=updated&o=desc',
                'https://github.com/search?q=temu&type=repositories&s=updated&o=desc',
                'https://github.com/search?q=拼多多&type=repositories&s=updated&o=desc',
            ]
            for url in urls:
                yield Request(url=url, callback=self.parse)

    def parse(self, response):
        cards = response.css('div.Box-sc-g0xbh4-0.jUbAHB')
        for card in cards:
            desc = card.css('span.Text-sc-17v1xeu-0.kWPXhV.search-match').extract()
            soup = BeautifulSoup(''.join(desc), 'html.parser')
            desc = soup.get_text()

            time_str = card.css('span[title]::attr(title)').get()
            # 将时间字符串解析为datetime对象
            time_object = datetime.strptime(time_str, "%b %d, %Y, %I:%M %p %Z")
            # 创建时区对象，表示中国的时区为东八区
            china_timezone = timezone(timedelta(hours=8))
            # 将时间转换为中国本地时间
            china_time = time_object.replace(tzinfo=timezone.utc).astimezone(china_timezone)
            # 格式化为指定格式的字符串
            last_update = china_time.strftime("%Y-%m-%d %H:%M:%S")

            url = card.css('a.Link__StyledLink-sc-14289xe-0.fIqerb::attr(href)').get()
            repo_name = url.strip('/')

            i = githubItem()
            i['content'] = repo_name + ' ## ' + desc
            i['pub_time'] = last_update
            i['url'] = 'https://github.com' + url
            i['author'] = url.strip('/').split('/')[0]

            time_now = datetime.now()
            current_time = time_now.strftime("%Y-%m-%d %H:%M:%S")
            i['craw_time'] = current_time
            i['source_url'] = response.request.url

            yield i

        # 下一页
        next_url = response.xpath('//a[@rel="next"]/@href').extract_first()
        if next_url:
            o = urlparse(next_url)
            for i in o.query.split('&'):
                if 'p=' in i:
                    num = int(i.split('=')[1])
                    if num <= 5:  # 最多爬取5页
                        yield scrapy.Request(url=next_url, callback=self.parse)
