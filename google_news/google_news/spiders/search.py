import scrapy

from google_news.items import googleItem
from scrapy import Request

try:
    from scrapy.spiders import Spider
except:
    from scrapy.spiders import BaseSpider as Spider

import dateparser, copy
import datetime
from dateutil.relativedelta import relativedelta
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from misc.db import MySQLUtil
from scrapy.utils.project import get_project_settings


class googleSpider(Spider):
    name = "search"
    allowed_domains = ["google.com"]
    env = get_project_settings()['MACHINE_ENV']

    def start_requests(self):
        if self.env == 'online':
            db = MySQLUtil('192.168.1.2', 3366, 'root', 'gw201221', 'pdd')
            self.logger.debug("execute start_requests start query sql")
            results = db.execute(
                "select channel_url from pdd_monitor_source where name='Google' and url_grade between 1 and 3")
            self.logger.debug("execute start_requests finish query sql")
            for row in results:
                url = row[0]
                self.logger.debug(url)
                yield Request(url=url, callback=self.parse)
        else:
            urls = [
                'https://www.google.com/search?q=pdd&sca_esv=581520105&tbas=0&tbs=qdr:w,sbd:1&tbm=nws&sxsrf=AM9HkKkXb3sBmvO6GPX6Bk-OFf-AauWLOA:1699710999318&ei=F4hPZeqGE5vf2roPk-C5sA4&start=0&sa=N&ved=2ahUKEwiq7tbyjLyCAxWbr1YBHRNwDuY4ChDx0wN6BAgCEAI&biw=1680&bih=825&dpr=2&hl=en'
            ]
            for url in urls:
                yield Request(url=url, callback=self.parse)

    def parse(self, response):
        news_list = self.build_response(response)
        for news in news_list:
            google_news = googleItem()
            google_news['content'] = news['title'] + ' ## ' + news['desc']
            google_news['author'] = news['author']
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
            start_num = int(query_dict['start'][0])
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

    def build_response(self, response):
        result = response.xpath('//div[@data-hveid]/div/div[@data-ved]')

        results = []
        for item in result:
            try:
                tmp_text = item.xpath('.//a/div/div[2]/div[2]/text()').get().replace("\n", "")
            except Exception:
                tmp_text = item.xpath('.//a/div/div/div[2]/text()').get().replace("\n", "")

            try:
                tmp_desc = item.xpath('.//a/div/div[2]/div[3]/text()').get().replace("\n", "")
            except Exception:
                tmp_desc = item.xpath('.//a/div/div/div[3]/text()').get().replace("\n", "")

            try:
                tmp_link = item.xpath('.//a/@href').get()
            except Exception:
                tmp_link = ''
            try:
                tmp_author = item.xpath('.//a/div/div[2]/div[1]/span/text()').get().replace("\n", "")
            except Exception:
                tmp_author = item.xpath('.//a/div/div/div[1]/span/text()').get().replace("\n", "")
            try:
                tmp_date_str = item.xpath('.//div[@style="bottom:0px"]/span/text()').get().replace("\n", "")
                tmp_date, tmp_datetime = self.lexical_date_parser(tmp_date_str)
            except Exception:
                tmp_date = ''
                tmp_datetime = None

            results.append(
                {
                    'title': tmp_text,
                    'desc': tmp_desc,
                    'author': tmp_author,
                    'date': tmp_date,
                    'datetime': self.define_date(tmp_date),
                    'link': tmp_link,
                }
            )
        return results

    def define_date(self, date):
        months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Sept': 9,
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

    def lexical_date_parser(self, date_to_check):
        if date_to_check == '':
            return ('', None)
        datetime_tmp = None
        date_tmp = copy.copy(date_to_check)
        try:
            datetime_tmp = dateparser.parse(date_tmp)
        except:
            date_tmp = None
            datetime_tmp = None

        if datetime_tmp == None:
            date_tmp = date_to_check
        else:
            datetime_tmp = datetime_tmp.replace(tzinfo=None)

        if date_tmp[0] == ' ':
            date_tmp = date_tmp[1:]
        return date_tmp, datetime_tmp
