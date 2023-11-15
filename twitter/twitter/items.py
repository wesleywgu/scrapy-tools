# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class twitterItem(Item):
    # define the fields for your item here like:
    user_name = Field()
    user_id = Field()
    pub_time = Field()
    text = Field()
    post_url = Field()
