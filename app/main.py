import os
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

from .webdriver import download_driver, copy_drivers
from .webdriver.undetected_chromedriver import (get_undetected_chromedriver, grp)

logger.remove(0)
logger.add("loguru.log")

CHROME_REGEX = r'Chrome/[^ ]+'

cwd = os.getcwd()

patched_drivers = os.path.join(cwd, 'patched_drivers')
viewports = [
    '2560,1440', '1920,1080', '1440,900',
    '1536,864', '1366,768', '1280,1024', '1024,768'
]

PAGE_URL = "https://online.warrington.gov.uk/planning/index.html?fa=getApplication&id=211349"
TWO_CAPTCHA_API_KEY = "your_api_key"


class Bcolors:
    HEADER = '\033[95m'
    OK_BLUE = '\033[94m'
    OK_CYAN = '\033[96m'
    OK_GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_colored(
        text: str,
        start_color: str,
        end_color: Optional[str] = Bcolors.ENDC,
        end: Optional[str] = '\n'
):
    print('%s%s%s' % (start_color, text, end_color), end=end)


def input_colored(text: str, start_color: Bcolors, end_color: Optional[Bcolors] = Bcolors.ENDC):
    return input("%s%s%s" % (start_color, text, end_color))


def solve_2_captcha(driver):
    sleep(2)
    driver.find_element(By.ID, "amzn-captcha-verify-button").click()
    goku_props = driver.execute_script("return window.gokuProps ")
    print(goku_props, type(goku_props))

    solver = TwoCaptcha(TWO_CAPTCHA_API_KEY)
    script_elements = driver.find_elements(By.XPATH, '//script')
    while True:

        result = solver.amazon_waf(
            sitekey=goku_props.get("key"),
            iv=goku_props.get('iv'),
            context=goku_props.get('context'),
            url=PAGE_URL,
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


def main_runner(helper: Helper, position: int):
    driver = None
    data_dir = None

    if helper.cancel_all:
        raise KeyboardInterrupt

    try:
        ua = UserAgent(browsers=['chrome'])
        agent = sorted(ua.data_browsers['chrome'], key=lambda a: grp(CHROME_REGEX, a))[-1]

        try:

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

            factor = int(helper.threads / (0.1 * helper.threads + 1))
            sleep_time = int((str(position)[-1])) * factor
            sleep(sleep_time)

            driver = get_undetected_chromedriver(
                headless=False,
                viewports=viewports,
                agent=agent,
                driver_executable_path=patched_driver,
                patcher_force_close=True,
                version_main=int(helper.major_version)
            )

            driver.get("https://online.warrington.gov.uk/planning/index.html?fa=getApplication&id=211349")

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

    except Exception as e:
        print(
            helper.timestamp() + Bcolors.FAIL +
            f"Worker {position} | Line : {e.__traceback__.tb_lineno} | {type(e).__name__} | {e.args[0] if e.args else ''}" + Bcolors.ENDC
        )


def run(helper: Helper):
    helper.threads = 1
    loop = 0

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
