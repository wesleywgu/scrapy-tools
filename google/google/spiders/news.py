import scrapy

from google.items import googleItem

try:
    from scrapy.spiders import Spider
except:
    from scrapy.spiders import BaseSpider as Spider

import dateparser, copy
from bs4 import BeautifulSoup as Soup
import datetime
from dateutil.relativedelta import relativedelta
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode


class googleSpider(Spider):
    name = "search_news"
    allowed_domains = ["google.com"]
    start_urls = [
        "https://www.google.com/search?q=%E6%8B%BC%E5%A4%9A%E5%A4%9A&sca_esv=581520105&tbas=0&tbs=qdr:w,sbd:1&tbm=nws&sxsrf=AM9HkKkXb3sBmvO6GPX6Bk-OFf-AauWLOA:1699710999318&ei=F4hPZeqGE5vf2roPk-C5sA4&start=0&sa=N&ved=2ahUKEwiq7tbyjLyCAxWbr1YBHRNwDuY4ChDx0wN6BAgCEAI&biw=1680&bih=825&dpr=2&hl=en",
    ]

    def parse(self, response):
        news_list = self.build_response(response.text)
        for news in news_list:
            google_news = googleItem()
            google_news['title'] = news['title']
            google_news['desc'] = news['desc']
            google_news['author'] = news['author']
            google_news['pub_time'] = news['datetime'].strftime("%Y-%m-%d %H:%M:%S")
            google_news['url'] = news['link']
            yield google_news

        next_btn = response.xpath('//a[@aria-label="Next page"]')
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
        content = Soup(response, "html.parser")
        result = content.find_all("a", attrs={'data-ved': True})

        results = []
        for item in result:
            try:
                tmp_text = item.find("h3").text.replace("\n", "")
            except Exception:
                tmp_text = ''
            try:
                tmp_link = item.get("href").replace('/url?esrc=s&q=&rct=j&sa=U&url=', '') \
                    .replace('http://www.google.com', '')
            except Exception:
                tmp_link = ''
            try:
                tmp_media = item.find('div').find('div').find('div').find_next_sibling('div').text
            except Exception:
                tmp_media = ''
            try:
                tmp_date = item.find('div').find_next_sibling('div').find('span').text
                tmp_date, tmp_datetime = self.lexical_date_parser(tmp_date)
            except Exception:
                tmp_date = ''
                tmp_datetime = None
            try:
                sibling = item.find('div').find_next_sibling('div')
                tmp_desc = sibling.text.replace('\n', '')
            except Exception:
                tmp_desc = ''
            try:
                tmp_img = item.find("img").get("src")
            except Exception:
                tmp_img = ''
            results.append(
                {
                    'title': tmp_text,
                    'desc': tmp_desc,
                    'author': tmp_media,
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
            date_tmp = date_tmp[date_tmp.rfind('..') + 2:]
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
