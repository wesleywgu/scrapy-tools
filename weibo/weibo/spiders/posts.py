import json
import math
import os
import sys
from collections import OrderedDict
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import requests
from scrapy import Request
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta

import scrapy
from lxml import etree

from items import WeiboItem
from items import WeiboDisplayItem
from misc.db import MySQLUtil


class UserPostsSpider(scrapy.Spider):
    name = "posts"
    allowed_domains = ["weibo.cn"]
    # start_urls = [
    #     "https://m.weibo.cn/api/container/getIndex?container_ext=profile_uid:3285381094&page_type=searchall&containerid=2304133285381094&page=1"
    # ]

    url_template = "https://m.weibo.cn/api/container/getIndex?container_ext=profile_uid:{uid}&page_type=searchall&containerid=230413{uid}&page=1"

    # 日期时间格式
    DTFORMAT = "%Y-%m-%dT%H:%M:%S"

    db = MySQLUtil('192.168.1.2', 3366, 'root', 'gw201221', 'pdd')

    def start_requests(self):
        self.logger.debug("execute start_requests start query sql")
        results = self.db.execute(
            "select channel_url from pdd_monitor_source where url_grade <> '9' and channel_url like '%https://weibo.com/u%'")
        self.logger.debug("execute start_requests finish query sql")
        for row in results:
            url = row[0]
            uid = url.split('/')[-1]
            new_url = self.url_template.format(uid=uid)
            self.logger.debug("old={url}, new_url={new_url}".format(url=url, new_url=new_url))
            yield Request(url=new_url, callback=self.parse)

    def parse(self, response):
        weibos = self.get_one_page(response)
        for weibo in weibos:
            i = WeiboDisplayItem()
            i['pub_time'] = weibo['created_at']
            i['post_url'] = weibo['post_url']
            i['screen_name'] = weibo['screen_name']
            i['text'] = weibo['text']

            time_now = datetime.now()
            current_time = time_now.strftime("%Y-%m-%d %H:%M:%S")
            i['craw_time'] = current_time
            i['source_url'] = response.request.url
            yield i

        # 下一页
        current_url = response.request.url
        query_dict = parse_qs(urlparse(current_url).query)
        user_id = query_dict['container_ext'][0].replace('profile_uid:', '')
        user_info = self.get_user_info(user_id)
        weibo_count = user_info["statuses_count"]
        max_page_count = int(math.ceil(weibo_count / 10.0))
        max_page_count = min(5, max_page_count)
        current_page = int(query_dict['page'][0])
        if current_page < max_page_count:
            next_url = self.replace_field(current_url, 'page', current_page + 1)
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

    def is_datetime(self, since_date):
        """判断日期格式是否为 %Y-%m-%dT%H:%M:%S"""
        try:
            datetime.strptime(since_date, self.DTFORMAT)
            return True
        except ValueError:
            return False

    def is_date(self, since_date):
        """判断日期格式是否为 %Y-%m-%d"""
        try:
            datetime.strptime(since_date, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def get_pics(self, weibo_info):
        """获取微博原始图片url"""
        if weibo_info.get("pics"):
            pic_info = weibo_info["pics"]
            pic_list = [pic["large"]["url"] for pic in pic_info]
            pics = ",".join(pic_list)
        else:
            pics = ""
        return pics

    def get_live_photo(self, weibo_info):
        """获取live photo中的视频url"""
        live_photo_list = []
        live_photo = weibo_info.get("pic_video")
        if live_photo:
            prefix = "https://video.weibo.com/media/play?livephoto=//us.sinaimg.cn/"
            for i in live_photo.split(","):
                if len(i.split(":")) == 2:
                    url = prefix + i.split(":")[1] + ".mov"
                    live_photo_list.append(url)
            return live_photo_list

    def get_video_url(self, weibo_info):
        """获取微博视频url"""
        video_url = ""
        video_url_list = []
        if weibo_info.get("page_info"):
            if (
                    weibo_info["page_info"].get("urls")
                    or weibo_info["page_info"].get("media_info")
            ) and weibo_info["page_info"].get("type") == "video":
                media_info = weibo_info["page_info"]["urls"]
                if not media_info:
                    media_info = weibo_info["page_info"]["media_info"]
                video_url = media_info.get("mp4_720p_mp4")
                if not video_url:
                    video_url = media_info.get("mp4_hd_url")
                if not video_url:
                    video_url = media_info.get("hevc_mp4_hd")
                if not video_url:
                    video_url = media_info.get("mp4_sd_url")
                if not video_url:
                    video_url = media_info.get("mp4_ld_mp4")
                if not video_url:
                    video_url = media_info.get("stream_url_hd")
                if not video_url:
                    video_url = media_info.get("stream_url")
        if video_url:
            video_url_list.append(video_url)
        live_photo_list = self.get_live_photo(weibo_info)
        if live_photo_list:
            video_url_list += live_photo_list
        return ";".join(video_url_list)

    def get_location(self, selector):
        """获取微博发布位置"""
        location_icon = "timeline_card_small_location_default.png"
        span_list = selector.xpath("//span")
        location = ""
        for i, span in enumerate(span_list):
            if span.xpath("img/@src"):
                if location_icon in span.xpath("img/@src")[0]:
                    location = span_list[i + 1].xpath("string(.)")
                    break
        return location

    def get_article_url(self, selector):
        """获取微博中头条文章的url"""
        article_url = ""
        text = selector.xpath("string(.)")
        if text.startswith("发布了头条文章"):
            url = selector.xpath("//a/@data-url")
            if url and url[0].startswith("http://t.cn"):
                article_url = url[0]
        return article_url

    def get_topics(self, selector):
        """获取参与的微博话题"""
        span_list = selector.xpath("//span[@class='surl-text']")
        topics = ""
        topic_list = []
        for span in span_list:
            text = span.xpath("string(.)")
            if len(text) > 2 and text[0] == "#" and text[-1] == "#":
                topic_list.append(text[1:-1])
        if topic_list:
            topics = ",".join(topic_list)
        return topics

    def get_at_users(self, selector):
        """获取@用户"""
        a_list = selector.xpath("//a")
        at_users = ""
        at_list = []
        for a in a_list:
            if "@" + a.xpath("@href")[0][3:] == a.xpath("string(.)"):
                at_list.append(a.xpath("string(.)")[1:])
        if at_list:
            at_users = ",".join(at_list)
        return at_users

    def string_to_int(self, string):
        """字符串转换为整数"""
        if isinstance(string, int):
            return string
        elif string.endswith("万+"):
            string = string[:-2] + "0000"
        elif string.endswith("万"):
            string = float(string[:-1]) * 10000
        elif string.endswith("亿"):
            string = float(string[:-1]) * 100000000
        return int(string)

    def standardize_date(self, created_at):
        """标准化微博发布时间"""
        if "刚刚" in created_at:
            ts = datetime.now()
        elif "分钟" in created_at:
            minute = created_at[: created_at.find("分钟")]
            minute = timedelta(minutes=int(minute))
            ts = datetime.now() - minute
        elif "小时" in created_at:
            hour = created_at[: created_at.find("小时")]
            hour = timedelta(hours=int(hour))
            ts = datetime.now() - hour
        elif "昨天" in created_at:
            day = timedelta(days=1)
            ts = datetime.now() - day
        else:
            created_at = created_at.replace("+0800 ", "")
            ts = datetime.strptime(created_at, "%c")

        created_at = ts.strftime(self.DTFORMAT)
        full_created_at = ts.strftime("%Y-%m-%d %H:%M:%S")
        return created_at, full_created_at

    # def standardize_info(self, weibo):
    #     """标准化信息，去除乱码"""
    #     for k, v in weibo.items():
    #         if (
    #                 "bool" not in str(type(v))
    #                 and "int" not in str(type(v))
    #                 and "list" not in str(type(v))
    #                 and "long" not in str(type(v))
    #         ):
    #             weibo[k] = (
    #                 v.replace("\u200b", "")
    #                 .encode(sys.stdout.encoding, "ignore")
    #                 .decode(sys.stdout.encoding)
    #             )
    #     return weibo

    def get_json(self, params):
        """获取网页中json数据"""
        url = "https://m.weibo.cn/api/container/getIndex?"

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
            'User_Agent': user_agent,
            'Cookie': 'WBtopGlobal_register_version=2023111214;SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5_O.oej.39ZcWLp6oDWTkx5JpX5KzhUgL.FoM7eo.4ehzNeoe2dJLoI7_N9PSj9PLkUfvrUBtt;SCF=AmcpWYdzMxEhUWLHtPDTlbQwfWmdXoXXSAVDE3zNSqAnongJh_1R04emj0dDgaebWYf4Bv11mto8nfW35Xvr3kc.;_s_tentry=www.amz123.com;UOR=,,www.amz123.com;SUB=_2A25IVApEDeRhGeFO6VsY8CzLyT-IHXVrKAOMrDV8PUNbmtANLWz-kW9NQWztmZkmYhNmjW5A0cgGP8Z8CjOvoPkG;Apache=2559002441077.0586.1699597577296;ALF=1731308948;PC_TOKEN=bc73529cb3;SINAGLOBAL=8684552721605.112.1696770171512;SSOLoginState=1699597596;ULV=1699597577339:7:3:2:2559002441077.0586.1699597577296:1699518952747'
        }
        r = requests.get(url, params=params, headers=headers, verify=False)
        return r.json(), r.status_code

    def get_user_info(self, user_id):
        """获取用户信息"""
        params = {"containerid": "100505" + str(user_id)}
        js, status_code = self.get_json(params)

        if js["ok"]:
            info = js["data"]["userInfo"]
            user_info = OrderedDict()
            user_info["id"] = user_id
            user_info["screen_name"] = info.get("screen_name", "")
            user_info["gender"] = info.get("gender", "")
            params = {
                "containerid": "230283" + user_id + "_-_INFO"
            }
            zh_list = ["生日", "所在地", "小学", "初中", "高中", "大学", "公司", "注册时间", "阳光信用"]
            en_list = [
                "birthday",
                "location",
                "education",
                "education",
                "education",
                "education",
                "company",
                "registration_time",
                "sunshine",
            ]
            for i in en_list:
                user_info[i] = ""
            js, _ = self.get_json(params)
            if js["ok"]:
                cards = js["data"]["cards"]
                if isinstance(cards, list) and len(cards) > 1:
                    card_list = cards[0]["card_group"] + cards[1]["card_group"]
                    for card in card_list:
                        if card.get("item_name") in zh_list:
                            user_info[
                                en_list[zh_list.index(card.get("item_name"))]
                            ] = card.get("item_content", "")
            user_info["statuses_count"] = self.string_to_int(
                info.get("statuses_count", 0)
            )
            user_info["followers_count"] = self.string_to_int(
                info.get("followers_count", 0)
            )
            user_info["follow_count"] = self.string_to_int(info.get("follow_count", 0))
            user_info["description"] = info.get("description", "")
            user_info["profile_url"] = info.get("profile_url", "")
            user_info["profile_image_url"] = info.get("profile_image_url", "")
            user_info["avatar_hd"] = info.get("avatar_hd", "")
            user_info["urank"] = info.get("urank", 0)
            user_info["mbrank"] = info.get("mbrank", 0)
            user_info["verified"] = info.get("verified", False)
            user_info["verified_type"] = info.get("verified_type", -1)
            user_info["verified_reason"] = info.get("verified_reason", "")
            return user_info
        else:
            return None

    def parse_weibo(self, weibo_info):
        weibo = WeiboItem()
        if weibo_info["user"]:
            weibo["user_id"] = weibo_info["user"]["id"]
            weibo["screen_name"] = weibo_info["user"]["screen_name"]
        else:
            weibo["user_id"] = ""
            weibo["screen_name"] = ""
        weibo["id"] = int(weibo_info["id"])
        weibo["bid"] = weibo_info["bid"]
        text_body = weibo_info["text"]
        selector = etree.HTML(f"{text_body}<hr>" if text_body.isspace() else text_body)

        text_list = selector.xpath("//text()")
        # 若text_list中的某个字符串元素以 @ 或 # 开始，则将该元素与前后元素合并为新元素，否则会带来没有必要的换行
        text_list_modified = []
        for ele in range(len(text_list)):
            if ele > 0 and (text_list[ele - 1].startswith(('@', '#')) or text_list[ele].startswith(('@', '#'))):
                text_list_modified[-1] += text_list[ele]
            else:
                text_list_modified.append(text_list[ele])
        weibo["text"] = "\n".join(text_list_modified)

        weibo["article_url"] = self.get_article_url(selector)
        weibo["pics"] = self.get_pics(weibo_info)
        weibo["video_url"] = self.get_video_url(weibo_info)
        weibo["location"] = self.get_location(selector)
        weibo["created_at"] = weibo_info["created_at"]
        weibo["source"] = weibo_info["source"]
        weibo["attitudes_count"] = self.string_to_int(
            weibo_info.get("attitudes_count", 0)
        )
        weibo["comments_count"] = self.string_to_int(
            weibo_info.get("comments_count", 0)
        )
        weibo["reposts_count"] = self.string_to_int(weibo_info.get("reposts_count", 0))
        weibo["topics"] = self.get_topics(selector)
        weibo["at_users"] = self.get_at_users(selector)
        # return self.standardize_info(weibo)
        return weibo

    def get_one_weibo(self, info):
        """获取一条微博的全部信息"""
        weibo_info = info["mblog"]
        weibo_id = weibo_info["id"]
        retweeted_status = weibo_info.get("retweeted_status")
        if retweeted_status and retweeted_status.get("id"):  # 转发
            weibo = self.parse_weibo(weibo_info)
            retweet = self.parse_weibo(retweeted_status)
            retweet["created_at"] = self.standardize_date(retweeted_status["created_at"])[1]
            weibo["retweet"] = retweet
        else:  # 原创
            weibo = self.parse_weibo(weibo_info)
        weibo["created_at"] = self.standardize_date(weibo_info["created_at"])[1]
        weibo['post_url'] = 'https://weibo.com/{user_id}/{bid}'.format(user_id=weibo['user_id'], bid=weibo['bid'])
        weibo['user_main_url'] = 'https://weibo.com/u/{user_id}'.format(user_id=weibo['user_id'])
        return weibo

    def get_one_page(self, response):
        """获取一页的全部微博"""
        js = json.loads(response.text)

        if js["ok"]:
            weibos = js["data"]["cards"]
            for w in weibos:
                if w["card_type"] == 11:
                    temp = w.get("card_group", [0])
                    if len(temp) >= 1:
                        w = temp[0] or w
                    else:
                        w = w
                    wb = self.get_one_weibo(w)
                if w["card_type"] == 9:
                    wb = self.get_one_weibo(w)
                yield wb
