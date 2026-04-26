import pytest
import os
from appium import webdriver
from appium.options.common import AppiumOptions
from selenium.webdriver.support.abstract_event_listener import AbstractEventListener
from selenium.webdriver.support.event_firing_webdriver import EventFiringWebDriver
from selenium.common.exceptions import UnknownMethodException

SERVER = 'http://localhost:4723'
PROJECT_ROOT = str(os.path.dirname(os.path.abspath(__file__)))
CAPABILITIES = {
    'platformName': 'Android',
    'automationName': 'uiautomator2',
    # 'deviceName': 'Pixel_9_API_36_1_extension_level_7_x86_64',
    # 'appium:app': os.path.join(PROJECT_ROOT, 'pnv.apk')
}
GET_REPORT = 'getReport'
DELETE_REPORT = 'deleteReport'
SET_TEST_INFO = 'setTestInfo'


@pytest.fixture(scope='session')
def check_env():
    java_home = os.getenv('JAVA_HOME')
    if not java_home:
        os.environ['JAVA_HOME'] = java_home = r'C:\Program files\java\jdk-26'
    print('JAVA_HOME:', java_home)


class MyListener(AbstractEventListener):
    def before_find(self, by, value, driver) -> None:
        print(f'Finding {by} {value}')
        super().before_find(by, value, driver)

    def before_click(self, element, driver) -> None:
        print(f'Click on {element}')


class LoggedDriver:
    _driver: WebDriver
    report_file: str = 'report.html'

    def __init__(self, appium_driver: WebDriver) -> None:
        appium_driver.command_executor._commands = {
            **appium_driver.command_executor._commands,
            GET_REPORT: ("GET", "/getReport"),
            DELETE_REPORT: ("DELETE", "/deleteReportData"),
            SET_TEST_INFO: ("POST", "/setTestInfo"),
        }
        # driver = EventFiringWebDriver(appium_driver, MyListener())
        # self._driver = driver
        self._driver = appium_driver

    @property
    def driver(self):
        return self._driver

    def __enter__(self):
        try:
            self._driver.execute(DELETE_REPORT)
        except UnknownMethodException as e:
            pytest.fail(f'Ошибка вызова метода {DELETE_REPORT!r}. Проверьте, что установлен плагин: appium plugin install --source=npm appium-reporter-plugin')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        driver = self._driver
        driver.execute(SET_TEST_INFO,
                   {"sessionId": driver.session_id, "testName": 'test_one', "testStatus": test_status})
        html = driver.execute(GET_REPORT)
        reports_folder = os.path.join(PROJECT_ROOT, 'reports')
        os.makedirs(reports_folder, exist_ok=True)
        file_name = os.path.join(reports_folder, self.report_file)
        with open(file_name, "wt") as r:
            r.write(html['value'])
            print(f'Report file saved to {file_name}')
        driver.quit()


@pytest.fixture(scope='session')
def driver(check_env, request):
    param = request.param if hasattr(request, 'param') else ''
    options = AppiumOptions()
    options.load_capabilities(CAPABILITIES)

    driver = webdriver.Remote(SERVER, options=options)
    if param == 'logged':
        with LoggedDriver(driver) as logged_driver:
            ts = datetime.now().strftime('%Y-%m-%d_%H-%M')
            logged_driver.report_file = f'report_{ts}.html'
            yield logged_driver.driver
    else:
        yield driver

    try:
        driver.quit()
    except:
        pass