# Scrapy settings for baidu project
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
import scrapy.utils.misc
import scrapy.core.scraper


def warn_on_generator_with_return_value_stub(spider, callable):
    pass


scrapy.utils.misc.warn_on_generator_with_return_value = warn_on_generator_with_return_value_stub
scrapy.core.scraper.warn_on_generator_with_return_value = warn_on_generator_with_return_value_stub

BOT_NAME = 'baidu'

SPIDER_MODULES = ['baidu.spiders']
NEWSPIDER_MODULE = 'baidu.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'baidu (+http://www.yourdomain.com)'

MACHINE_ENV = os.environ.get('env', 'dev')
print("machine env={}".format(MACHINE_ENV))

if MACHINE_ENV == 'online':
    DOWNLOADER_MIDDLEWARES = {
        'misc.middleware.CustomHttpsProxyMiddleware': 399,
        'misc.middleware.TooManyRequestsRetryMiddleware': 400,
        'misc.middleware.BaiduUserAgentMiddleware': 401,

    }

    ITEM_PIPELINES = {
        # 'baidu.pipelines.JsonWithEncodingPipeline': 300,
        # 'baidu.pipelines.RedisPipeline': 301,
        'crawlab.CrawlabPipeline': 300,
    }
else:
    DOWNLOADER_MIDDLEWARES = {
        'misc.middleware.CustomHttpsProxyMiddleware': 400,
        'misc.middleware.BaiduUserAgentMiddleware': 401,

    }

    ITEM_PIPELINES = {
        'baidu.pipelines.JsonWithEncodingPipeline': 300,
        # 'baidu.pipelines.RedisPipeline': 301,
        # 'crawlab.CrawlabPipeline': 300,
    }

LOG_LEVEL = 'INFO'
LOG_STDOUT = True
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 10
AUTOTHROTTLE_ENABLED = True
RETRY_HTTP_CODES = [302]
