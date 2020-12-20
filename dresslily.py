import json
import scrapy
import re
from urllib.parse import urlencode


class DresslilySpider(scrapy.Spider):
    name = 'dresslily'
    start_urls = ['https://www.dresslily.com/hoodies-c-181.html']
    custom_settings = {
        'FEED_EXPORT_ENCODING': 'utf-8',
    }

    def parse(self, response, *kwargs):
        links = set(response.xpath('//div[@class="category-list js-category"]//a[1]/@href').extract())

        for link in links:
            print(link)
            yield scrapy.Request(url=link, callback=self.get_product_parse)
        urlpage = response.xpath('//div[@class="site-pager-pad-pc site-pager"]/ul/li[last()]//@href').extract_first()
        if urlpage:
            yield scrapy.Request(url=response.urljoin(urlpage), callback=self.parse)

    def get_product_parse(self, response):
        try:
            total_reviews = \
                re.findall(r'[0-9]+',
                           response.xpath('//div[@class="good-hgap good-basic-info"]'
                                          '//div[@class="goodprice-line-end"]'
                                          '//span[@class="review-all-count js-goreview"]//text()').extract_first())[0]
        except:
            total_reviews = None
        try:
            product_info = re.sub(r'(.+?PRODUCT INFO|\s+)|show more', ' ', ''.join(response.xpath(
                '//div[@class="good-hgap good-basic-info"]'
                '//div[@class="good-desc-container"]//text()').extract())).strip()
        except:
            product_info = None
        data = {
            'product_id': re.findall(r"product(.*?)\.html", response.url)[0],
            'product_url': response.url,
            'name': response.xpath('//div[@class="good-hgap good-basic-info"]'
                                   '/h1/span[@class="goodtitle"]/text()').extract_first(),
            'discount': None,
            'discounted_price': None,
            'original_price': None,
            'total_reviews': total_reviews,
            'product_info': product_info,
        }
        url = 'https://www.dresslily.com/fun/ajax/index.php'
        headers = {'x-requested-with': 'XMLHttpRequest',
                   'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        skus = re.findall(r'o\.goods\.sn = \"(.*?)\"', ' '.join(response.xpath('//script//text()').extract()))[0]
        body = {"jsonParam": f'[{{"action":"goods_getGoodsPrice","param":{{"skus":"{skus}"}}}}]'}


        yield scrapy.FormRequest(url=url, headers=headers, method="POST",
                                 body=urlencode(body), meta={'item_data': data},
                                 callback=self.get_parse_price)

    def get_parse_price(self, response):
        data = response.meta['item_data']
        price = list(json.loads(response.body)['data']['goods_getGoodsPrice'].values())[0]
        if price['price_type'] != 0:
            data['discount'] = price['promote_zhekou']
            data['discounted_price'] = price['shop_price']
            data['original_price'] = price['market_price']
        else:
            data['discount'] = 0
            data['discounted_price'] = 0
            data['original_price'] = price['shop_price']
        yield data
