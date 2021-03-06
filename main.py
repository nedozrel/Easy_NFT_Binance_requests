import asyncio
import json
import time
import sys
import traceback

import aiohttp
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from seleniumwire import webdriver as wire_webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as chrome_options
import requests


def log_uncaught_exceptions(ex_cls, ex, tb):
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)
    text += ''.join(traceback.format_tb(tb))
    print(text)
    with open('data/error.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    input('Произошла фатальная ошибка, нажмите кнопку Enter или крестик для завершения работы.')
    sys.exit()


sys.excepthook = log_uncaught_exceptions


def get_proxy():
    try:
        with open('data/proxy.txt', 'r') as f:
            proxy = f.read()
        if proxy:
            return proxy
        else:
            return None
    except FileNotFoundError:
        return None


def get_seleniumwire_options(proxy):
    if proxy is not None:
        return {
            'proxy': {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
        }
    else:
        return None


def save_cookies(driver):
    with open('data/cookies.json', 'w') as file:
        json.dump(driver.get_cookies(), file)


def load_cookies(driver):
    try:
        with open('data/cookies.json', 'r') as cookies_file:
            cookies = json.load(cookies_file)
    except ValueError:
        with open('data/cookies.json', 'w') as cookies_file:
            cookies_file.write('{}')
        with open('data/cookies.json', 'r') as cookies_file:
            cookies = json.load(cookies_file)
    for cookie in cookies:
        driver.add_cookie(cookie)


def check_auth(driver, timeout=5):
    try:
        return WebDriverWait(driver=driver, timeout=timeout, poll_frequency=0.1).until(
            EC.any_of(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, '#__APP > div > header > div:nth-child(4) > div > svg > use')
                ),
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'svg.css-6px2js')
                )
            )
        )
    except TimeoutException:
        return False


def do_auth(driver):
    print('Ожидание авторизации...')
    driver.get('https://accounts.binance.com/ru/login')
    WebDriverWait(driver=driver, timeout=6000, poll_frequency=1) \
        .until(EC.any_of(EC.visibility_of_element_located((By.CSS_SELECTOR, '#__APP > div > header > div:nth-child(4) > div > svg > use')),
                         EC.visibility_of_element_located((By.CSS_SELECTOR, 'svg.css-6px2js'))))
    print('Авторизация прошла успешно!')
    save_cookies(driver)


def sale_page(driver):
    url = 'https://www.binance.com/ru/nft/balance?tab=nft'
    driver.get(url)

    # Выбор первого нфт в инвентаре на продажу
    try:
        first_nft_for_sale = WebDriverWait(driver=driver, timeout=10, poll_frequency=0.000000001).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="__APP"]/div/div[2]/main/div/div[2]/div/div[2]/div/div'
                           '/div/div[2]/div[2]/div/div/div/div[1]/div/div[1]/div/div'))
        )
        first_nft_for_sale.click()
    except TimeoutException:
        input('У вас нет НФТ в инвентаре, чтобы обойти капчу у вас должен быть хотя бы 1 НФТ!\n'
              'Нажмите Enter для завершения работы программы.')
        quit()

    # Нажатие на кнопку соглашения с условиями бинанса
    try:
        btn = WebDriverWait(driver=driver, timeout=10, poll_frequency=0.000000001).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.css-qzf033'))
        )
        time.sleep(2)
        btn.click()
    except TimeoutException:
        pass

    sell_btn = WebDriverWait(driver=driver, timeout=10, poll_frequency=0.000000001).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="__APP"]/div/div[2]/main/div/div'
                           '/div[2]/div/div[1]/div[5]/div/button[1]'))
        )
    sell_btn.click()

    cost_placeholder = WebDriverWait(driver=driver, timeout=60, poll_frequency=0.1).until(
        EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="__APP"]/div/div[2]/main/div/div/div[4]/div[2]/div/div[1]/input')
        )
    )
    input_cost = ActionChains(driver)
    input_cost.move_to_element(cost_placeholder)
    input_cost.click()
    input_cost.perform()
    input_cost.send_keys_to_element(cost_placeholder, 500)
    input_cost.perform()

    time.sleep(5)
    driver.find_element(By.CSS_SELECTOR, 'button.css-19xplxv').click()


