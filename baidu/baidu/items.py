# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class BaiduNewsItem(Item):
    # define the fields for your item here like:
    title = Field()
    author = Field()
    pub_time = Field()
    desc = Field()
    url = Field()
    title = Field()