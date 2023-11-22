# Scrapy settings for github project
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

BOT_NAME = 'github'

SPIDER_MODULES = ['github.spiders']
NEWSPIDER_MODULE = 'github.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'github (+http://www.yourdomain.com)'
MACHINE_ENV = os.environ.get('env', 'dev')
print("machine env={}".format(MACHINE_ENV))

if MACHINE_ENV == 'online':
    DOWNLOADER_MIDDLEWARES = {
        # 'misc.middleware.LocalHttpProxyMiddleware': 400,
        'misc.middleware.CustomUserAgentMiddleware': 401,
    }

    ITEM_PIPELINES = {
        # 'github.pipelines.JsonWithEncodingPipeline': 300,
        # 'github.pipelines.RedisPipeline': 301,
        'crawlab.CrawlabPipeline': 300,
    }
else:
    DOWNLOADER_MIDDLEWARES = {
        'misc.middleware.LocalHttpProxyMiddleware': 400,
        'misc.middleware.CustomUserAgentMiddleware': 401,
    }

    ITEM_PIPELINES = {
        # 'github.pipelines.JsonWithEncodingPipeline': 300,
        # 'github.pipelines.RedisPipeline': 301,
        # 'crawlab.CrawlabPipeline': 300,
    }

LOG_LEVEL = 'DEBUG'
LOG_STDOUT = True
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 10
