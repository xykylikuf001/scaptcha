import os
import platform
import subprocess
import shutil
import sys
import zipfile

from typing import Literal, Optional, Tuple, List, TYPE_CHECKING
from urllib.request import urlretrieve, urlopen
from packaging.version import Version

from loguru import logger

from .undetected_chromedriver import get_undetected_chromedriver

if TYPE_CHECKING:
    from undetected_chromedriver import ChromeOptions as UCChromeOptions

__all__ = [
    "get_driver", "download_driver", "copy_drivers"
]

cwd = os.getcwd()

CHROME = [
    '{8A69D345-D564-463c-AFF1-A69D9E530F96}',
    '{8237E44A-0054-442C-B6B6-EA0509993955}',
    '{401C381F-E0DE-4B85-8BD8-3F3F14FBDA57}',
    '{4ea16ac7-fd5a-47c3-875b-dbf4a2008c20}'
]

CHROME_DRIVER_URL_REPO = "https://chromedriver.storage.googleapis.com"
CHROME_LABS_URL_REPO = "https://googlechromelabs.github.io/chrome-for-testing"

# https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/linux64/chromedriver-linux64.zip
# https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/mac-x64/chromedriver-mac-x64.zip
# https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/win64/chromedriver-win64.zip
CHROME_EDGE_URL_REPO = "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing"


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


def get_driver(

        headless: Optional[bool] = True,
        agent: Optional[str] = None,
        viewports: Optional[List[str]] = None,
        options: Optional["UCChromeOptions"] = None,
        driver_executable_path: Optional[str] = None,

        auth_required: Optional[bool] = False,
        proxy: Optional[str] = None,
        proxy_type: Optional[str] = None,
        proxy_folder: Optional[str] = None,

):
    return get_undetected_chromedriver(
        headless=headless,
        viewports=viewports,
        agent=agent,
        driver_executable_path=driver_executable_path,
        patcher_force_close=True,
        options=options,
        proxy=proxy,
        auth_required=auth_required,
        proxy_type=proxy_type,
        proxy_folder=proxy_folder,
    )


def download_driver(
        patched_drivers: str, driver: Optional[Literal["chromedriver"]] = "chromedriver"
) -> Tuple[str, str, str]:
    if driver == "chromedriver":
        return __download_chrome_driver(patched_drivers)
    raise Exception("Invalid driver option")


