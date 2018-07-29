#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from pyquery import PyQuery as pq
from config import *
import pymongo

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

# browser = webdriver.Chrome()
# 设置不显示浏览器界面
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
# 如果没有添加环境变量，需要添加chromedriver路径
browser = webdriver.Chrome(executable_path=r'C:\Users\admin\.virtualenvs\selenium-lib-nobG1dkn\Scripts\chromedriver.exe', chrome_options=chrome_options)
# browser = webdriver.PhantomJS(service_args=SERVICE_ARGS, executable_path=r'D:\phantomjs-2.1.1-windows\phantomjs-2.1.1-windows\bin\phantomjs.exe')
wait = WebDriverWait(browser, 10)

# 设置窗口大小
# browser.set_window_size(1400, 900)

def search():
    try:
        browser.get('https://www.taobao.com/')
        # 等待时间10秒
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button')))
        input.send_keys(KEYWORD)
        submit.click()

        total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total')))
        get_product()
        return total.text
    except TimeoutException:
        print('search timeout')
        return search()

def next_page(page_number):
    try:
        input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
            )
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number)))
        get_product()
    except TimeoutException:
        print('find error')
        next_page(page_number)

def get_product():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image' : item.find('.pic .img').attr('data-src'),
            'price' : item.find('.price').text().replace("\n",""),
            'deal' : item.find('.deal-cnt').text(),
            'title' : item.find('.title').text(),
            'shop' : item.find('.shop').text(),
            'location' : item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('save ok', result)
            pass
    except Exception:
        print('save error', result)
        pass


def main():
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))
    for i in range(2, total + 1):
        next_page(i)


if __name__ == '__main__':
    main()