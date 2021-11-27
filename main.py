import asyncio
import json
import time

import aiohttp
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from seleniumwire import webdriver

from сonfig import *


def sale_page():
    url = 'https://www.binance.com/ru/nft/goods/sale/14571476255560?isBlindBox=1&isOpen=false'
    driver.get(url)
    time.sleep(5)

    input_sum = driver.find_element(By.XPATH,
                                    '/html/body/div[1]/div/div[2]/main/div/div/div[5]/div[2]/div/div[1]/input')
    input_sum.click()
    input_sum.clear()
    input_sum.send_keys(5)

    time.sleep(5)
    driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/main/div/div/div[8]/button[2]').click()


def click_confirm():
    if check_exists_by_xpath('/html/body/div[4]/div/div/div[7]/button[2]'):
        confirm = driver.find_element(By.XPATH, '/html/body/div[4]/div/div/div[7]/button[2]')
    elif check_exists_by_xpath('/html/body/div[5]/div/div/div[7]/button[2]'):
        confirm = driver.find_element(By.XPATH, '/html/body/div[5]/div/div/div[7]/button[2]')
    elif check_exists_by_xpath('/html/body/div[6]/div/div/div[7]/button[2]'):
        confirm = driver.find_element(By.XPATH, '/html/body/div[6]/div/div/div[7]/button[2]')
    else:
        confirm = driver.find_element(By.XPATH, '/html/body/div[7]/div/div/div[7]/button[2]')
    ActionChains(driver).move_to_element(confirm).click().perform()
    print('Нажали confirm')

    request = driver.wait_for_request('https://www.binance.com/bapi/nft/v1/private/nft/nft-trade/product-onsale')

    cookies = request.headers['cookie']
    csrftoken = request.headers['csrftoken']
    deviceinfo = 'eyJzY3JlZW5fcmVzb2x1dGlvbiI6Ijg1OCwxNTI1IiwiYXZhaWxhYmxlX3NjcmVlbl9yZXNvbHV0aW9uIjoiOD' \
                 'EzLDE1MjUiLCJzeXN0ZW1fdmVyc2lvbiI6IldpbmRvd3MgNyIsImJyYW5kX21vZGVsIjoidW5rbm93biIsInN5' \
                 'c3RlbV9sYW5nIjoiZW4tVVMiLCJ0aW1lem9uZSI6IkdNVCs2IiwidGltZXpvbmVPZmZzZXQiOi0zNjAsInVzZX' \
                 'JfYWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCA2LjE7IFdpbjY0OyB4NjQ7IHJ2OjkzLjApIEdlY2tv' \
                 'LzIwMTAwMTAxIEZpcmVmb3gvOTMuMCIsImxpc3RfcGx1Z2luIjoiIiwiY2FudmFzX2NvZGUiOiIyOWI5YmU4My' \
                 'IsIndlYmdsX3ZlbmRvciI6Ikdvb2dsZSBJbmMuIiwid2ViZ2xfcmVuZGVyZXIiOiJBTkdMRSAoSW50ZWwoUikg' \
                 'SEQgR3JhcGhpY3MgRGlyZWN0M0QxMSB2c181XzAgcHNfNV8wKSIsImF1ZGlvIjoiMzUuNzM4MzI5NTkzMDkyMi' \
                 'IsInBsYXRmb3JtIjoiV2luMzIiLCJ3ZWJfdGltZXpvbmUiOiJBc2lhL0FsbWF0eSIsImRldmljZV9uYW1lIjoi' \
                 'RmlyZWZveCBWOTMuMCAoV2luZG93cykiLCJmaW5nZXJwcmludCI6Ijg3YmY0OTA2ZDU3NDc4ZTE0NjAwMzQwYm' \
                 'Y3MWUyYTUzIiwiZGV2aWNlX2lkIjoiIiwicmVsYXRlZF9kZXZpY2VfaWRzIjoiMTYyOTEzODQ2NTA4NHBCVTJI' \
                 'S2JOeWhjRWRKRkpHMGksMTYyOTk4Mjk5NzgwMnBPQWVDMGRmcldqUUZxV2NZTmEsMTYyOTk4NTIzMTY3MXlndG' \
                 'lyOFhBOWZWWW93TWFRRDcifQ=='
    useragent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'

    xNftCheckbotSitekey = request.headers['x-nft-checkbot-sitekey']
    xNftCheckbotToken = request.headers['x-nft-checkbot-token']
    xTraceId = request.headers['x-trace-id']
    xUiRequestTrace = request.headers['x-ui-request-trace']

    headers = {
        'Host': 'www.binance.com',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'clienttype': 'web',
        'x-nft-checkbot-token': xNftCheckbotToken,
        'x-nft-checkbot-sitekey': xNftCheckbotSitekey,
        'x-trace-id': xTraceId,
        'x-ui-request-trace': xUiRequestTrace,
        'content-type': 'application/json',
        'cookie': cookies,
        'csrftoken': csrftoken,
        'device-info': deviceinfo,
        'user-agent': useragent
    }
    return headers


def check_exists_by_xpath(path):
    try:
        driver.find_element(By.XPATH, path)
    except NoSuchElementException:
        return False
    return True


def get_tasks(session, url):
    tasks = []
    for i in range(requestsNumber):
        tasks.append(asyncio.create_task(session.post(url, data=json.dumps(js), ssl=False)))
    return tasks


async def get_symbols(headers):
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = get_tasks(session, 'https://www.binance.com/bapi/nft/v1/private/nft/mystery-box/purchase')
        responses = await asyncio.gather(*tasks)
        for response in responses:
            results.append(await response.text())


def start_session(headers):
    asyncio.get_event_loop().run_until_complete(get_symbols(headers))


driver = webdriver.Chrome()
driver.get("https://accounts.binance.com/ru/login")
a = input('Залогинтесь и нажмите Enter: ')
sale_page()

results = []
while True:
    ts = time.time()
    if saleTime > ts:
        print(f'{saleTime - ts} - секунд до дропа')
    if saleTime < ts:
        req_headers = click_confirm()
        print('Начало отправки запросов...')
        rqStart = time.time()
        start_session(req_headers)
        rqStop = time.time()
        print('Конец отправки запросов...')
        break

print('Проверка результата...')
success = False
for r in results:
    if r.find('success:true') != -1:
        success = True
        print(r)
        break

if success:
    print('Удалось :)')
else:
    print('Не удалось :(')

print(f'{rqStop - rqStart}')
driver.quit()
