import math
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Union
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import scrapy
from scrapy import Request

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup

from items import BaiduNewsItem

try:
    from scrapy.spiders import Spider
except:
    from scrapy.spiders import BaseSpider as Spider

import misc.log as log
from misc.db import MySQLUtil
from scrapy.utils.project import get_project_settings


class baiduSpider(Spider):
    name = "news"
    allowed_domains = ["baidu.com"]
    env = get_project_settings()['MACHINE_ENV']

    def start_requests(self):
        if self.env == 'online':
            db = MySQLUtil('192.168.1.2', 3366, 'root', 'gw201221', 'pdd')
            self.logger.info("execute start_requests start query sql")
            results = db.execute(
                "select channel_url from pdd_monitor_source where name='百度' and url_grade between 1 and 2")
            self.logger.info("execute start_requests finish query sql")
            for row in results:
                url = row[0]
                self.logger.info(url)

            for row in results:
                url = row[0]
                yield Request(url=url, callback=self.parse)
        else:
            urls = [
                "https://www.baidu.com/s?tn=news&rtt=4&bsst=1&cl=2&wd=temu%20malware&medium=0&pn=0",
                # "https://www.baidu.com/s?tn=news&rtt=4&bsst=1&cl=2&wd=pdd&medium=0&pn=0",
                # "https://www.baidu.com/s?tn=news&rtt=4&bsst=1&cl=2&wd=pinduoduo&medium=0&pn=0",
                # "https://www.baidu.com/s?tn=news&rtt=4&bsst=1&cl=2&wd=temu&medium=0&pn=0",
                # "https://www.baidu.com/s?tn=news&rtt=4&bsst=1&cl=2&wd=拼多多&medium=0&pn=0",
            ]
            for url in urls:
                yield Request(url=url, callback=self.parse)

    def parse(self, response):
        result = self.parse_news(response.text)
        total = result['total']
        for news in result['results']:
            i = BaiduNewsItem()
            i['author'] = news['author']

            if news['date']:
                i['pub_time'] = self.convert_time(news['date']).strftime("%Y-%m-%d %H:%M:%S")
            else:
                i['pub_time'] = '无'
            i['url'] = news['url']
            i['content'] = '标题：{title}\n 内容：{content}'.format(title=news['title'], content=news['des'])

            time_now = datetime.now()
            current_time = time_now.strftime("%Y-%m-%d %H:%M:%S")
            i['craw_time'] = current_time
            i['source_url'] = response.request.url
            yield i

        # 下一页
        current_url = response.request.url
        query_dict = parse_qs(urlparse(current_url).query)
        if 'pn' in query_dict:
            start_num = int(query_dict['pn'][0])
        else:
            start_num = 0

        max_pages = min(5, math.ceil(int(total) / 10))
        current_page = int(start_num / 10) + 1
        if current_page < max_pages:
            next_url = self.replace_field(current_url, 'pn', current_page * 10)
            yield scrapy.Request(url=next_url, callback=self.parse)

    def replace_field(self, url, name, value):
        parse = urlparse(url)
        query = parse.query
        query_pair = parse_qs(query)
        query_pair[name] = value
        new_query = urlencode(query_pair, doseq=True)
        new_parse = parse._replace(query=new_query)
        next_page = urlunparse(new_parse)
        return next_page

    def parse_news(self, content: str) -> dict:
        """解析百度资讯搜索的页面源代码.

        Args:
            content (str): 已经转换为UTF-8编码的百度资讯搜索HTML源码

        Returns:
            dict: 解析后的结果
        """
        bs = BeautifulSoup(self._format(content), "html.parser")

        # 搜索结果总数
        total = int(
            bs.find("div", id="wrapper_wrapper")
            .find("span", class_="nums")
            .text.split("资讯", 1)[-1]
            .split("篇", 1)[0]
            .split("个", 1)[0]
            .replace(",", "")
        )
        # 搜索结果容器
        data = (
            bs.find("div", id="content_left")
            # .findAll("div")[1]
            .findAll("div", class_="result-op")
        )
        results = []
        for res in data:
            # 标题
            title = self._format(res.find("h3").find("a").text)
            # 链接
            url = res.find("h3").find("a")["href"]
            # 简介
            des = (
                res.find("div", class_="c-span-last")
                .find("span", class_="c-color-text")
                .text
            )
            _ = res.find("div", class_="c-span-last")
            # 作者
            author = _.find("span", class_="c-color-gray").text
            # 发布日期
            try:
                date = _.find("span", class_="c-color-gray2").text
            except AttributeError:
                date = None
            # 封面图片
            try:
                cover = res.find("div", class_="c-img-radius-large").find("img")["src"]
            except Exception:
                cover = None
            # 生成结果
            result = {
                "title": title,
                "author": author,
                "date": date,
                "des": des,
                "url": url,
                "cover": cover,
            }
            results.append(result)  # 加入结果
        return {"results": results, "total": total}

    def _format(self, string: str) -> str:
        """去除字符串中不必要的成分并返回

        Args:
            string (str): 要整理的字符串

        Returns:
            str: 处理后的字符串
        """
        text_to_replace = ("\xa0", "\u2002""\u3000")
        string = string.strip()
        for text in text_to_replace:
            string = string.replace(text, "")
        return string

    def convert_time(self, t: str, as_list: bool = False) -> Union[datetime, bool]:
        """转换有时间差的汉字表示的时间到`datetime.datetime`形式的时间

        Args:
            t (str): 要转换的字符串
            as_list (bool): 是否以列表形式返回

        Returns:
            datetime: 转换后的`datetime.datetime`结果
        """
        if not t or not t.strip():
            return None

        t = t.strip()
        days_in_chinese = {"昨天": 1, "前天": 2, "今天": 0}
        if t in days_in_chinese:
            return datetime.now() - timedelta(days=days_in_chinese[t])

        delta = int(re.findall(r"\d+", t)[0])
        # print( t.replace(str(delta), "").strip(), delta)
        if "秒" in t:
            s = datetime.now() - timedelta(seconds=delta)
        elif "分钟" in t:
            s = datetime.now() - timedelta(minutes=delta)
        elif "小时" in t:
            s = datetime.now() - timedelta(hours=delta)
        elif t.replace(str(delta), "").split(":")[0].strip() in days_in_chinese:
            _ = int(re.findall(r"\d+", t)[-1])
            __ = t.replace(str(delta), "").split(":")[0].strip()
            s = datetime.now() - timedelta(days=days_in_chinese[__])
            s = datetime(s.year, s.month, s.day, delta, _)
        elif "天" in t:
            s = datetime.now() - timedelta(days=delta)
        # elif '年' in t:
        #     s = (datetime.now() - timedelta(days=365 * delta))
        elif "年" in t and "月" in t and "日" in t:
            s = datetime.strptime(t, r"%Y年%m月%d日")
        elif "月" in t and "日" in t:
            today = datetime.today()
            year = str(today.year)
            t = year + '年' + t
            s = datetime.strptime(t, r"%Y年%m月%d日")
        else:
            s = datetime.now()

        if not as_list:
            return s
        else:
            return (s.year, s.month, s.day, s.hour, s.minute, s.second)
