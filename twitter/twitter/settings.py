# Scrapy settings for twitter project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

import sys
import os
from os.path import dirname
from shutil import which

path = dirname(dirname(os.path.abspath(os.path.dirname(__file__))))
sys.path.append(path)
path = dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(path)
from misc.log import *

BOT_NAME = 'twitter'

SPIDER_MODULES = ['twitter.spiders']
NEWSPIDER_MODULE = 'twitter.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'twitter (+http://www.yourdomain.com)'

MACHINE_ENV = os.environ.get('env', 'dev')

# COOKIES_ENABLED = False
LOG_STDOUT = True
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 10
AUTOTHROTTLE_ENABLED = True

SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = which('chromedriver')

if MACHINE_ENV == 'online':
    DOWNLOADER_MIDDLEWARES = {
        # 'misc.middleware.CustomHttpProxyMiddleware': 400,
        'misc.middleware.SeleniumMiddleware': 401,
    }

    ITEM_PIPELINES = {
        # 'twitter.pipelines.JsonWithEncodingPipeline': 300,
        # 'twitter.pipelines.RedisPipeline': 301,
        'crawlab.CrawlabPipeline': 300,
    }

    SELENIUM_DRIVER_ARGUMENTS = [
        '--headless',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        # '--proxy-server=%s' % '127.0.0.1:7890',
        '--user-agent=%s' % 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    ]
    LOG_LEVEL = 'INFO'
else:
    DOWNLOADER_MIDDLEWARES = {
        # 'misc.middleware.CustomHttpProxyMiddleware': 400,
        'misc.middleware.SeleniumMiddleware': 401,
    }

    ITEM_PIPELINES = {
        'twitter.pipelines.JsonWithEncodingPipeline': 300,
        # 'twitter.pipelines.RedisPipeline': 301,
        # 'crawlab.CrawlabPipeline': 300,
    }
    SELENIUM_DRIVER_ARGUMENTS = [
        # '--headless',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--user-agent=%s' % 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    ]
    LOG_LEVEL = 'DEBUG'
