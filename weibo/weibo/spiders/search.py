import os
import sys
from datetime import datetime

import requests
import scrapy
from scrapy import Request

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from urllib.parse import unquote

from scrapy.spiders import Spider
from items import WeiboItem
from items import WeiboDisplayItem
from utils import util
from scrapy.exceptions import CloseSpider
from urllib.parse import urlparse
from misc.db import MySQLUtil
from scrapy.utils.project import get_project_settings


class weibo_searchSpider(Spider):
    name = "search"
    allowed_domains = ["s.weibo.com"]
    base_url = 'https://s.weibo.com'
    env = get_project_settings()['MACHINE_ENV']

    def start_requests(self):
        if self.env == 'online':
            db = MySQLUtil('192.168.1.2', 3366, 'root', 'gw201221', 'pdd')
            self.logger.debug("execute start_requests start query sql")
            results = db.execute("select channel_url from pdd_monitor_source where name='新浪微博'")
            self.logger.debug("execute start_requests finish query sql")
            for row in results:
                url = row[0]
                self.logger.debug(url)
                yield Request(url=url, callback=self.parse)
        else:
            urls = [
                'https://s.weibo.com/realtime?q=pdd&rd=realtime&tw=realtime&Refer=weibo_realtime',
                # 'https://s.weibo.com/realtime?q=pinduoduo&rd=realtime&tw=realtime&Refer=weibo_realtime',
                # 'https://s.weibo.com/realtime?q=temu&rd=realtime&tw=realtime&Refer=weibo_realtime',
                # 'https://s.weibo.com/realtime?q=拼多多&rd=realtime&tw=realtime&Refer=weibo_realtime',
                # 'https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D%23pdd%23',
                # 'https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D%23pinduoduo%23',
                # 'https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D%23temu%23',
                # 'https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D%23拼多多%23',
            ]
            for url in urls:
                yield Request(url=url, callback=self.parse)

    def parse(self, response):
        """解析搜索结果的信息"""
        is_empty = response.xpath('//div[@class="card card-no-result s-pt20b40"]')
        if is_empty:
            print('当前页面搜索结果为空')
        else:
            for weibo in self.parse_weibo(response):
                i = WeiboDisplayItem()
                i['pub_time'] = weibo['created_at'] + ":00"
                i['url'] = weibo['post_url']
                i['author'] = weibo['screen_name']
                i['content'] = weibo['text']

                time_now = datetime.now()
                current_time = time_now.strftime("%Y-%m-%d %H:%M:%S")
                i['craw_time'] = current_time
                i['source_url'] = response.request.url
                yield i

            # 下一页
            next_url = response.xpath('//a[@class="next"]/@href').extract_first()
            if next_url:
                next_url = self.base_url + next_url
                o = urlparse(next_url)
                for i in o.query.split('&'):
                    if 'page' in i:
                        num = int(i.split('=')[1])
                        if num <= 5:  # 最多爬取5页
                            yield scrapy.Request(url=next_url, callback=self.parse)

    def get_ip(self, bid):
        url = f"https://weibo.com/ajax/statuses/show?id={bid}&locale=zh-CN"
        response = requests.get(url, headers=self.settings.get('DEFAULT_REQUEST_HEADERS'))
        if response.status_code != 200:
            return ""
        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            return ""
        ip_str = data.get("region_name", "")
        if ip_str:
            ip_str = ip_str.split()[-1]
        return ip_str

    def get_article_url(self, selector):
        """获取微博头条文章url"""
        article_url = ''
        text = selector.xpath('string(.)').extract_first().replace(
            '\u200b', '').replace('\ue627', '').replace('\n', '').replace(' ', '')
        if text.startswith('发布了头条文章'):
            urls = selector.xpath('.//a')
            for url in urls:
                if url.xpath(
                        'i[@class="wbicon"]/text()').extract_first() == 'O':
                    if url.xpath('@href').extract_first() and url.xpath(
                            '@href').extract_first().startswith('http://t.cn'):
                        article_url = url.xpath('@href').extract_first()
                    break
        return article_url

    def get_location(self, selector):
        """获取微博发布位置"""
        a_list = selector.xpath('.//a')
        location = ''
        for a in a_list:
            if a.xpath('./i[@class="wbicon"]') and a.xpath(
                    './i[@class="wbicon"]/text()').extract_first() == '2':
                location = a.xpath('string(.)').extract_first()[1:]
                break
        return location

    def get_at_users(self, selector):
        """获取微博中@的用户昵称"""
        a_list = selector.xpath('.//a')
        at_users = ''
        at_list = []
        for a in a_list:
            if len(unquote(a.xpath('@href').extract_first())) > 14 and len(
                    a.xpath('string(.)').extract_first()) > 1:
                if unquote(a.xpath('@href').extract_first())[14:] == a.xpath(
                        'string(.)').extract_first()[1:]:
                    at_user = a.xpath('string(.)').extract_first()[1:]
                    if at_user not in at_list:
                        at_list.append(at_user)
        if at_list:
            at_users = ','.join(at_list)
        return at_users

    def get_topics(self, selector):
        """获取参与的微博话题"""
        a_list = selector.xpath('.//a')
        topics = ''
        topic_list = []
        for a in a_list:
            text = a.xpath('string(.)').extract_first()
            if len(text) > 2 and text[0] == '#' and text[-1] == '#':
                if text[1:-1] not in topic_list:
                    topic_list.append(text[1:-1])
        if topic_list:
            topics = ','.join(topic_list)
        return topics

    def parse_weibo(self, response):
        """解析网页中的微博信息"""
        keyword = response.meta.get('keyword')
        for sel in response.xpath("//div[@class='card-wrap']"):
            info = sel.xpath("div[@class='card']/div[@class='card-feed']/div[@class='content']/div[@class='info']")
            if info:
                weibo = WeiboItem()
                weibo['id'] = sel.xpath('@mid').extract_first()
                post_url = sel.xpath('.//div[@class="from"]/a[1]/@href').extract_first()
                weibo['post_url'] = 'http:' + post_url
                bid = post_url.split('/')[-1].split('?')[0]
                weibo['bid'] = bid
                user_main_url = info[0].xpath('div[2]/a/@href').extract_first()
                weibo['user_main_url'] = 'http:' + user_main_url
                weibo['user_id'] = user_main_url.split('?')[0].split('/')[-1]
                weibo['screen_name'] = info[0].xpath('div[2]/a/@nick-name').extract_first()
                txt_sel = sel.xpath('.//p[@class="txt"]')[0]
                retweet_sel = sel.xpath('.//div[@class="card-comment"]')
                retweet_txt_sel = ''
                if retweet_sel and retweet_sel[0].xpath('.//p[@class="txt"]'):
                    retweet_txt_sel = retweet_sel[0].xpath(
                        './/p[@class="txt"]')[0]
                content_full = sel.xpath(
                    './/p[@node-type="feed_list_content_full"]')
                is_long_weibo = False
                is_long_retweet = False
                if content_full:
                    if not retweet_sel:
                        txt_sel = content_full[0]
                        is_long_weibo = True
                    elif len(content_full) == 2:
                        txt_sel = content_full[0]
                        retweet_txt_sel = content_full[1]
                        is_long_weibo = True
                        is_long_retweet = True
                    elif retweet_sel[0].xpath(
                            './/p[@node-type="feed_list_content_full"]'):
                        retweet_txt_sel = retweet_sel[0].xpath(
                            './/p[@node-type="feed_list_content_full"]')[0]
                        is_long_retweet = True
                    else:
                        txt_sel = content_full[0]
                        is_long_weibo = True
                weibo['text'] = txt_sel.xpath(
                    'string(.)').extract_first().replace('\u200b', '').replace(
                    '\ue627', '')
                weibo['article_url'] = self.get_article_url(txt_sel)
                weibo['location'] = self.get_location(txt_sel)
                if weibo['location']:
                    weibo['text'] = weibo['text'].replace(
                        '2' + weibo['location'], '')
                weibo['text'] = weibo['text'][2:].replace(' ', '')
                if is_long_weibo:
                    weibo['text'] = weibo['text'][:-4]
                weibo['at_users'] = self.get_at_users(txt_sel)
                weibo['topics'] = self.get_topics(txt_sel)
                reposts_count = sel.xpath(
                    './/a[@action-type="feed_list_forward"]/text()').extract()
                reposts_count = "".join(reposts_count)
                try:
                    reposts_count = re.findall(r'\d+.*', reposts_count)
                except TypeError:
                    print(
                        "无法解析转发按钮，可能是 1) 网页布局有改动 2) cookie无效或已过期。\n"
                        "请在 https://github.com/dataabc/weibo-search 查看文档，以解决问题，"
                    )
                    raise CloseSpider()
                weibo['reposts_count'] = reposts_count[
                    0] if reposts_count else '0'
                comments_count = sel.xpath(
                    './/a[@action-type="feed_list_comment"]/text()'
                ).extract_first()
                comments_count = re.findall(r'\d+.*', comments_count)
                weibo['comments_count'] = comments_count[
                    0] if comments_count else '0'
                attitudes_count = sel.xpath(
                    './/a[@action-type="feed_list_like"]/button/span[2]/text()').extract_first()
                attitudes_count = re.findall(r'\d+.*', attitudes_count)
                weibo['attitudes_count'] = attitudes_count[0] if attitudes_count else '0'
                created_at = \
                sel.xpath('.//div[@class="from"]/a[1]/text()').extract_first().replace(' ', '').replace('\n',
                                                                                                        '').split(
                    '前')[0]
                weibo['created_at'] = util.standardize_date(created_at)
                source = sel.xpath('.//div[@class="from"]/a[2]/text()'
                                   ).extract_first()
                weibo['source'] = source if source else ''
                pics = ''
                is_exist_pic = sel.xpath('.//div[@class="media media-piclist"]')
                if is_exist_pic:
                    pics = is_exist_pic[0].xpath('ul[1]/li/img/@src').extract()
                    pics = [pic[8:] for pic in pics]
                    pics = [
                        re.sub(r'/.*?/', '/large/', pic, 1) for pic in pics
                    ]
                    pics = ['https://' + pic for pic in pics]
                video_url = ''
                is_exist_video = sel.xpath(
                    './/div[@class="thumbnail"]//video-player').extract_first()
                if is_exist_video:
                    video_url = re.findall(r'src:\'(.*?)\'', is_exist_video)[0]
                    video_url = video_url.replace('&amp;', '&')
                    video_url = 'http:' + video_url
                if not retweet_sel:
                    weibo['pics'] = pics
                    weibo['video_url'] = video_url
                else:
                    weibo['pics'] = ''
                    weibo['video_url'] = ''
                weibo['retweet_id'] = ''
                if retweet_sel and retweet_sel[0].xpath(
                        './/div[@node-type="feed_list_forwardContent"]/a[1]'):
                    retweet = WeiboItem()
                    retweet['id'] = retweet_sel[0].xpath(
                        './/a[@action-type="feed_list_like"]/@action-data'
                    ).extract_first()[4:]
                    retweet['bid'] = retweet_sel[0].xpath(
                        './/p[@class="from"]/a/@href').extract_first().split(
                        '/')[-1].split('?')[0]
                    info = retweet_sel[0].xpath(
                        './/div[@node-type="feed_list_forwardContent"]/a[1]'
                    )[0]
                    retweet['user_id'] = info.xpath(
                        '@href').extract_first().split('/')[-1]
                    retweet['screen_name'] = info.xpath(
                        '@nick-name').extract_first()
                    retweet['text'] = retweet_txt_sel.xpath(
                        'string(.)').extract_first().replace('\u200b',
                                                             '').replace(
                        '\ue627', '')
                    retweet['article_url'] = self.get_article_url(
                        retweet_txt_sel)
                    retweet['location'] = self.get_location(retweet_txt_sel)
                    if retweet['location']:
                        retweet['text'] = retweet['text'].replace(
                            '2' + retweet['location'], '')
                    retweet['text'] = retweet['text'][2:].replace(' ', '')
                    if is_long_retweet:
                        retweet['text'] = retweet['text'][:-4]
                    retweet['at_users'] = self.get_at_users(retweet_txt_sel)
                    retweet['topics'] = self.get_topics(retweet_txt_sel)
                    reposts_count = retweet_sel[0].xpath(
                        './/ul[@class="act s-fr"]/li[1]/a[1]/text()'
                    ).extract_first()
                    reposts_count = re.findall(r'\d+.*', reposts_count)
                    retweet['reposts_count'] = reposts_count[
                        0] if reposts_count else '0'
                    comments_count = retweet_sel[0].xpath(
                        './/ul[@class="act s-fr"]/li[2]/a[1]/text()'
                    ).extract_first()
                    comments_count = re.findall(r'\d+.*', comments_count)
                    retweet['comments_count'] = comments_count[
                        0] if comments_count else '0'
                    attitudes_count = retweet_sel[0].xpath(
                        './/a[@class="woo-box-flex woo-box-alignCenter woo-box-justifyCenter"]//span[@class="woo-like-count"]/text()').extract_first()
                    attitudes_count = re.findall(r'\d+.*', attitudes_count)
                    retweet['attitudes_count'] = attitudes_count[
                        0] if attitudes_count else '0'
                    created_at = retweet_sel[0].xpath(
                        './/p[@class="from"]/a[1]/text()').extract_first(
                    ).replace(' ', '').replace('\n', '').split('前')[0]
                    retweet['created_at'] = util.standardize_date(created_at)
                    source = retweet_sel[0].xpath(
                        './/p[@class="from"]/a[2]/text()').extract_first()
                    retweet['source'] = source if source else ''
                    retweet['pics'] = pics
                    retweet['video_url'] = video_url
                    retweet['retweet_id'] = ''
                    yield {'weibo': retweet, 'keyword': keyword}
                    weibo['retweet_id'] = retweet['id']
                weibo["ip"] = self.get_ip(bid)
                yield weibo
