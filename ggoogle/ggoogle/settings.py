# Scrapy settings for ggoogle project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

import os
import sys
from os.path import dirname

path = dirname(dirname(dirname(os.path.abspath((__file__)))))
sys.path.append(path)

BOT_NAME = 'ggoogle'

SPIDER_MODULES = ['ggoogle.spiders']
NEWSPIDER_MODULE = 'ggoogle.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'ggoogle (+http://www.yourdomain.com)'

MACHINE_ENV = os.environ.get('env','dev')
print("machine env={}".format(MACHINE_ENV))

if MACHINE_ENV == 'online':
    DOWNLOADER_MIDDLEWARES = {
        # 'misc.middleware.LocalHttpProxyMiddleware': 400,
        'misc.middleware.GoogleUserAgentMiddleware': 401,
    }

    ITEM_PIPELINES = {
        # 'ggoogle.pipelines.JsonWithEncodingPipeline': 300,
        # 'ggoogle.pipelines.RedisPipeline': 301,
        'crawlab.CrawlabPipeline': 300,
    }
else:
    DOWNLOADER_MIDDLEWARES = {
        'misc.middleware.LocalHttpProxyMiddleware': 400,
        'misc.middleware.GoogleUserAgentMiddleware': 401,
    }

    ITEM_PIPELINES = {
        'ggoogle.pipelines.JsonWithEncodingPipeline': 300,
        # 'ggoogle.pipelines.RedisPipeline': 301,
        # 'crawlab.CrawlabPipeline': 300,
    }

LOG_LEVEL = 'INFO'
COOKIES_ENABLED = False
LOG_STDOUT = True
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 10
