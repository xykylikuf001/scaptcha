import os
from random import randint, choice

import psutil
import sys
import subprocess
import shutil
import json
from typing import Optional, List
from time import sleep
from requests.exceptions import RequestException
from urllib.parse import urlparse, parse_qs

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, wait

from fake_useragent import UserAgent
from undetected_chromedriver import Patcher
from loguru import logger
from twocaptcha import TwoCaptcha

from selenium.webdriver.support.ui import WebDriverWait  # To wait
from selenium.webdriver.support import expected_conditions as EC  # To wait
from selenium.webdriver.common.by import By  # To find the elements

from app import Bcolors, input_colored, print_colored
from app.conf.config import settings
from .webdriver import download_driver, copy_drivers
from .webdriver.undetected_chromedriver import (get_undetected_chromedriver, grp)
from .proxies import get_proxy_list, scrape_api, check_proxy

logger.remove(0)
logger.add("loguru.log")

CHROME_REGEX = r'Chrome/[^ ]+'

cwd = os.getcwd()

patched_drivers = os.path.join(cwd, 'patched_drivers')
viewports = [
    '2560,1440', '1920,1080', '1440,900',
    '1536,864', '1366,768', '1280,1024', '1024,768'
]


def solve_2_captcha(driver):
    sleep(2)
    driver.find_element(By.ID, "amzn-captcha-verify-button").click()
    goku_props = driver.execute_script("return window.gokuProps ")
    print(goku_props, type(goku_props))

    solver = TwoCaptcha(settings.TWO_CAPTCHA_API_KEY)
    script_elements = driver.find_elements(By.XPATH, '//script')
    while True:

        result = solver.amazon_waf(
            sitekey=goku_props.get("key"),
            iv=goku_props.get('iv'),
            context=goku_props.get('context'),
            url=settings.PAGE_URL,
            challenge_script=script_elements[1].get_attribute('src'),
            captcha_script=script_elements[2].get_attribute('src'),
        )
        print(result, type(result))

        if result in ['CAPCHA_NOT_READY', "ERROR_NO_SLOT_AVAILABLE"]:
            sleep(5)
            continue
        elif isinstance(result, dict):
            result = result.get('code')
            print(result, type(result))
            my_dict = json.loads(result)

            o = open(f'{cwd}/static/validate.js', 'r')
            body = o.read()
            driver.execute_script(body, my_dict.get('captcha_voucher'), my_dict.get("existing_token"))
            driver.set_script_timeout(120)
            sleep(1)
            # driver.find_element(By.ID, "amzn-btn-verify-internal").click()

            break
        else:
            raise Exception(f'TwoCaptcha response error: {result}')


