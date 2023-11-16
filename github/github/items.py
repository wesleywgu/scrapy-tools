# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class githubItem(Item):
    # define the fields for your item here like:
    repo_name = Field()
    desc = Field()
    last_update = Field()
    url = Field()


class CommitItem(Item):
    # define the fields for your item here like:
    url = Field()
    title = Field()
    time = Field()
    author = Field()
