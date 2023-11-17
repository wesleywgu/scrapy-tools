# Scrapy settings for baidu project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

import sys
import os
from os.path import dirname

path = dirname(dirname(os.path.abspath(os.path.dirname(__file__))))
sys.path.append(path)
from misc.log import *

BOT_NAME = 'baidu'

SPIDER_MODULES = ['baidu.spiders']
NEWSPIDER_MODULE = 'baidu.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'baidu (+http://www.yourdomain.com)'

DOWNLOADER_MIDDLEWARES = {
    # 'misc.middleware.CustomHttpProxyMiddleware': 400,
    'misc.middleware.BaiduUserAgentMiddleware': 401,

}

ITEM_PIPELINES = {
    # 'baidu.pipelines.JsonWithEncodingPipeline': 300,
    # 'baidu.pipelines.RedisPipeline': 301,
    'crawlab.CrawlabPipeline': 300,
}

LOG_LEVEL = 'DEBUG'

DOWNLOAD_DELAY = 1