class Helper:
    __slots__ = [
        'osname',
        'exe_name',
        "major_version",
        'constructor',
        'driver_dict',
        'temp_folders',
        'cpu_usage',
        "threads",
        "date_fmt",
        'futures',
        "cancel_all",
        "status",

        'proxy_list', 'bad_proxies', 'total_proxies', 'checked_proxies', 'proxies_from_api', 'used_proxies',
    ]
    futures: Optional[list]
    start_time: Optional[float]
    console: list
    temp_folders: List[str]
    cancel_all: bool
    status: Optional[int]
    auth_headers: dict

    def __init__(
            self,
            osname: str,
            exec_name: str,
            major_version: str,
    ):
        self.osname = osname

        self.exe_name = exec_name
        self.major_version = major_version
        if self.osname == 'win':
            import wmi
            self.constructor = wmi.WMI()
        self.date_fmt = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        self.driver_dict = {}
        self.temp_folders = []
        self.cpu_usage = str(psutil.cpu_percent(1))
        self.proxy_list = []
        self.bad_proxies = []
        self.used_proxies = []
        self.proxies_from_api = []
        self.checked_proxies = {}
        self.total_proxies = 0

        self.threads = 0
        self.cancel_all = False

    def set_status(self, value: int):
        self.status = value

    def set_futures(self, value: list):
        self.futures = value

    def timestamp(self):
        self.date_fmt = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        return Bcolors.OK_GREEN + f'[{self.date_fmt}] | ' + Bcolors.OK_CYAN + f'{self.cpu_usage} | '

    def windows_kill_drivers(self):
        for process in self.constructor.Win32_Process(["CommandLine", "ProcessId"]):
            try:
                if 'UserAgentClientHint' in process.CommandLine:
                    print(f'Killing PID : {process.ProcessId}', end="\r")
                    subprocess.Popen(
                        ['taskkill', '/F', '/PID', f'{process.ProcessId}'],
                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
                    )
            except Exception:
                pass
        print('\n')

    def quit_driver(self, driver, data_dir: Optional[str] = None):

        print_colored(
            'Quiting driver...',
            self.timestamp() + Bcolors.WARNING
        )
        if driver and driver in self.driver_dict:
            driver.quit()
            if data_dir and data_dir in self.temp_folders:
                self.temp_folders.remove(data_dir)

        print_colored(
            'Driver quited',
            self.timestamp() + Bcolors.OK_BLUE
        )
        proxy_folder = self.driver_dict.pop(driver, None)
        if proxy_folder:
            shutil.rmtree(proxy_folder, ignore_errors=True)

        # self.set_status(400)
        # return self.status

    def clean_exit(self):
        print_colored(
            'Cleaning up processes...',
            self.timestamp() + Bcolors.WARNING
        )

        if self.osname == 'win':
            print_colored(
                'Cleaning windows os...',
                self.timestamp() + Bcolors.WARNING
            )

            for driver in list(self.driver_dict):
                self.quit_driver(driver=driver, data_dir=None)
            self.driver_dict.clear()
            self.windows_kill_drivers()
        else:
            print_colored(
                f'Cleaning {self.osname} os...',
                self.timestamp() + Bcolors.WARNING
            )
            for driver in list(self.driver_dict):
                self.quit_driver(driver=driver, data_dir=None)
        for folder in self.temp_folders:
            shutil.rmtree(folder, ignore_errors=True)

    def stop_server(self, immediate: Optional[bool] = False):
        if not immediate:
            print('Allowing a maximum of 15 minutes to finish all the running drivers...')
            for _ in range(180):
                sleep(5)
                if 'state=running' not in str(self.futures[1:-1]):
                    break

        # if self.enable_api and self.server:
        #     loop = asyncio.get_event_loop()
        #     loop.run_until_complete(self.server.shutdown())
        #     loop.close()

        # for _ in range(10):
        # response = requests.get(f'http://127.0.0.1:{self.config_info.http_api.http_port}/shutdown/')
        # if response.status_code == 200:
        #     print('Server shut down successfully!')
        #     break
        # else:
        #     print(f'Server shut down error : {response.status_code}')
        #     sleep(3)

    def cancel_pending_task(self, not_done: set):
        self.cancel_all = True
        for future in not_done:
            _ = future.cancel()

        self.clean_exit()

        print_colored(
            'Stopping server...',
            self.timestamp() + Bcolors.WARNING
        )
        self.stop_server(immediate=True)

        print_colored(
            'Server stopped',
            self.timestamp() + Bcolors.OK_BLUE
        )
        _ = wait(not_done, timeout=None)

        print_colored(
            'Reclean (drivers, temp folders)...',
            self.timestamp() + Bcolors.WARNING
        )
        self.clean_exit()

        print_colored(
            'Recleaned (drivers, temp folders)',
            self.timestamp() + Bcolors.OK_BLUE
        )

    def set_proxy_list(self, value: List[str]):
        self.proxy_list = value
        self.total_proxies = len(value)

    def set_proxies_from_api(self, value: list):
        self.proxies_from_api = value


