import os
import re

from typing import Optional, List
from random import choice
from undetected_chromedriver import Chrome, ChromeOptions
from fake_useragent import UserAgent
from glob import glob

VIEWPORTS = [
    '2560,1440', '1920,1080', '1440,900',
    '1536,864', '1366,768', '1280,1024', '1024,768'
]

cwd = os.getcwd()

WEBRTC = os.path.join(cwd, 'extension', 'webrtc_control')
ACTIVE = os.path.join(cwd, 'extension', 'always_active')
FINGERPRINT = os.path.join(cwd, 'extension', 'fingerprint_defender')
CUSTOM_EXTENSIONS = glob(os.path.join('extension', 'custom_extension', '*.crx'))

CHROME_REGEX = r'Chrome/[^ ]+'


def grp(pat, txt):
    r = re.search(pat, txt)
    return r.group(0) if r else '&'


def create_proxy_folder(proxy, folder_name):
    proxy = proxy.replace('@', ':')
    proxy = proxy.split(':')
    manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
 """

    background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt("%s")
        },
        bypassList: ["localhost"]
        }
    };
chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}
chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (proxy[2], proxy[-1], proxy[0], proxy[1])

    os.makedirs(folder_name, exist_ok=True)
    with open(os.path.join(folder_name, "manifest.json"), 'w') as fh:
        fh.write(manifest_json)

    with open(os.path.join(folder_name, "background.js"), 'w') as fh:
        fh.write(background_js)


def get_undetected_chromedriver(
        headless: Optional[bool] = True,
        agent: Optional[str] = None,
        viewports: Optional[List[str]] = None,
        options: Optional[ChromeOptions] = None,
        driver_executable_path: Optional[str] = None,
        patcher_force_close: Optional[bool] = False,
        version_main: Optional[int] = None,
        is_incognito: Optional[bool] = False,

        auth_required: Optional[bool] = False,
        proxy: Optional[str] = None,
        proxy_type: Optional[str] = None,
        proxy_folder: Optional[str] = None,
):
    if agent is None:
        ua = UserAgent(browsers=['chrome'])
        agent = sorted(ua.data_browsers['chrome'], key=lambda a: grp(CHROME_REGEX, a))[-1]
        # agent = ua.chrome
    if options is None:
        options = ChromeOptions()
    if is_incognito:
        options.add_argument('--incognito')
    if viewports:
        options.add_argument(f"--window-size={choice(viewports)}")
    options.add_argument("--log-level=3")
    options.headless = headless

    prefs = {"intl.accept_languages": 'en_US,en',
             "credentials_enable_service": False,
             "profile.password_manager_enabled": False,
             "profile.default_content_setting_values.notifications": 2,
             "download_restrictions": 3}
    options.add_experimental_option("prefs", prefs)

    # options.add_experimental_option('extensionLoadTimeout', 120000)  # this giving error on "uc"

    options.add_argument(f"--user-agent={agent}")
    options.add_argument("--mute-audio")
    options.add_argument('--no-sandbox')
    # options.add_argument('--no-startup-window')  # to disable startup page
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-features=UserAgentClientHint')
    options.add_argument("--disable-web-security")
    # DesiredCapabilities.CHROME['loggingPrefs'] = {
    #     'driver': 'OFF', 'server': 'OFF', 'browser': 'OFF'
    # }
    extensions = []

    if not headless:
        extensions += [WEBRTC, FINGERPRINT, ACTIVE]

    if proxy:
        if auth_required:
            if not proxy_folder:
                proxy_folder = os.path.join(cwd, 'extension', f'proxy_auth')
            create_proxy_folder(proxy, proxy_folder)
            extensions.append(proxy_folder)
            # options.add_argument(f"--load-extension={proxy_folder}")
        else:
            options.add_argument(f'--proxy-server={proxy_type}://{proxy}')
    if extensions:
        options.add_argument(f"--load-extension={','.join(extensions)}")

    driver = Chrome(
        # service=service,
        options=options,
        driver_executable_path=driver_executable_path,
        patcher_force_close=patcher_force_close,
        version_main=version_main,
    )

    return driver
