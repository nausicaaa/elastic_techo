import scrapy
from scrapy.contrib.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from lxml import html


class TechoSpider(scrapy.Spider):
    name = "techo"
    allowed_domains = ["ezakupy.tesco.pl"]
    start_urls = (
            # page numeration starts with 1
            'https://ezakupy.tesco.pl/groceries/pl-PL/shop/owoce-warzywa/all?page=1',
    )

    Rules = (Rule(LinkExtractor(allow=(),
                                # restrict_xpaths=('//a[@class="button next"]',)
                                ),
                  callback="parse",
                  follow= True),)

    def parse(self, response):
        site = html.fromstring(response.body_as_unicode())
        names = site.xpath('//a[contains(@class, "product-tile--title product-tile--browsable")]')
        prices = site.xpath('//div[contains(@class, "price-per-quantity-weight")]//span[contains(@class, "value")]')
        currencies = site.xpath('//span[contains(@class, "currency")]')
        kg_or_szts = site.xpath('//span[contains(@class, "weight")]')
        converter = currencies[0].text + kg_or_szts[0].text
        print(names[0].text, prices[0].text, converter, 'AAAA')

# lista produktów jest w :
# <li class="product-list--list-item first">
# dobrze by wyciągnąć ilość stron ta jak oni tam w przykładzie robią albo to olać i iterować aż do błędu.


        # follow next page links
        # next_page = response.xpath('.//a[@class="button next"]/@href').extract()
        # if next_page:
        #     next_href = next_page[0]
        #     next_page_url = 'http://sfbay.craigslist.org' + next_href
        #     request = scrapy.Request(url=next_page_url)
        #     yield request
