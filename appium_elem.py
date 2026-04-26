import allure
import os
import pytest
from appium.webdriver.extensions.android.nativekey import AndroidKey
from appium.webdriver.webdriver import WebDriver
from conftest import PROJECT_ROOT
from datetime import datetime
from random import randint
from selenium.common import WebDriverException
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from time import sleep

driver: WebDriver | None = None
SCREENSHOT_FOLDER = str(os.path.join(PROJECT_ROOT, 'screenshots'))
ts = datetime.now().strftime('%Y-%m-%d_%H-%M')


def swipe_and_hold(start_x, start_y, end_x, end_y, duration=1.0):
    """Прокрутка экрана и удержание курсора, чтобы избежать прокрутки по инерции"""
    if not isinstance(driver, WebDriver):
        pytest.fail('Ошибка скроллинга: не указан драйвер')
    actions = ActionChains(driver)
    # Define a finger (pointer) input
    finger = PointerInput(interaction.POINTER_TOUCH, "finger")
    actions.w3c_actions = ActionBuilder(driver, mouse=finger)

    # 1. Move to the start position and press down
    actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
    actions.w3c_actions.pointer_action.pointer_down()

    # 2. Move to the end position (the swipe)
    actions.w3c_actions.pointer_action.move_to_location(end_x, end_y)

    # 3. Hold at the end position for the specified duration
    actions.w3c_actions.pointer_action.pause(duration)

    # 4. Release the finger
    actions.w3c_actions.pointer_action.pointer_up()

    # Execute the sequence
    actions.perform()


class AppiumElement:
    driver: WebDriver
    locator: tuple

    def screenshot(self):
        driver = self.driver
        path = str(os.path.join(SCREENSHOT_FOLDER, ts))
        os.makedirs(path, exist_ok=True)
        now = datetime.now().strftime('%H-%M-%S') + f'_{randint(10, 9999)}'
        name = os.path.join(path, f'screenshot_{now}.png')

        try:
            allure.attach(
                driver.get_screenshot_as_png(),
                name=name,
                attachment_type=allure.attachment_type.PNG,
            )
        except WebDriverException as e:
            allure.attach(
                str(e),
                name=f'Ошибка создания скриншота: {name}',
                attachment_type=allure.attachment_type.TEXT,
            )

    def __init__(self, *locator, webdriver: WebDriver | None = driver):
        global driver
        if isinstance(webdriver, WebDriver):
            self.driver = driver = webdriver
        elif driver:
            self.driver = driver
        if len(locator) == 1:
            loc1 = locator[0]
            locator = (By.XPATH if loc1[:2] == '//' else By.ID, loc1)
        self.locator = locator or None

    def find(self):
        """Поиск элемента по локатору"""
        try:
            return self.driver.find_element(*self.locator)
        except WebDriverException:
            return None

    def find_all(self):
        """Поиск всех элементов по локатору"""
        return self.driver.find_elements(*self.locator)

    @property
    def text(self):
        """Выдача текста на элементе"""
        if elem := self.find():
            return elem.text
        return None

    @property
    def all_texts(self):
        """Поиск всех элементов и выдача их текста"""
        if elements := self.find_all():
            return [element.text for element in elements]
        return []

    def click(self, screenshot=False):
        """Попытка нажатия элемента и вывод сообщения об ошибке в случае неудачи"""
        try:
            if elem := self.find():
                elem.click()
                if screenshot:
                    self.screenshot()
                return ''
            return f'Не найден элемент: {self.locator}'
        except WebDriverException as e:
            if screenshot:
                self.screenshot()
            return str(e).split('\n')[0]

    def find_by_text(self, text: str):
        """Поиск элемента с заданным текстом"""
        elements = self.find_all()
        if elements:
            texts = [element.text for element in elements]
            if text in texts:
                return elements[texts.index(text)]
        return None

    @allure.step('Прокрутка экрана')
    def check_app_and_swipe(self, app_name: str):
        """Прокручивания экрана и поиск приложения"""
        # 1. Проверка, что приложение видно до прокрутки
        elements = self.find_all()
        if not elements:
            allure
            return []
        texts = [element.text for element in elements]
        if app_name in texts:
            self.screenshot()
            return texts
        # 2. Листание экрана
        x1, y1, x2, y2 = elements[-2].rect['x'], elements[-2].rect['y'], elements[0].rect['x'], elements[0].rect['y']
        swipe_and_hold(x1, y1, x2, y2, .5)
        self.screenshot()
        return self.all_texts

    @allure.step('Переход на домашний экран Android')
    def go_home(self):
        """Нажатие кнопки Home (кружок на телефоне)"""
        self.driver.press_keycode(AndroidKey.HOME)
        self.screenshot()
