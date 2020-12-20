import os
import random
import json
import time
import argparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from urllib.parse import urljoin
from progress.bar import Bar

HEADERS = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'}

class Peopo():
    def __init__(self, out_dir, period=31):
        self.domain_url = "https://www.peopo.org"
        self.postfix = "/tag/28916%2B2"
        self.out_dir = out_dir
        self.cate_list = ['政治經濟', '社會關懷']
        self.period = period
        
    def _del_special_char(self, s):
        s = s.replace(u'\u3000', ' ')
        s = s.replace(u'\xa0', ' ')
        return s
    
    def _find_keywords(self, soup):
        keywords = []
        try:
            for div in soup.find_all('div', 'field-label'):
                if "標籤" in div.text:
                    tag_lists = div.find_next().find_all('li')
                    for li in tag_lists:
                        keywords.append(li.text.strip())
            if keywords is None:
                keywords = ''
            else:
                keywords = '、'.join(keywords)
        except:
            print("標籤 NOT FOUND")
        return keywords
        
    def _find_content(self, soup):
        content = ''
        try:
            content_body = soup.find('div', 'field-name-body')
            for p in content_body.find_all('p'):
                content += p.text.strip()
        except:
            print("CONTENT NOT FOUND")
        return content

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
        for category in self.cate_list:
            articles_list = []
            page = 1
            while True:
                resp = requests.get(self.domain_url+self.postfix, 
                                    headers = HEADERS, 
                                    params={
                                        'g': category,
                                        'page': str(page)
                                    })
                if resp.status_code != 200:
                    print("REQUEST ERROR! ON PAGE: ", page)
                else:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    try:
                        grids = soup.find_all('div','grid-row')
                        for grid in grids:
                            title = grid.find('h3').text.strip()
                            author = grid.find('span', 'author-name').text.strip()
                            newslink = urljoin(self.domain_url,grid.find('h3', 'view-list-title').a['href'].strip())
                            dt = grid.find('div', 'view-list-date').text.strip()
                            articles_list.append({
                                'title': title,
                                'author': author,
                                'datetime': dt,
                                'newslink': newslink,
                                'label': category,
                                'website': "Peopo公民新聞",
                            })
                        print("PAGE: {} SUCCESSFUL!".format(page))
                    except Exception as E:
                        print(E)
                        print("The web page might change")
                        
                    f_dt = datetime.strptime(dt, '%Y-%m-%d %H:%M').date()
                    if (f_dt >= last_month_day):
                        page = page + 1
                    else:
                        # break while loop
                        print('\n{} ~ {} 完成'.format(f_dt, today))
                        break
                time.sleep(random.randint(3, 7))
            self.write_json_articles(category, articles_list, 'list')
            cate_article_list[category] = articles_list
        
        self.cate_article_list = cate_article_list
        return cate_article_list
    
    def crawl_articles_content(self):
        for category in self.cate_list:
            article_list = []
            print('Process all articles: ', len(self.cate_article_list[category]))
            with Bar('Processing', max=len(self.cate_article_list[category])) as bar: 
                for article in self.cate_article_list[category]:
                    # print(article['title'])
                    resp = requests.get(article['newslink'], headers=HEADERS)
                    if resp.status_code != 200:
                        print("{} BAD REQUESTS!", url)
                    else:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        article['keyword'] = self._find_keywords(soup)
                        article['content'] = self._del_special_char(self._find_content(soup))
                        article_list.append(article)
                    bar.next()
                self.write_json_articles(category, article_list, 'news')
        return article_list

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Peopo Web Crawler')
    parser.add_argument('--out_dir', type=str, help='output directory')
    parser.add_argument('--period', type=int, help='crawler time range')
    args = parser.parse_args()
    peopo = Peopo(args.out_dir)
    if args.period is not None:
        peopo = Peopo(args.out_dir, args.period)
    article_list = peopo.crawl_articles_list()
    _ = peopo.crawl_articles_content()