def click_confirm(driver):
    confirm = WebDriverWait(driver=driver, timeout=100, poll_frequency=0.0000000000000000001).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'button.css-mh5cnv'))
    )
    ActionChains(driver).move_to_element(confirm).click().perform()
    print('Нажали confirm')

    request = driver.wait_for_request('https://www.binance.com/bapi/nft/v1/private/nft/nft-trade/product-onsale',
                                      timeout=60)

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


def check_exists_by_xpath(driver, path):
    try:
        driver.find_element(By.XPATH, path)
    except NoSuchElementException:
        return False
    return True


def send_purchase_requests(headers, requests_number, js, proxy):
    url = 'https://www.binance.com/bapi/nft/v1/private/nft/mystery-box/purchase'
    req_results = []

    async def start_session():
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = [
                asyncio.create_task(
                    session.post(url, data=json.dumps(js), ssl=False, proxy=proxy)
                ) for i in range(requests_number)
            ]
            responses = await asyncio.gather(*tasks)
            for response in responses:
                req_results.append(
                    await response.json() if response.content_type == 'application/json' else await response.text()
                )

    asyncio.get_event_loop_policy().get_event_loop().run_until_complete(start_session())
    return req_results


def get_result(results):
    success = False
    with open('data/requests_result.txt', 'w', encoding='utf-8') as f:
        for r in results:
            if type(r) == dict:
                if r.get('success'):
                    success = r.get('success')
            if len(r) > 250:
                print('blocked', file=f)
            else:
                print(r, file=f)
    return success


def main():
    product_id = int(input('Введите product id: '))
    sale_time = int(input('Введите время начала отправки запросов в формате unix: '))
    nft_amount = int(input('Введите количество NFT для покупки: '))
    requests_number = int(input('Введите количество запросов: '))
    js = {"number": nft_amount, "productId": product_id}
    proxy = get_proxy()
    seleniumwire_options = get_seleniumwire_options(proxy)
    proxy = f'http://{proxy}' if proxy is not None else None

    print('Загрузка браузера...')
    options = chrome_options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = wire_webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)
    driver.get("https://www.binance.com/")
    print('Проверка авторизации...')
    load_cookies(driver)
    driver.refresh()
    authenticated = check_auth(driver, timeout=10)
    print('Вы авторизованы!' if authenticated else 'Вы не авторизованы!')
    if not authenticated:
        driver.delete_all_cookies()
        do_auth(driver)
        load_cookies(driver)
        driver.refresh()
    sale_page(driver)
    print('Ожидание дропа...')
    confirm_clicked = False
    req_headers = {}
    while True:
        ts = time.time()
        if not confirm_clicked and sale_time - ts < 13:
            req_headers = click_confirm(driver)
            confirm_clicked = True
        if sale_time < ts:
            print('Начало отправки запросов...')
            results = send_purchase_requests(req_headers, requests_number, js, proxy)
            print('Конец отправки запросов...')
            break

    print('Проверка результата...')
    success = get_result(results)
    print('Удалось :)' if success else 'Не удалось :(')
    input('Нажмите Enter для завершения работы.')


if __name__ == '__main__':
    with open('data/personal_key.txt', 'r') as file:
        key = file.read()
    if key:
        req = requests.get(f'https://snkrs.na4u.ru/{key.strip()}:binance_nft_bot')
        if req.text == 'yes':
            main()
        else:
            input('Проверьте правильность введеного ключа!')
    else:
        input('Добавьте персональный ключ доступа в personal_key.txt в папке data и перезапустите программу.')
