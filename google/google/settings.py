# Scrapy settings for google project
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

BOT_NAME = 'google'

SPIDER_MODULES = ['google.spiders']
NEWSPIDER_MODULE = 'google.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'google (+http://www.yourdomain.com)'

DOWNLOADER_MIDDLEWARES = {
    'misc.middleware.CustomHttpProxyMiddleware': 400,
    'misc.middleware.CustomUserAgentMiddleware': 401,
}

ITEM_PIPELINES = {
    # 'google.pipelines.JsonWithEncodingPipeline': 300,
    # 'google.pipelines.RedisPipeline': 301,
}

LOG_LEVEL = 'DEBUG'

DOWNLOAD_DELAY = 1
