from urllib.parse import urlparse

import scrapy

try:
    from scrapy.spiders import Spider
except:
    from scrapy.spiders import BaseSpider as Spider
from github.items import *


class githubSpider(Spider):
    name = "github"
    allowed_domains = ["github.com"]
    start_urls = [
        "https://github.com/search?q=pdd&type=repositories",
    ]

    def parse(self, response):
        cards = response.css('div.Box-sc-g0xbh4-0.jUbAHB')
        for card in cards:
            # Assuming the span is present on the page
            desc = card.css('span.Text-sc-17v1xeu-0.kWPXhV.search-match').extract()

            last_update = card.css('span[title]::attr(title)').get()
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
