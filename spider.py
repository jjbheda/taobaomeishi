import json
import os

from pyquery import PyQuery as pq
from config import *
import pymongo
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chromedriver = '/usr/local/bin/chromedriver'
os.environ["webdriver.chrome.driver"] = chromedriver
browser = webdriver.Chrome(chromedriver)


# browser = webdriver.PhantomJS(service_args=SERVICE_ARGS)
wait = WebDriverWait(browser, 60)


def login():
    os.remove('cookies_tao.json')
    browser.get('https://login.taobao.com/member/login.jhtml?spm=a21bo.2017.754894437.1.5af911d9A3avuP&f=top&redirectURL=https%3A%2F%2Fwww.taobao.com%2F')
    input("请回车登录")
    dictCookies = browser.get_cookies()
    jsonCookies = json.dumps(dictCookies)
    # 登录完成后,将cookies保存到本地文件
    with open("cookies_tao.json", "w") as fp:
        fp.write(jsonCookies)


def search():
    # 删除第一次登录是储存到本地的cookie
    browser.delete_all_cookies()
    # 读取登录时储存到本地的cookie
    with open("cookies_tao.json", "r", encoding="utf8") as fp:
        ListCookies = json.loads(fp.read())

    from selenium.common.exceptions import TimeoutException
    try:
        browser.get(url = 'https://www.taobao.com')
        for item in ListCookies:
            browser.add_cookie(item)
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q')))
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button')))
        input.send_keys('美食')
        submit.click()
        total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.total')))
        get_products()
        return total.text

    except TimeoutException:
        pass


def next_page(page_number):
    from selenium.common.exceptions import TimeoutException
    try:
        input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input')))
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number)))
        get_products()
    except TimeoutException:
           next_page(page_number)


def get_products():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'deal': item.find('deal-cnt').text()[:-3],
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)


def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到MongoDB成功',result)
    except Exception:
        print('存储到MongoDb失败',result)


def main():
    total = search()
    import re
    total = int(re.compile('(\d+)').search(total).group(1))
    # print(total)
    for i in range(2, 5 + 1):
        next_page(i)

    browser.close()

if __name__ == '__main__':
    login()
    main()



