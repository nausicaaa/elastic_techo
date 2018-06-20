import datetime
import logging
import re

import scrapy
from colorlog import ColoredFormatter
from scrapy.contrib.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from lxml import html

from techo_scraper.items import Product

log = logging.getLogger('techo')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(ColoredFormatter())
log.addHandler(ch)


class TechoSpider(scrapy.Spider):
    TESCO_URL = 'https://ezakupy.tesco.pl'
    name = 'techo'
    allowed_domains = ['ezakupy.tesco.pl']
    start_urls = (
        'https://ezakupy.tesco.pl/groceries/pl-PL/shop/',
    )

    Rules = (Rule(
        LinkExtractor(allow=(),
                      ),
        callback='parse',
        follow=True),)

    def parse(self, response):
        categories = {
            selector.xpath('span[@class="list-item-single-line"]/text()').get(): selector.xpath('@href').get()
            for selector in response.xpath('//div[@class="current"]//a')
        }
        for category_name, category_uri in categories.items():
            yield scrapy.Request(
                f'{self.TESCO_URL}{category_uri}/all',
                callback=self.parse_categories,
                meta={'category_name': category_name}
            )

    def parse_categories(self, response):
        dom = html.fromstring(response.body)
        category_name = response.meta.get('category_name')
        uris = dom.xpath('//a[contains(@class, "product-tile--title product-tile--browsable")]/@href')
        names = dom.xpath('//a[contains(@class, "product-tile--title product-tile--browsable")]')
        prices = dom.xpath('//div[contains(@class, "price-per-quantity-weight")]//span[contains(@class, "value")]')
        currencies = dom.xpath('//span[contains(@class, "currency")]')
        kg_or_szts = dom.xpath('//span[contains(@class, "weight")]')
        for name, price, currency, kg_or_szt, uri in zip(names, prices, currencies, kg_or_szts, uris):
            maybe_volume = re.search(r'[\d,]+\s*(g|kg|ml|szt)', name.text)
            if maybe_volume:
                volume = maybe_volume.group()
                self.crawler.stats.inc_value('regex matched', 1)
            else:
                volume = None
                self.crawler.stats.inc_value('regex not matched', 1)
            unit = f'{currency.text}{kg_or_szt.text}'
            p = Product(
                name=name.text,
                price=float(price.text.replace(",", ".")),
                unit=unit,
                volume=volume,
                category=category_name,
                url=f'{self.TESCO_URL}{uri}',
                when=datetime.datetime.now(),
            )
            yield p

        next_page = response.xpath(
            "//a[contains(span/@class, 'icon-icon_whitechevronright') and not(contains(@class, 'disabled'))]/@href"
        ).extract()
        if next_page:
            next_href = next_page[0]
            next_page_url = f'{self.TESCO_URL}{next_href}'
            log.info(f'Scraped products from url with number:{next_href}')
            request = scrapy.Request(
                url=next_page_url,
                callback=self.parse_categories,
                meta={'category_name': category_name}
            )
            yield request
