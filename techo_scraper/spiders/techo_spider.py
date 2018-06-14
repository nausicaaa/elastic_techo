import datetime

import scrapy
from scrapy.contrib.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from lxml import html

from techo_scraper.items import Product


class TechoSpider(scrapy.Spider):
    TESCO_URL = 'https://ezakupy.tesco.pl'
    name = "techo"
    allowed_domains = ["ezakupy.tesco.pl"]
    start_urls = (
        'https://ezakupy.tesco.pl/groceries/pl-PL/shop/',
    )

    Rules = (Rule(
        LinkExtractor(allow=(),
                      ),
        callback="parse",
        follow=True),)

    def parse(self, response):
        categories = {
            selector.xpath('span[@class="list-item-single-line"]/text()').get(): selector.xpath('@href').get()
            for selector in response.xpath('//div[@class="current"]//a')
        }
        for category_name, category_uri in categories.items():
            category_uri = f'{self.TESCO_URL}{category_uri}/all'
            yield scrapy.Request(
                category_uri,
                callback=self.parse_categories,
                meta={'category_name': category_name, 'uri': category_uri}
            )

    def parse_categories(self, response):
        dom = html.fromstring(response.body)
        category_name = response.meta.get('category_name')
        uri = response.meta.get('uri')
        names = dom.xpath('//a[contains(@class, "product-tile--title product-tile--browsable")]')
        prices = dom.xpath('//div[contains(@class, "price-per-quantity-weight")]//span[contains(@class, "value")]')
        currencies = dom.xpath('//span[contains(@class, "currency")]')
        kg_or_szts = dom.xpath('//span[contains(@class, "weight")]')
        for name, price, currency, kg_or_szt in zip(names, prices, currencies, kg_or_szts):
            unit = currency.text + kg_or_szt.text
            p = Product(
                name=name.text,
                price=price.text,
                currency=currency.text,
                kg_or_szt=kg_or_szt.text,
                unit=unit,
                category=category_name,
                category_url=uri,
                last_updated=datetime.datetime.now(),
            )
            yield p

        next_page = response.xpath(
            "//a[contains(span/@class, 'icon-icon_whitechevronright') and not(contains(@class, 'disabled'))]/@href"
        ).extract()
        if next_page:
            next_href = next_page[0]
            next_page_url = f'{self.TESCO_URL}{next_href}'
            self.logger.info(f'Scraped products from url with number:{next_href}')
            request = scrapy.Request(
                url=next_page_url,
                callback=self.parse_categories,
                meta={'category_name': category_name, 'uri': uri}
            )
            yield request
