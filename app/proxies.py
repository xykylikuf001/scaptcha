import sys
import os
import requests
import shutil
import re

from random import shuffle
from typing import List, Optional
from glob import glob
from concurrent.futures import ThreadPoolExecutor, wait
from fake_useragent import UserAgent
from time import sleep

from app import Bcolors, print_colored, input_colored

os.system("")

checked = {}
cancel_all = False
CHROME_REGEX = r'Chrome/[^ ]+'


def grp(pat, txt):
    r = re.search(pat, txt)
    return r.group(0) if r else '&'


def gather_proxy():
    proxies = []
    print_colored(
        'Scraping proxies ...',
        Bcolors.OK_GREEN
    )

    link_list = [
        'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
        'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
        'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt',
        'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt',
        'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/proxy.txt',
        'https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt'
    ]

    for link in link_list:
        response = requests.get(link)
        output = response.content.decode()

        if '\r\n' in output:
            proxy = output.split('\r\n')
        else:
            proxy = output.split('\n')

        for lines in proxy:
            for line in lines.split('\n'):
                proxies.append(line)

        print(
            Bcolors.BOLD + f'{len(proxy)}' + Bcolors.OK_BLUE +
            ' proxies gathered from ' + Bcolors.OK_CYAN + f'{link}' + Bcolors.ENDC
        )

    proxies = list(set(filter(None, proxies)))
    shuffle(proxies)

    return proxies


def _shuffle_proxies(proxy_list: List[str], is_shuffled: Optional[bool] = True):
    # proxies = []
    # for lines in proxy_list:
    #     if lines.count(':') == 4 and "|" in lines:
    #         splitted = lines.split('|')
    #         print(splitted)
    #         if len(splitted) == 3:
    #             lines = splitted[0]
    #         if lines.count(':') == 3:
    #             split = lines.split(':')
    #             lines = f'{split[2]}:{split[-1]}@{split[0]}:{split[1]}|{splitted[-1]}{splitted[-2]}'
    #     elif lines.count(':') == 3 and ("http://" not in lines and "https://" in lines):
    #         split = lines.split(':')
    #         lines = f'{split[2]}:{split[-1]}@{split[0]}:{split[1]}'
    #     proxies.append(lines)

    proxies = list(filter(None, proxy_list))
    if is_shuffled:
        shuffle(proxies)

    return proxies


def load_proxy(filename: str, is_shuffled: Optional[bool] = True):
    if not os.path.isfile(filename) and filename[-4:] != '.txt':
        filename = f'{filename}.txt'
    try:
        with open(filename, encoding="utf-8") as fh:
            loaded = [x.strip() for x in fh if x.strip() != '']
            fh.close()
    except Exception as e:
        print_colored(str(e), Bcolors.FAIL)
        input('')
        sys.exit()
    return _shuffle_proxies(loaded, is_shuffled)


def scrape_api(link: str):
    try:
        response = requests.get(link)
        output = response.content.decode()
    except Exception as e:
        print_colored(str(e), Bcolors.FAIL)
        input('')
        sys.exit()

    if '\r\n' in output:
        proxy_list = output.split('\r\n')
    else:
        proxy_list = output.split('\n')

    return _shuffle_proxies(proxy_list)


def check_proxy(category, agent, proxy, proxy_type):
    if category == 'f':
        headers = {
            'User-Agent': f'{agent}',
        }

        proxy_dict = {
            "http": f"{proxy_type}://{proxy}",
            "https": f"{proxy_type}://{proxy}",
        }
        response = requests.get(
            'https://visa.vfsglobal.com/tur/en/pol/login',
            headers=headers,
            proxies=proxy_dict,
            timeout=30,
        )
        status = response.status_code

    else:
        status = 200

    return status


def backup():
    try:
        shutil.copy('GoodProxy.txt', 'ProxyBackup.txt')
        print_colored(
            'GoodProxy.txt backed up in ProxyBackup.txt',
            Bcolors.WARNING
        )
    except Exception:
        pass

    print('', file=open('GoodProxy.txt', 'w'))


