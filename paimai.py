#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'liu-mou'
__mtime__ = '2018-12-25'
 
# 欢迎进入我的主页：https://www.cnblogs.com/liu-mou/
"""

import re
import urllib
import pymongo
from config import *
from pyquery import PyQuery as pq
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# 连接MongoDB
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

# 配置chrome无头浏览模式
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')

browser = webdriver.Chrome(chrome_options=chrome_options)
wait = WebDriverWait(browser, 10)

browser.set_window_size(1400, 900)

# url中省份字段需使用gb2312编码
province = urllib.parse.quote(PROVINCE, encoding='gb2312')


def search():
    print('正在搜索')
    try:
        browser.get('https://sf.taobao.com/item_list.htm?&province=' +
                    province + '&auction_start_seg=30&page=1')
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.page-total')))
        get_products()
        return total.text
    except TimeoutException:
        return search()


def next_page(page_number):
    print('正在翻页', page_number)
    try:
        input = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'body > div.sf-wrap > div.pagination.J_Pagination > span.page-skip > label > input'))
        )
        submit = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'body > div.sf-wrap > div.pagination.J_Pagination > span.page-skip > button')))
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, 'body > div.sf-wrap > div.pagination.J_Pagination > span.current'), str(page_number)))
        get_products()
    except TimeoutException:
        next_page(page_number)


def get_products():
    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'body > div.sf-wrap > div.sf-content > div.sf-item-list > ul')))
    html = browser.page_source
    doc = pq(html)
    items = doc('.pai-item').items()
    for item in items:
        info = item.find('.info-section').text(),
        info = info[0].split()
        footer = item.find('.footer-section').text(),
        product = {
            'url': item.find('a').attr.href,
            'title': item.find('.header-section').text(),
            'Starting price': info[1].strip('¥'),
            'Starting price U': info[2],
            'Current price': info[4].strip('¥'),
            'Current price U': info[5],
            'Evaluation price': info[12] + info[13],
            'Start time': info[15] + info[16],
            'end_time': info[-2] + info[-1],
            'footer': footer
        }
        save_to_mongo(product)


def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到MONGODB成功', result)
    except Exception as e:
        print('存储到MONGODB失败', result)


def main():
    try:
        total = int(re.compile('(\d+)').search(total).group(1))
        search()
        for i in range(1, total + 1):
            next_page(i)
        print(total)
    except Exception as e:
        print('出错啦')
    finally:
        browser.close()


if __name__ == '__main__':
    main()
