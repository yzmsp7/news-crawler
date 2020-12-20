import os
import random
import json
import time
import requests
import argparse
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from progress.bar import Bar

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15"
HEADERS = {'user-agent': UA}
NEWSNAME = '芋傳媒'

class TaroNews:
    def __init__(self, out_dir):
        self.domain_url = "https://taronews.tw/"
        self.cate_index = {'政治':'politics','國際':'world'}
        self.out_dir = out_dir
        
    def _crawl_content(self, soup):
        content = ''
        try:
            content_div = soup.find('div', 'single-post-content')
            for div_p in content_div.find_all('p'):
                content += div_p.text.strip()
        except:
            print('CANNOT FIND content div')

        return content
    
    def _crawl_keywords(self, soup):
        tags = []
        try:
            for tag in soup.find('div', 'post-tags').find_all('a'):
                tags.append(tag.text.strip())
        except:
            print('CANNOT FIND Keywords')
        return '、'.join(tags)

    def _crawl_badges(self, soup):
        badges = []
        try:
            for badge in soup.find('div', 'term-badges'):
                badges.append(badge.a.text.strip())
        except:
            print('CANNOT FIND badges')
        return '、'.join(badges)


    def write_json_articles_list(self, category, data):        
        aclist_dir = os.path.join(self.out_dir, category, 'list')
        if not os.path.exists(aclist_dir):
            os.makedirs(aclist_dir)
            print("create directory: {} successfully".format(aclist_dir))
        today = datetime.strftime(date.today(), "%Y%m%d")
        filename = os.path.join(aclist_dir,'articles_list_{}.json'.format(today))
        try:
            with open(filename, 'w') as outfile:
                json.dump(data, outfile,ensure_ascii=False)
            print("articles list write to json file successfully")
        except:
            print("articles list write to json file fail")
        return
    
    def write_json_news(self, category, data):        
        aclist_dir = os.path.join(self.out_dir, category, 'news')
        if os.path.exists(aclist_dir):
            print('directory: {} exists'.format(aclist_dir))
        else:
            os.makedirs(aclist_dir)
            print("create directory: {} successfully".format(aclist_dir))
        today = datetime.strftime(date.today(), "%Y%m%d")
        filename = os.path.join(aclist_dir,'news_{}.json'.format(today))
        try:
            with open(filename, 'w') as outfile:
                json.dump(data, outfile,ensure_ascii=False)
            print("all news write to json file successfully")
        except:
            print("all news write to json file fail")
        return
    

    def request_page(self,url):
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print('BAD REQUEST')
        soup = BeautifulSoup(resp.text,'html.parser')
        return soup

    def parse_article_content(self,url):
        soup = self.request_page(url)
        content = self._crawl_content(soup)
        keywords = self._crawl_keywords(soup)
        labels = self._crawl_badges(soup)
    
        return content, keywords, labels
    
    def crawl_articles_list(self):
        today = date.today()
        # 31 days as a month (absolutely)
        last_month_day = today - timedelta(days=31)
        category_articles = {}
        # for each category
        for category in self.cate_index:
            print('正在爬芋傳媒[{}]...'.format(category))
            page = 1
            print('Page: ', end='')
            while True:
                articles_list = []
                print(str(page)+'...', end='')
                target_url = urljoin(self.domain_url, 'category/{}/page/{}'.format(
                    self.cate_index[category], page))

                soup = self.request_page(target_url)
                divs = soup.find_all('div', 'item-inner')
                # This is for lists of news
                for div in divs:
                    # check for not politics related div
                    if div.h2 is None:
                        break
                    title = div.h2.text.strip()
                    newslink = div.h2.a['href'].strip()
                    author = div.find('i','post-author').text.strip()
                    dt = div.find('span', 'time').text.strip()
                    # data = self._convert2dict([title,author,datetime,content,keywords,newslink,labels])
                    data = {'title': title,'author': author,'datetime': dt,'newslink': newslink}
                    _ = articles_list.append(data)
                f_dt = datetime.strptime(dt, "%Y-%m-%d %H:%M")
                if f_dt.date() >= last_month_day:
                    # random wait
                    time.sleep(random.randint(2, 8))
                    page = page + 1
                else:
                    print('\n{} ~ {} 完成'.format(f_dt.date(), today))
                    # break while True
                    break 
            category_articles[category] = articles_list
            self.write_json_articles_list(self.cate_index[category],articles_list)
        return category_articles
    
    def crawler_inner_content(self, cate_article_list):
        for cate in cate_article_list:
            newslist = []
            with Bar('Processing', max=len(cate_article_list[cate])) as bar:   
                for data in cate_article_list[cate]:
                    try:
                        content, keywords, labels = self.parse_article_content(data['newslink'])
                        # print(data['newslink'], ' success')
                    except:
                        print(data['newslink'], ' failed')
                    data['content'] = content
                    data['keyword'] = keywords
                    data['label'] = labels
                    data['website'] = '芋傳媒'
                    _ = newslist.append(data)
                    bar.next()
            self.write_json_news(self.cate_index[cate], newslist)
        return

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Taro News Web Crawler')
    parser.add_argument('--out_dir', type=str, help='output directory')
    args = parser.parse_args()
    taro = TaroNews(out_dir=args.out_dir)
    taro_articles = taro.crawl_articles_list()
    taro.crawler_inner_content(taro_articles)
