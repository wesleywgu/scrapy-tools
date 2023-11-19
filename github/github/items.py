# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class githubItem(Item):
    # define the fields for your item here like:
    repo_name = Field()
    desc = Field()
    pub_time = Field()
    url = Field()
    craw_time = Field()
    source_url = Field()


class CommitItem(Item):
    # define the fields for your item here like:
    url = Field()
    title = Field()
    pub_time = Field()
    author = Field()
    craw_time = Field()
    source_url = Field()
