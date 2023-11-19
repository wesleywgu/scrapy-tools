# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class twitterItem(Item):
    # define the fields for your item here like:
    user_name = Field()
    pub_time = Field()
    text = Field()
    url = Field()
    craw_time = Field()
    source_url = Field()