def clean_exe_temp(folder):
    try:
        temp_name = sys._MEIPASS.split('\\')[-1]
    except Exception:
        temp_name = None

    for f in glob(os.path.join('temp', folder, '*')):
        if temp_name not in f:
            shutil.rmtree(f, ignore_errors=True)


def get_proxy_list(
        is_rotating: Optional[bool] = False,
        filename: Optional[str] = 'files/proxies.txt',
        max_threads: Optional[int] = 5,
        proxy_api: Optional[bool] = False
):
    if filename:
        if is_rotating:
            factor = max_threads if max_threads > 1000 else 1000
            proxy_list = [filename] * factor
        else:
            if proxy_api:
                proxy_list = scrape_api(filename)
            else:
                proxy_list = load_proxy(filename)
    else:
        proxy_list = gather_proxy()

    return proxy_list


##########################
#########################
#########################

def main_checker(proxy_type: str, proxy: str, position: int):
    if cancel_all:
        raise KeyboardInterrupt

    checked[position] = None

    try:
        proxy_dict = {
            "http": f"{proxy_type}://{proxy}",
            "https": f"{proxy_type}://{proxy}",
        }
        ua = UserAgent(browsers=['chrome'])
        agent = sorted(ua.data_browsers['chrome'], key=lambda a: grp(CHROME_REGEX, a))[-1]

        headers = {
            'User-Agent': f'{agent}',
        }

        response = requests.get(
            'https://www.youtube.com/',
            headers=headers, proxies=proxy_dict, timeout=30,
        )
        status = response.status_code

        if status != 200:
            raise Exception(status)

        print(
            Bcolors.OK_BLUE + f"Worker {position + 1} | " + Bcolors.OK_GREEN +
            f'{proxy} | GOOD | Type : {proxy_type} | Response : {status}' + Bcolors.ENDC
        )

        print(f'{proxy}|{proxy_type}', file=open('GoodProxy.txt', 'a'))

    except Exception as e:
        try:
            e = int(e.args[0])
        except Exception:
            e = ''
        print(
            Bcolors.OK_BLUE + f"Worker {position + 1} | " + Bcolors.FAIL +
            f'{proxy} | {proxy_type} | BAD | {e}' + Bcolors.ENDC
        )
        checked[position] = proxy_type


def proxy_check(position: int):
    sleep(2)
    proxy = proxy_list_global[position]

    if '|' in proxy:
        splitted = proxy.split('|')
        main_checker(splitted[-1], splitted[0], position)
    else:
        main_checker('http', proxy, position)
        if checked[position] == 'http':
            main_checker('socks4', proxy, position)
        if checked[position] == 'socks4':
            main_checker('socks5', proxy, position)


def main():
    global cancel_all
    cancel_all = False
    pool_number = [i for i in range(total_proxies)]

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(proxy_check, position)
            for position in pool_number
        ]
        done, not_done = wait(futures, timeout=0)
        try:
            while not_done:
                freshly_done, not_done = wait(not_done, timeout=5)
                done |= freshly_done
        except KeyboardInterrupt:
            print_colored(
                'Hold on!!! Allow me a moment to finish the running threads',
                Bcolors.WARNING
            )
            cancel_all = True
            for future in not_done:
                _ = future.cancel()
            _ = wait(not_done, timeout=None)
            raise KeyboardInterrupt
        except IndexError:
            print_colored(
                'Number of proxies are less than threads. Provide more proxies or less threads. ',
                Bcolors.WARNING
            )


if __name__ == '__main__':
    clean_exe_temp(folder='proxy_check')
    backup()

    threads = 100
    proxy_filename = 'files/proxies.txt'
    input_filename = str(
        input_colored(
            f'Provide proxy filename path: (default={proxy_filename}',
            Bcolors.OK_CYAN,
        )
    )
    proxy_list_global = load_proxy(input_filename if input_filename else proxy_filename)
    # removing empty & duplicate proxies
    proxy_list_global = list(set(filter(None, proxy_list_global)))

    total_proxies = len(proxy_list_global)
    print_colored(
        f'Total unique proxies : {total_proxies}',
        Bcolors.OK_CYAN
    )

    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