def __download_chrome_driver(
        patched_drivers: str,
        repo: Optional[Literal['chrome_labs', 'chrome_driver']] = 'chrome_labs'
) -> Tuple[str, str, str]:
    osname = platform.system()
    if repo == 'chrome_driver':
        repo_url = CHROME_DRIVER_URL_REPO
        zip_name = 'chromedriver_%s.zip'

    else:
        zip_name = 'chromedriver-%s.zip'

        repo_url = CHROME_LABS_URL_REPO
    print(Bcolors.WARNING + 'Getting Chrome Driver...' + Bcolors.ENDC)

    if osname == 'Linux':
        osname = 'lin'
        exe_name = ""
        with subprocess.Popen(['google-chrome-stable', '--version'], stdout=subprocess.PIPE) as proc:
            version = proc.stdout.read().decode('utf-8').replace('Google Chrome', '').strip()
    elif osname == 'Darwin':
        osname = 'mac'
        exe_name = ""
        process = subprocess.Popen(
            ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'], stdout=subprocess.PIPE)
        version = process.communicate()[0].decode('UTF-8').replace('Google Chrome', '').strip()
    elif osname == 'Windows':
        osname = 'win'
        exe_name = ".exe"
        version = None
        try:
            process = subprocess.Popen(
                ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
            )
            version = process.communicate()[0].decode('UTF-8').strip().split()[-1]
        except Exception:
            for i in CHROME:
                for j in ['opv', 'pv']:
                    try:
                        command = [
                            'reg', 'query', f'HKEY_LOCAL_MACHINE\\Software\\Google\\Update\\Clients\\{i}', '/v', f'{j}',
                            '/reg:32'
                        ]
                        process = subprocess.Popen(
                            command,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
                        )
                        version = process.communicate()[0].decode(
                            'UTF-8').strip().split()[-1]
                    except Exception:
                        pass

        if not version:
            print(
                Bcolors.WARNING +
                "Couldn't find your Google Chrome version automatically!" + Bcolors.ENDC
            )
            version = input(
                Bcolors.WARNING +
                'Please input your google chrome version (ex: 91.0.4472.114) : ' + Bcolors.ENDC
            )
    else:
        input('{} OS is not supported.'.format(osname))
        sys.exit()

    try:
        with open('version.txt', 'r') as f:
            previous_version = f.read()
    except Exception:
        previous_version = '0'

    with open('version.txt', 'w') as f:
        f.write(version)

    if version != previous_version:
        try:
            os.remove(f'chromedriver{exe_name}')
        except Exception:
            pass

        shutil.rmtree(patched_drivers, ignore_errors=True)

    major_version = version.split('.')[0]

    base = 'chromedriver{}'
    if not os.path.exists(base.format(exe_name)):
        path = f"/latest_release_{major_version}"
        path = path.upper()
        logger.debug("getting release number from %s" % path)
        release = Version(urlopen(repo_url + path).read().decode())
        version_full = release

        platform_sm = sys.platform

        if platform_sm.endswith("win32"):
            platform_category = "win32"
        elif platform_sm.endswith("win64"):
            platform_category = "win64"
        elif platform_sm.endswith(("linux", "linux2")):
            platform_category = "linux64"
        elif platform_sm.endswith("darwin"):
            platform_machine = platform.machine()
            if repo == "chrome_driver":
                if platform_machine == "x86_64":
                    platform_category = "mac64"
                else:
                    platform_category = "mac_arm64"
            else:
                if platform_machine == "x86_64":
                    platform_category = "mac-x64"
                else:
                    platform_category = "mac-arm64"

        else:
            raise Exception("Unsupported system os")
        zip_name %= platform_category

        if repo == "chrome_driver":
            u = "%s/%s/%s" % (CHROME_DRIVER_URL_REPO, version_full.base_version, zip_name)
        else:
            u = "%s/%s/%s/%s" % (CHROME_EDGE_URL_REPO, version_full.base_version, platform_category, zip_name)
        print(Bcolors.OK_CYAN + f'Chrome downloading version: {version_full.base_version}' + Bcolors.ENDC)
        print(Bcolors.OK_CYAN + f'Chrome driver url: {u}' + Bcolors.ENDC)

        urlretrieve(u, filename=zip_name)
        with zipfile.ZipFile(zip_name) as zf:
            if repo == "chrome_driver":
                zf.extract(base.format(exe_name))
            else:
                base_dir = f"{cwd}/{zip_name.replace('.zip', '')}"
                zf.extract(f"{zip_name.replace('.zip', '')}/{base.format(exe_name)}", cwd)
                shutil.move(
                    f"{base_dir}/{base.format(exe_name)}",
                    f"{cwd}/{base.format(exe_name)}"
                )
                shutil.rmtree(base_dir)

        os.remove(zip_name)
        if sys.platform != "win32":
            os.chmod(base.format(exe_name), 0o755)
    else:
        print('Chromedriver already exists')
    return osname, exe_name, major_version


def copy_drivers(patched_drivers: str, exe: str, total: int, driver_name: Optional[str] = "chromedriver"):
    current = os.path.join(cwd, f'{driver_name}{exe}')
    os.makedirs(patched_drivers, exist_ok=True)
    for i in range(total + 1):
        try:
            destination = os.path.join(
                patched_drivers, f'{driver_name}_{i}{exe}'
            )
            shutil.copy(current, destination)
        except Exception:
            pass
