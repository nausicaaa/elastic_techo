import scrapy


class Product(scrapy.Item):
    name = scrapy.Field()
    price = scrapy.Field()
    unit = scrapy.Field()
    volume = scrapy.Field()
    when = scrapy.Field()
    category = scrapy.Field()
    url = scrapy.Field()

