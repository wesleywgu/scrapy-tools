import time

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.common import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy


def get_capabilities():
    option = AppiumOptions()
    option.set_capability("platformName", "Android")  # 操作系统
    option.set_capability("platformVersion", "9")  # 设备版本号
    option.set_capability("deviceName", "bc20c6a")  # 设备 ID
    option.set_capability("appPackage", "com.tencent.mm")  # app 包名
    option.set_capability("appActivity", "com.tencent.mm.ui.LauncherUI")  # app 启动时主 Activity
    option.set_capability("noReset", True)  # 是否保留 session 信息，可以避免重新登录
    option.set_capability("unicodeKeyboard", True)  # 使用 unicodeKeyboard 的编码方式来发送字符串
    option.set_capability("resetKeyboard", True)  # 将键盘给隐藏起来
    option.set_capability("automationName", 'UiAutomator2')
    return option


# # 添加好友
# def add_friends():
#     driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub', options=get_capabilities())
#     time.sleep(10)
#     print('点击+号')
#     driver.find_element('com.tencent.mm:id/ef9').click()
#     time.sleep(5)
#     print('选择添加朋友')
#     driver.find_element('com.tencent.mm:id/gam')[1].click()
#     time.sleep(5)
#     print('点击搜索框')
#     driver.find_element('com.tencent.mm:id/fcn').click()
#     time.sleep(5)
#     print('在搜索框输入微信号')
#     driver.find_element('com.tencent.mm:id/bhn').send_keys('ityard')
#     time.sleep(3)
#     print('点击搜索')
#     driver.find_element('com.tencent.mm:id/ga1').click()
#     time.sleep(3)
#     print('点击添加到通讯录')
#     driver.find_element('com.tencent.mm:id/g6f').click()
#
#
# def send_msg():
#     driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub', options=get_capabilities())
#     time.sleep(10)
#     print('点击微信搜索框')
#     driver.find_element_by_id('com.tencent.mm:id/f8y').click()
#     time.sleep(10)
#     print('在搜索框输入搜索信息')
#     driver.find_element_by_id('com.tencent.mm:id/bhn').send_keys('Python小二')
#     time.sleep(3)
#     print('点击搜索到的好友')
#     driver.find_element_by_id('com.tencent.mm:id/tm').click()
#     time.sleep(3)
#     # 输入文字
#     driver.find_element_by_id('com.tencent.mm:id/al_').send_keys('hello')
#     time.sleep(3)
#     # 输入表情
#     driver.find_element_by_id('com.tencent.mm:id/anz').click()
#     time.sleep(3)
#     driver.find_element_by_id('com.tencent.mm:id/rv').click()
#     # 点击发送按钮发送信息
#     driver.find_element_by_id('com.tencent.mm:id/anv').click()
#     # 退出
#     driver.quit()

def start_setting():
    capabilities = dict(
        platformName='Android',
        automationName='uiautomator2',
        deviceName='Android',
        appPackage='com.android.settings',
        appActivity='.Settings',
        # language='en',
        # locale='US'
    )
    appium_server_url = 'http://localhost:4723'
    driver = webdriver.Remote(appium_server_url, options=UiAutomator2Options().load_capabilities(capabilities))
    el = driver.find_element(by=AppiumBy.XPATH, value='//*[@text="WLAN"]')
    el.click()
    time.sleep(10)
    driver.quit()


def search_articles(key_word):
    capabilities = dict(
        platformName='Android',
        automationName='uiautomator2',
        deviceName='Android',
        appPackage='com.tencent.mm',
        appActivity='com.tencent.mm.ui.LauncherUI',
        noReset=True,
        unicodeKeyboard=True,
        resetKeyboard=True
    )
    appium_server_url = 'http://localhost:4723'
    driver = webdriver.Remote(appium_server_url, options=UiAutomator2Options().load_capabilities(capabilities))
    time.sleep(5)
    # 点击搜索
    driver.find_element(AppiumBy.XPATH, '(//android.widget.ImageView[@resource-id="com.tencent.mm:id/f15"])[1]').click()
    time.sleep(5)
    # # 点击搜搜内容框
    driver.find_element('com.tencent.mm:id/cd7').click()
    # 输入搜索内容
    driver.find_element('com.tencent.mm:id/cd7').send_keys(key_word)
    time.sleep(5)
    # 点击搜索结果页跳转按钮
    driver.find_element(AppiumBy.XPATH,
                        '(//android.widget.LinearLayout[@resource-id="com.tencent.mm:id/ohx"])[1]/android.widget.ImageView[2]').click()
    time.sleep(5)
    driver.find_element('//android.view.View[@text="已选定,公众号,按钮,13之4"]').click()


if __name__ == '__main__':
    search_articles('拼多多')
    # start_setting()
