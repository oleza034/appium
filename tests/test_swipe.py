import allure
import appium_elem
import pytest
from appium_elem import AppiumElement
from datetime import datetime, timedelta
from time import sleep


@allure.step('Поиск и открытие приложения PNV')
def open_pnv(app_name='Package Names', driver=None):
    """On the start screen, finds Package Names app and taps it"""

    elem = AppiumElement(f'//android.widget.TextView[@content-desc="{app_name}"]', webdriver=driver)
    # 1. Проверяем, что приложение открыто
    driver = driver or appium_elem.driver
    pkg = driver.current_package
    if pkg == 'com.csdroid.pkg':
        elem.screenshot()
        return ''

    # 2. Если нет - идём на начальный экран Android
    elem.go_home()

    # и пытаемся нажать ярлык приложения и возвращаем текст ошибки
    result = elem.click()
    if not result:
        sleep(2)
    elem.screenshot()
    return result


@allure.step('Поиск приложения Календарь')
def search_app(app:str):
    """Поиск в цикле приложения сс прокруткой экрана"""
    elem = AppiumElement('com.csdroid.pkg:id/tv_title')

    last_scene = elem.all_texts
    if not last_scene:
        elem.screenshot()
        pytest.fail(f'Не найдены элементы списка приложений. '
                    f'Проверьте, что приложение PNV открыто перед запуском теста')

    # Цикл поиска приложения
    while app not in last_scene:
        # Читаем список видимых приложений и прокручиваем экран
        element_names = elem.check_app_and_swipe(app)
        #  Если список тот же самый, значит весь список пролистан, выдаём ошибку
        if last_scene and element_names == last_scene:
            elem.screenshot()
            pytest.fail(f'Приложение {app} не найдено')
        last_scene = element_names

    elem.screenshot()
    return app


@allure.step('Открытие приложения Календарь')
def open_calendar(app='Calendar'):
    """Поиск и открытие приложения Календарь"""
    def tap_item(loc):
        """Вспомогательный метод: если элемент не найден, ждём по таймауту и тапаем его"""
        dt = datetime.now() + timedelta(seconds=2)
        while (err := AppiumElement(loc).click()) and datetime.now() < dt:
            sleep(.5)
        if err:
            pytest.fail(err)

    # Локаторы нужных элементов: 1. название приложения в списке поиска,
    # 2. сообщение с ID приложения и 3. кнопка Открыть
    items = (
        [
            f'//android.widget.TextView[@resource-id="com.csdroid.pkg:id/tv_title" and @text="{app}"]',
            'Проверка сообщения об открытии приложения'],
        ['android:id/message', ''],
        ['android:id/button1', 'Открытие приложения']
    )

    loc1, step1 = items[0]
    with allure.step(step1):
        # 1. жмём на приложение Календарь в списке приложений и ждём 2 сек.
        tap_item(loc1)
        sleep(2)
        # 2. читаем текст с ID приложения
        loc2, _ = items[1]
        elem: AppiumElement = AppiumElement(loc2)
        text = elem.text
        elem.screenshot()
        if not text:
            pytest.fail(f'Не найдено окно с данными о приложении {app}')

    # 3. Жмём кнопку Открыть
    loc3, step3 = items[2]
    with allure.step(step3):
        tap_item(loc3)
        sleep(2)
        elem.screenshot()

    # 4. Возвращаем ID приложения
    return text.split('\n')[0]


@pytest.mark.parametrize('driver', [''], indirect=True)
@allure.description('Поиск и открытие календаря')
def test_swipe(driver, app='Calendar'):
    """
    Домашнее задание по Appium:
    1. Открыть приложение PNW
    2. Свайпать вниз до заданного приложения
    3. Запустить приложение
    4. Сгенерировать отчёт в Appium / Allure
    """
    appium_elem.driver = driver

    if err := open_pnv(driver=driver):
        pytest.fail(f'Ошибка открытия приложения PNV: {err}')

    if search_app(app) != app:
        pytest.fail(f'Ошибка поиска приложения {app} в приложении Package Names')

    expected = open_calendar(app)

    with allure.step('Проверка запущенного приложения'):
        AppiumElement().screenshot()
        if expected != (pkg := driver.current_package):
            (f'Открыто неверное приложение {pkg}. Ожидается приложение {expected}. '
             f'Перед тестированием убедитесь, что приложение {app} настроено корректно.')
