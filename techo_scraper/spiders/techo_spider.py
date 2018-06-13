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
            # 'https://ezakupy.tesco.pl/groceries/pl-PL/shop/owoce-warzywa/all?page=1',
            'https://ezakupy.tesco.pl/groceries/pl-PL/shop/',
    )

    Rules = (Rule(LinkExtractor(allow=(),
                                # restrict_xpaths=('//a[@class="pagination--button prev-next"]',)
                                ),
                  callback="parse",
                  follow=True),)

    def parse(self, response):
        cats_urls = response.xpath('//div[@class="current"]//a')
        cats_with_urls = [(_.select('span[@class="list-item-single-line"]/text()').get(), _.select('@href').get()) for _ in cats_urls]
        for cat_name, cat_url in cats_with_urls:
            cat_url = 'https://ezakupy.tesco.pl/' + cat_url + '/all'
            yield scrapy.Request(cat_url, callback=self.parse_categories,
                                 meta={'category': cat_name,
                                       'url': cat_url})

    def parse_categories(self, response):
        site = html.fromstring(response.body_as_unicode())
        category = response.meta.get('category')
        url = response.meta.get('url')
        names = site.xpath('//a[contains(@class, "product-tile--title product-tile--browsable")]')
        prices = site.xpath('//div[contains(@class, "price-per-quantity-weight")]//span[contains(@class, "value")]')
        currencies = site.xpath('//span[contains(@class, "currency")]')
        kg_or_szts = site.xpath('//span[contains(@class, "weight")]')
        for name, price, currency, kg_or_szt in zip(names, prices, currencies, kg_or_szts):
            unit = currency.text + kg_or_szt.text
            p = Product(name=name.text, price=price.text, currency=currency.text, kg_or_szt=kg_or_szt.text, unit=unit,
                        category=category, url=url, last_updated=datetime.datetime.now())
            # print("AA", p["name"], p['category'], p["url"])

        next_page = response.xpath("//a[contains(span/@class, 'icon-icon_whitechevronright') and not(contains(@class, 'disabled'))]/@href").extract()
        if next_page:
            next_href = next_page[0]
            next_page_url = 'https://ezakupy.tesco.pl' + next_href
            print("Scraped products from url with number:", next_href)
            request = scrapy.Request(url=next_page_url)
            yield request