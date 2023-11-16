from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta

import scrapy

try:
    from scrapy.spiders import Spider
except:
    from scrapy.spiders import BaseSpider as Spider
from github.items import *
from bs4 import BeautifulSoup


class githubSpider(Spider):
    name = "search"
    allowed_domains = ["github.com"]
    start_urls = [
        "https://github.com/search?q=pdd&type=repositories",
    ]

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
            i['repo_name'] = repo_name
            i['desc'] = desc
            i['last_update'] = last_update
            i['url'] = 'https://github.com' + url
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
