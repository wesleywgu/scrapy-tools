import re
import traceback

import scrapy
from ggoogle.items import googleItem
from scrapy import Request

try:
    from scrapy.spiders import Spider
except:
    from scrapy.spiders import BaseSpider as Spider

import datetime
from dateutil.relativedelta import relativedelta
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from misc.db import MySQLUtil
from scrapy.utils.project import get_project_settings


class googleSearchSpider(Spider):
    name = "search"
    allowed_domains = ["google.com"]
    env = get_project_settings()['MACHINE_ENV']

    def start_requests(self):
        if self.env == 'online':
            db = MySQLUtil('192.168.1.2', 3366, 'root', 'gw201221', 'pdd')
            self.logger.debug("execute start_requests start query sql")
            results = db.execute(
                "select channel_url from pdd_monitor_source where name='Google' and channel_url like '%search%' and url_grade between 1 and 3")
            self.logger.debug("execute start_requests finish query sql")
            for row in results:
                url = row[0]
                self.logger.debug(url)
                yield Request(url=url, callback=self.parse)
        else:
            urls = [
                'https://www.google.com/search?q=%E6%8B%BC%E5%A4%9A%E5%A4%9A+%E5%8D%A1%E5%B7%B4%E6%96%AF%E5%9F%BA&sca_esv=585373397&biw=1680&bih=826&sxsrf=AM9HkKnvRzgTiM-9GIWw61P_daZPCasX8w%3A1700986382857&ei=Dv5iZc_5M5aehwOWj4CQAw&ved=0ahUKEwjPuPiInOGCAxUWz2EKHZYHADIQ4dUDCBA&uact=5&oq=%E6%8B%BC%E5%A4%9A%E5%A4%9A+%E5%8D%A1%E5%B7%B4%E6%96%AF%E5%9F%BA&gs_lp=Egxnd3Mtd2l6LXNlcnAiFuaLvOWkmuWkmiDljaHlt7Tmlq_ln7oyChAAGEcY1gQYsAMyChAAGEcY1gQYsAMyChAAGEcY1gQYsAMyChAAGEcY1gQYsAMyChAAGEcY1gQYsAMyChAAGEcY1gQYsAMyChAAGEcY1gQYsAMyChAAGEcY1gQYsAMyChAAGEcY1gQYsAMyChAAGEcY1gQYsANImQVQAFgAcAF4AZABAJgBAKABAKoBALgBA8gBAOIDBBgAIEGIBgGQBgo&sclient=gws-wiz-serp&hl=zh-CN&start=0'
            ]
            for url in urls:
                yield Request(url=url, callback=self.parse)

    def parse(self, response):
        news_list = self.build_response(response)
        for news in news_list:
            google_news = googleItem()
            google_news['content'] = news['title'] + ' ## ' + news['desc']
            google_news['author'] = news['author']
            if news['datetime'] == '':
                google_news['pub_time'] = '无'
            else:
                google_news['pub_time'] = news['datetime'].strftime("%Y-%m-%d %H:%M:%S")

            google_news['url'] = news['link']

            time_now = datetime.datetime.now()
            current_time = time_now.strftime("%Y-%m-%d %H:%M:%S")
            google_news['craw_time'] = current_time
            google_news['source_url'] = response.request.url
            yield google_news

        next_btn = response.xpath('//a[@id="pnnext"]')
        if next_btn:
            current_url = response.request.url
            query_dict = parse_qs(urlparse(current_url).query)
            if 'start' in query_dict:
                start_num = int(query_dict['start'][0])
            else:
                start_num = 0
            current_page = int(start_num / 10) + 1
            next_url = self.replace_field(current_url, 'start', current_page * 10)
            if current_page <= 4:
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

    def en_date_parser(self, date):
        months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9,
                  'Sept': 9,
                  'Oct': 10, 'Nov': 11, 'Dec': 12, '01': 1, '02': 2, '03': 3, '04': 4, '05': 5, '06': 6, '07': 7,
                  '08': 8,
                  '09': 9, '10': 10, '11': 11, '12': 12}
        try:
            if ' ago' in date.lower():
                q = int(date.split()[-3])
                if 'minutes' in date.lower() or 'mins' in date.lower():
                    return datetime.datetime.now() + relativedelta(minutes=-q)
                elif 'hour' in date.lower():
                    return datetime.datetime.now() + relativedelta(hours=-q)
                elif 'day' in date.lower():
                    return datetime.datetime.now() + relativedelta(days=-q)
                elif 'week' in date.lower():
                    return datetime.datetime.now() + relativedelta(days=-7 * q)
                elif 'month' in date.lower():
                    return datetime.datetime.now() + relativedelta(months=-q)
            elif 'yesterday' in date.lower():
                return datetime.datetime.now() + relativedelta(days=-1)
            else:
                date_list = date.replace('/', ' ').split(' ')
                if len(date_list) == 2:
                    date_list.append(datetime.datetime.now().year)
                elif len(date_list) == 3:
                    if date_list[0] == '':
                        date_list[0] = '1'
                return datetime.datetime(day=int(date_list[0]), month=months[date_list[1]], year=int(date_list[2]))
        except:
            return float('nan')

    def chinese_date_parser(self, date_str):
        try:
            if '前' in date_str.lower():
                if '分' in date_str.lower() or '分钟' in date_str.lower():
                    q = int(date_str.split('分')[0])
                    return datetime.datetime.now() + relativedelta(minutes=-q)
                elif '小时' in date_str.lower():
                    q = int(date_str.split('小时')[0])
                    return datetime.datetime.now() + relativedelta(hours=-q)
                elif '天' in date_str.lower():
                    q = int(date_str.split('天')[0])
                    return datetime.datetime.now() + relativedelta(days=-q)
                elif '周' in date_str.lower():
                    q = int(date_str.split('周')[0])
                    return datetime.datetime.now() + relativedelta(days=-7 * q)
                elif '月' in date_str.lower():
                    q = int(date_str.split('月')[0])
                    return datetime.datetime.now() + relativedelta(months=-q)
            elif '昨天' in date_str.lower():
                return datetime.datetime.now() + relativedelta(days=-1)
            else:
                converted_date = datetime.datetime.strptime(date_str, '%Y年%m月%d日')
                return converted_date
        except:
            return float('nan')

    def remove_html_tags(self, html):
        """
        去除HTML标签
        """
        pattern = re.compile(r'<[^>]+>')
        return pattern.sub('', html)

    def build_response(self, response):
        result = response.xpath('//div[@id="rso"]/div/div')

        results = []
        for item in result:
            try:
                tmp_title = item.xpath('.//div/div[1]/div/div/span/a/h3/text()').get().replace("\n", "")
            except Exception:
                tmp_title = ''

            try:
                tmp_desc = item.xpath('.//div/div[2]/div/span[2]').get().replace("\n", "")
                tmp_desc = self.remove_html_tags(tmp_desc)
            except Exception:
                tmp_desc = ''

            try:
                tmp_link = item.xpath('.//div/div[1]/div/div/span/a/@href').get()
            except Exception:
                tmp_link = ''

            try:
                tmp_author = item.xpath('.//div/div[1]/div/div/span/a/div/div/span/text()').get().replace("\n", "")
            except Exception:
                tmp_author = ''
            try:
                tmp_date_str = item.xpath('.//div/div[2]/div/span[1]/span/text()').get().replace("\n", "")

                url = response.request.url
                parse = urlparse(url)
                query = parse.query
                query_pair = parse_qs(query)
                language = query_pair['hl'][0]

                if language == 'en':
                    pub_datetime = self.en_date_parser(tmp_date_str)
                else:
                    pub_datetime = self.chinese_date_parser(tmp_date_str)
            except Exception:
                traceback.print_stack()
                pub_datetime = ''

            results.append(
                {
                    'title': tmp_title,
                    'desc': tmp_desc,
                    'author': tmp_author,
                    'datetime': pub_datetime,
                    'link': tmp_link,
                }
            )
        # 返回所有结果
        return results