def main_runner(
        helper: Helper,  proxy_type: str, proxy: str, position: int,
        refresh_link: Optional[str] = None
):
    driver = None
    data_dir = None

    if helper.cancel_all:
        raise KeyboardInterrupt

    try:
        ua = UserAgent(browsers=['chrome'])
        agent = sorted(ua.data_browsers['chrome'], key=lambda a: grp(CHROME_REGEX, a))[-1]
        helper.checked_proxies[position] = None

        if settings.PROXY_CATEGORY == 'r' and settings.PROXY_API:
            for _ in range(20):
                proxy = choice(helper.proxies_from_api)
                if proxy not in helper.used_proxies:
                    break
            helper.used_proxies.append(proxy)
        helper.status = check_proxy(settings.CATEGORY, agent, proxy, proxy_type)

        if helper.status != 200:
            raise RequestException(helper.status)

        try:
            print(
                helper.timestamp() + Bcolors.OK_BLUE + f"Worker {position} | " + Bcolors.OK_GREEN +
                f"{proxy} | {proxy_type.upper()} | Good Proxy | Opening a new driver..." + Bcolors.ENDC
            )

            while proxy in helper.bad_proxies:
                helper.bad_proxies.remove(proxy)
                sleep(1)

            patched_driver = os.path.join(
                patched_drivers, f'chromedriver_{position % helper.threads}{helper.exe_name}'
            )

            try:
                Patcher(executable_path=patched_driver).patch_exe()
            except Exception as e:
                print_colored(
                    f"Worker {position} | Line : {e.__traceback__.tb_lineno} |"
                    f" {type(e).__name__} | {e.args[0] if e.args else ''}",
                    helper.timestamp() + Bcolors.FAIL
                )


            proxy_folder = os.path.join(
                cwd, 'extension', f'proxy_auth_{position}'
            )

            factor = int(helper.threads / (0.1 * helper.threads + 1))
            sleep_time = int((str(position)[-1])) * factor
            sleep(sleep_time)

            if helper.cancel_all:
                raise KeyboardInterrupt

            print(
                helper.timestamp() + Bcolors.OK_BLUE + f"Worker {position} | " + Bcolors.OK_GREEN +
                f"{proxy} | {proxy_type.upper()} | Good Proxy | Creating new driver..." + Bcolors.ENDC
            )

            if refresh_link:
                refresh_driver = get_undetected_chromedriver(
                    headless=True,
                    driver_executable_path=patched_driver,
                    version_main=int(helper.major_version),
                )
                refresh_driver.get(refresh_link)
                sleep(5)
                # is_success = check_element_exists(
                #     driver=refresh_driver,
                #     find_by=By.XPATH,
                #     element="//body[contains(text(), 'OK')]",
                #     timeout=1
                # )
                refresh_driver.quit()
                # if not is_success:
                #     raise Exception("Can not refresh mobile proxy api")

            driver = get_undetected_chromedriver(
                headless=False,
                viewports=viewports,
                agent=agent,
                driver_executable_path=patched_driver,
                patcher_force_close=True,
                version_main=int(helper.major_version)
            )

            driver.get(settings.PAGE_URL)

            driver.maximize_window()

            solve_2_captcha(driver=driver)
            sleep(15)
            helper.quit_driver(driver=driver, data_dir=data_dir)

            if helper.cancel_all:
                raise KeyboardInterrupt

        except Exception as e:
            logger.add('exp.log')
            logger.exception('Something went wrong')
            helper.quit_driver(driver=driver, data_dir=data_dir)
            print_colored(
                f"Worker {position} | Line : {e.__traceback__.tb_lineno} | {type(e).__name__} | {e.args[0] if e.args else ''}",
                helper.timestamp() + Bcolors.FAIL
            )
    except RequestException:
        print(helper.timestamp() + Bcolors.OK_BLUE + f"Worker {position} | " +
              Bcolors.FAIL + f"{proxy} | {proxy_type.upper()} | Bad proxy " + Bcolors.ENDC)
        helper.checked_proxies[position] = proxy_type
        helper.bad_proxies.append(proxy)

    except Exception as e:
        print(
            helper.timestamp() + Bcolors.FAIL +
            f"Worker {position} | Line : {e.__traceback__.tb_lineno} | {type(e).__name__} | {e.args[0] if e.args else ''}" + Bcolors.ENDC
        )


