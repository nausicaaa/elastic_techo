import datetime

import scrapy
from scrapy.contrib.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from lxml import html

from techo_scraper.items import Product


class TechoSpider(scrapy.Spider):
    name = "techo"
    allowed_domains = ["ezakupy.tesco.pl"]
    start_urls = (
            # page numeration starts with 1
            'https://ezakupy.tesco.pl/groceries/pl-PL/shop/owoce-warzywa/all?page=1',
    )

    Rules = (Rule(LinkExtractor(allow=(),
                                restrict_xpaths=('//a[@class="pagination--button prev-next"]',)
                                ),
                  callback="parse",
                  follow= True),)

    def parse(self, response):
        site = html.fromstring(response.body_as_unicode())
        names = site.xpath('//a[contains(@class, "product-tile--title product-tile--browsable")]')
        prices = site.xpath('//div[contains(@class, "price-per-quantity-weight")]//span[contains(@class, "value")]')
        currencies = site.xpath('//span[contains(@class, "currency")]')
        kg_or_szts = site.xpath('//span[contains(@class, "weight")]')
        for name, price, currency, kg_or_szt in zip(names, prices, currencies, kg_or_szts):
            unit = currency.text + kg_or_szt.text
            p = Product(name=name.text, price=price.text, currency=currency.text, kg_or_szt=kg_or_szt.text, unit=unit,
                        last_updated=datetime.datetime.now())
            # print("AA", p["name"], p["kg_or_szt"], p["currency"], unit)
            
        next_page = response.xpath("//a[contains(span/@class, 'icon-icon_whitechevronright') and not(contains(@class, 'disabled'))]/@href").extract()
        if next_page:
            next_href = next_page[0]
            next_page_url = 'https://ezakupy.tesco.pl' + next_href
            print("Scraped products from url with number:", next_href)
            request = scrapy.Request(url=next_page_url)
            yield request