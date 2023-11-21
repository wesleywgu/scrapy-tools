# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class githubItem(Item):
    # define the fields for your item here like:
    content = Field()
    author = Field()
    url = Field()
    pub_time = Field()
    craw_time = Field()
    source_url = Field()


class CommitItem(Item):
    # define the fields for your item here like:
    content = Field()
    author = Field()
    url = Field()
    pub_time = Field()
    craw_time = Field()
    source_url = Field()
