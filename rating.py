from datetime import datetime
import json
import scrapy
import re


class CommetSpider(scrapy.Spider):
    name = 'rating'
    start_urls = ['https://www.dresslily.com/hoodies-c-181.html']
    headers = {"X-Requested-With": "XMLHttpRequest"}

    def parse(self, response, *kwargs):
        links = set(response.xpath('//div[@class="category-right-part clearfix"]'
                                   '/div[@class="category-list js-category"]'
                                   '/div[contains(@class, "js-good js-dlGood")]//a[1]/@href').extract())
        for link in links:
            product_id = re.findall(r"product(.*?)\.html", link)[0]
            print(link)
            yield scrapy.Request(url=f"https://www.dresslily.com/"
                                     f"m-review-a-view_review_list-goods_id-{product_id}-page-1?odr=0",
                                 headers=self.headers, callback=self.get_rating)
        urlpage = response.xpath('//div[@class="site-pager-pad-pc site-pager"]/ul/li[last()]//@href').extract_first()
        if urlpage:
            yield scrapy.Request(url=response.urljoin(urlpage), callback=self.parse)

    def get_rating(self, response):
        review = json.loads(response.body)
        for rew in review['data']['review']['review_list']:
            data = dict()
            data['product_id'] = re.findall(r"goods_id-(.*?)-", response.url)[0]
            data['time'] = datetime.strptime(rew['adddate'], '%b,%d  %Y %H:%M:%S').timestamp()
            data['reate'] = rew['rate_overall'] or 0
            data['text'] = rew['pros'] or ''
            try:
                data['color'] = rew['goods']['color']
                data['size'] = rew['goods']['size']
            except:
                data['color'] = ''
                data['size'] = ''
            yield data

        if review['data']['page_count']:
            for i in range(2, review['data']['page_count']+1):
                yield scrapy.Request(
                    url=f"https://www.dresslily.com/m-review-a-view_review_list-goods_id-"
                        f"{data['product_id']}-page-{i}?odr=0",
                    headers=self.headers, callback=self.get_rating)
