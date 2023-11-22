# Scrapy settings for weibo project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

import os
import sys
from os.path import dirname

path = dirname(dirname(os.path.abspath(os.path.dirname(__file__))))
sys.path.append(path)
path = dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(path)

BOT_NAME = 'weibo'

SPIDER_MODULES = ['weibo.spiders']
NEWSPIDER_MODULE = 'weibo.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'weibo (+http://www.yourdomain.com)'

MACHINE_ENV = os.environ.get('env','dev')
print("machine env={}".format(MACHINE_ENV))

if MACHINE_ENV == 'online':
    DOWNLOADER_MIDDLEWARES = {
        # 'misc.middleware.CustomHttpProxyMiddleware': 400,
        'misc.middleware.WeiboUserAgentMiddleware': 401,
    }

    ITEM_PIPELINES = {
        # 'weibo.pipelines.JsonWithEncodingPipeline': 300,
        # 'weibo.pipelines.RedisPipeline': 301,
        'crawlab.CrawlabPipeline': 300,
    }
else:
    DOWNLOADER_MIDDLEWARES = {
        # 'misc.middleware.CustomHttpProxyMiddleware': 400,
        'misc.middleware.WeiboUserAgentMiddleware': 401,
    }

    ITEM_PIPELINES = {
        'weibo.pipelines.JsonWithEncodingPipeline': 300,
        # 'weibo.pipelines.RedisPipeline': 301,
        # 'crawlab.CrawlabPipeline': 300,
    }

LOG_LEVEL = 'DEBUG'
COOKIES_ENABLED = False
LOG_STDOUT = True
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 10
