from time import sleep
from appium import webdriver
from appium.options.common import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy

if __name__ == '__main__':
    option = AppiumOptions()
    option.set_capability("platformName", "Android")
    option.set_capability("platformVersion", "7.1.2")
    option.set_capability("deviceName", "emulator-5554")
    # option.set_capability("appPackage", "com.tencent.mm")
    # option.set_capability("appActivity", "com.tencent.mm.ui.LauncherUI")
    # option.set_capability("noReset", True)
    # option.set_capability("unicodeKeyboard", True)
    # option.set_capability("resetKeyboard", True)

    driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub', options=option)

    driver.find_element(AppiumBy.XPATH, '(//android.widget.ImageView[@resource-id="com.tencent.mm:id/f15"])[1]').click()

    # print("去登录")
    # sleep(5)
    # # 点击登录
    # driver.find_element(AppiumBy.ID, 'com.tencent.mm:id/j_9').click()
    # sleep(3)
    # # 输入电话号码
    # driver.find_element(AppiumBy.ID, 'om.tencent.mm:id/cd7').click()
    # driver.find_element(AppiumBy.ID, 'om.tencent.mm:id/cd7').send_keys("18606501239")
    # sleep(3)
    # driver.find_element(AppiumBy.ID, 'com.tencent.mm:id/hfe').click()
    # sleep(3)
    # driver.find_element(AppiumBy.XPATH,'//android.widget.EditText[@resource-id="com.tencent.mm:id/cd7" and @text="请填写微信密码"]').send_keys('gw201221')
    # sleep(3)
    # # 点击登录
    # driver.find_element(AppiumBy.ID, 'com.tencent.mm:id/hfe').click()
    # sleep(20)
