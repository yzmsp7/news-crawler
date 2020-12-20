import os
import random
import json
import time
import requests
import argparse
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from urllib.parse import urljoin
from progress.bar import Bar

HEADERS = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'}

class Wealth():
    def __init__(self, out_dir, period=31):
        self.domain_url = "https://www.wealth.com.tw"
        self.category_index = {'焦點新聞-國際':1, '政治風雲': 2, '財經動態': 3}
        self.out_dir = out_dir
        self.period = period
    
    def _delSpecialChar(self, s):
        s = s.replace(u'\u3000', ' ')
        s = s.replace(u'\xa0', ' ')
        return s

    def _findContent(self, soup):
        content = ''
        try:
            if soup.find('p', 'main-img-intro'):
                soup.find('p', 'main-img-intro').extract()

            for p in soup.find('div', 'entry-content').find_all('p'):
                if p.text == "延伸閱讀：":
                    break
                content += self._delSpecialChar(p.text.strip())
        except:
            print('CONTENT NOT FOUND')
        return content
    

    def _findKeyword(self, soup):
        keyword = ''
        try:
            keyword = soup.find('div','article-tag mb20').find('p', 'f-s14').text[5:].strip()
        except:
            print('KEYWORD NOT FOUND')
        return keyword
    

    def write_json_articles(self, category, data, dir_='list'):
        aclist_dir = os.path.join(self.out_dir, category, dir_)
        if not os.path.exists(aclist_dir):
            os.makedirs(aclist_dir)
            print("create directory: {} successfully".format(aclist_dir))
        today = datetime.strftime(date.today(), "%Y%m%d")
        filename = os.path.join(aclist_dir,'articles_list_{}.json'.format(today))
        try:
            with open(filename, 'w') as outfile:
                json.dump(data, outfile, ensure_ascii=False)
                print("articles list write to json file successfully")
        except:
            print("articles list write to json file fail")

    def crawl_articles_list(self):
        cate_article_list = {}
        today = date.today()
        last_month_day = today - timedelta(days=self.period)
        for category in self.category_index:
            print("Now process category: ", category)
            articles_list = []
            page = 1
            while True:
                resp = requests.get(urljoin(self.domain_url, "home/articles"), 
                                    params = {
                                        'category_id':self.category_index[category],
                                        'page':page
                                    }, 
                                    headers = HEADERS)

                if resp.status_code != 200:
                    print("url: {} has wrong!".format(resp.url))
                else:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    news_articles = soup.find_all("article", "b-post_main")
                    for article in news_articles:
                        newslink = urljoin(self.domain_url,article.a['href'].strip())
                        meta_info_divs = article.find('div', 'entry-meta').find_all('span')
                        meta_info = [meta.text.strip() for meta in meta_info_divs]
                        dt = meta_info[0]
                        author = meta_info[1][4:] # get rid of 作者:
                        title = self._delSpecialChar(article.find('h2','entry-title').text.strip())
                        articles_list.append({
                            'title': title,
                            'author': author,
                            'datetime': dt,
                            'newslink': newslink,
                            'label': category,
                            'website': "財訊",
                        })
                    f_dt = datetime.strptime(dt, '%Y-%m-%d').date()
                    if (f_dt >= last_month_day):
                        page = page + 1
                    else:
                        # break while loop
                        print('\n{} ~ {} 完成'.format(f_dt, today))
                        break
            self.write_json_articles(category, articles_list, 'list')
            cate_article_list[category] = articles_list

        self.cate_article_list = cate_article_list
        return cate_article_list
    
    def crawl_articles_content(self):
        for category in self.category_index:
            article_list = []
            print('Process num of articles: ', len(self.cate_article_list[category]))
            with Bar('Processing', max=len(self.cate_article_list[category])) as bar: 
                for article in self.cate_article_list[category]:
                    resp = requests.get(article['newslink'], headers = HEADERS)
                    
                    soup = BeautifulSoup(resp.text, "html.parser")
                    article['content'] = self._findContent(soup)
                    article['keyword'] = self._findKeyword(soup)
                    article_list.append(article)
                    bar.next()
            self.write_json_articles(category, article_list, 'news')
        return article_list
    
if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Wealth Web Crawler')
    parser.add_argument('--out_dir', type=str, help='output directory')
    parser.add_argument('--period', type=int, help='crawler time range')
    args = parser.parse_args()
    wealth = Wealth(args.out_dir)
    if args.period is not None:
        wealth = Wealth(args.out_dir, args.period)
    article_list = wealth.crawl_articles_list()
    _ = wealth.crawl_articles_content()