def prepare_run(helper: Helper):
    try:
        sleep(2)
        proxy = choice(helper.proxy_list)
        proxy_index = helper.proxy_list.index(proxy)
        proxy_type = settings.PROXY_TYPE
        refresh_link = None
        if '|' in proxy:
            splitted = proxy.split('|')
            if 'http://' in splitted[-1] or 'https://' in splitted[-1]:
                splitted_proxy_type = splitted[-2]
                refresh_link = splitted[-1]
            else:
                splitted_proxy_type = splitted[-1]
            if not proxy_type:
                proxy_type = splitted_proxy_type
            main_runner(helper, proxy_type, splitted[0], proxy_index, refresh_link)
        elif proxy_type:
            main_runner(helper, proxy_type, proxy, proxy_index)
        else:
            main_runner(helper, 'http', proxy, proxy_index)
            if helper.checked_proxies[proxy_index] == 'http':
                main_runner(helper, 'socks4', proxy, proxy_index)
            if helper.checked_proxies[proxy_index] == 'socks4':
                main_runner(helper, 'socks5', proxy, proxy_index)

    except Exception as e:
        print(
            helper.timestamp() + Bcolors.FAIL +
            f"Line :{e.__traceback__.tb_lineno} | {type(e).__name__} | {e.args[0] if e.args else ''}" + Bcolors.ENDC
        )


def run(helper: Helper):
    helper.threads = 1
    loop = 0

    proxy_list = get_proxy_list(
        filename=settings.PROXY_FILENAME,
        is_rotating=settings.PROXY_CATEGORY == 'r',
        max_threads=settings.MAX_THREADS,
        proxy_api=settings.PROXY_API,
    )

    proxy_list = [x for x in proxy_list if x not in helper.bad_proxies]
    helper.set_proxy_list(proxy_list)

    if len(proxy_list) == 0:
        helper.bad_proxies.clear()
        get_proxy_list(
            filename=settings.PROXY_FILENAME,
            is_rotating=settings.PROXY_CATEGORY == 'r',
            max_threads=settings.MAX_THREADS,
            proxy_api=settings.PROXY_API,
        )
        helper.set_proxy_list(proxy_list)
    if proxy_list[0] != 'dummy':
        helper.proxy_list.insert(0, 'dummy')
    if proxy_list[-1] != 'dummy':
        helper.proxy_list.append('dummy')

    if settings.PROXY_CATEGORY == 'r' and settings.PROXY_API:
        proxies_from_api = scrape_api(link=settings.PROXY_FILENAME)
        helper.set_proxies_from_api(proxies_from_api)

    helper.threads = randint(settings.MIN_THREADS, settings.MAX_THREADS)

    with ThreadPoolExecutor(max_workers=helper.threads) as executor:
        futures = [
            executor.submit(main_runner, helper, position)
            for position in range(helper.threads)
        ]

        helper.set_futures(futures)
        done, not_done = wait(helper.futures, timeout=0)

        try:
            while not_done:
                freshly_done, not_done = wait(not_done, timeout=1)
                done |= freshly_done

                loop += 1
                for _ in range(70):
                    cpu = str(psutil.cpu_percent(0.2))
                    helper.cpu_usage = cpu + '%' + ' ' * (5 - len(cpu)) if cpu != '0.0' else helper.cpu_usage

                if settings.PROXY_CATEGORY == 'r' and settings.PROXY_API:
                    proxies_from_api = scrape_api(link=settings.PROXY_FILENAME)
                    helper.set_proxies_from_api(proxies_from_api)

        except KeyboardInterrupt:
            print_colored(
                'Hold on!!! Allow me a moment to close all the running drivers.',
                helper.timestamp() + Bcolors.WARNING
            )

            helper.cancel_pending_task(not_done=not_done)
            raise KeyboardInterrupt
        except Exception as e:
            print(
                helper.timestamp() + Bcolors.FAIL +
                f"Line :{e.__traceback__.tb_lineno} | {type(e).__name__} | {e.args[0] if e.args else ''}" + Bcolors.ENDC
            )


def main():
    osname, exe_name, major_version = download_driver(patched_drivers=patched_drivers)

    if settings.PROXY_AUTH_REQUIRED and settings.HEADLESS:
        print_colored(
            "Premium proxy needs extension to work. Chrome doesn't support extension in Headless mode.",
            Bcolors.FAIL,
        )
        input_colored(
            "Either use proxy without username & password or disable headless mode ",
            Bcolors.WARNING
        )
        sys.exit()
    helper = Helper(
        osname=osname,
        exec_name=exe_name,
        major_version=major_version,

    )
    try:
        copy_drivers(patched_drivers=patched_drivers, exe=exe_name, total=1)
        run(helper=helper)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == "__main__":
    main()
