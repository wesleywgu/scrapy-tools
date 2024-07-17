import csv
import pickle
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# 配置ChromeDriver路径
chrome_driver_path = '/Users/guwen/Downloads/chromedriver-mac-x64/chromedriver'  # 请替换为你本地的chromedriver路径
service = Service(chrome_driver_path)
options = webdriver.ChromeOptions()

csv_file = 'linkin.csv'
csv_columns = ['name', 'link', 'desc', 'area']
csvfile = open(csv_file, 'a', newline='', encoding='utf-8')
writer = csv.DictWriter(csvfile, fieldnames=csv_columns)

# 判断文件是否为空，如果为空则写入表头
csvfile.seek(0, 2)  # 移动到文件末尾
if csvfile.tell() == 0:
    writer.writeheader()


def craw_page(n):
    # 等待页面加载
    time.sleep(5)

    # 使用JavaScript将页面滚动到最底部
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)

    # 获取好友列表
    connections = driver.find_elements(By.CSS_SELECTOR, 'li.reusable-search__result-container')
    print("page " + str(n) + ", connection count: " + str(len(connections)))

    for connection in connections:
        try:
            name = connection.find_element(By.XPATH,
                                           './/div/div/div/div[2]/div[1]/div[1]/div/span[1]/span/a/span/span[1]').text
            nane_link = connection.find_element(By.CSS_SELECTOR, 'a.app-aware-link').get_attribute('href')
            desc = connection.find_element(By.XPATH, './/div/div/div/div[2]/div[1]/div[2]').text
            area = connection.find_element(By.XPATH, './/div/div/div/div[2]/div[1]/div[3]').text

            data = {
                'name': name,
                'link': nane_link,
                'desc': desc,
                'area': area
            }
            print(data)
            writer.writerow(data)
        except Exception as ex:
            pass


if __name__ == '__main__':

    # 初始化webdriver
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 10)
    driver.maximize_window()

    driver.get("https://www.linkedin.com")

    # 保存cookie到文件
    # time.sleep(300)
    # with open("cookies_wq.pkl", "wb") as file:
    #     pickle.dump(driver.get_cookies(), file)

    # 加载cookie
    time.sleep(5)
    with open("cookies_wq.pkl", "rb") as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            print(cookie)
            driver.add_cookie(cookie)

    # 刷新页面以应用cookie
    driver.refresh()

    # 访问好友列表页面
    url_ceo = 'https://www.linkedin.com/search/results/people/?connectionOf=%5B%22ACoAAA8kUOUBr1uJOawiaNG2X4CP9PtkiOJF9ZY%22%5D&network=%5B%22F%22%2C%22S%22%5D&origin=MEMBER_PROFILE_CANNED_SEARCH&page=11&sid=0DC'
    # url_test = 'https://www.linkedin.com/search/results/people/?connectionOf=%5B%22ACoAADnw1I0BJtEyIX61L9iv0EbSA8eTHc3ngVs%22%5D&network=%5B%22F%22%2C%22S%22%5D&origin=MEMBER_PROFILE_CANNED_SEARCH&sid=SXA'
    driver.get(url_ceo)
    print('\n')
    craw_page(1)

    # 查找并点击“下页”按钮
    for i in range(86):
        try:
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']")))
            next_button.click()

            # 爬取下一页
            print('\n')
            craw_page(i + 2)

        except Exception as e:
            print(f"无法点击下一页按钮: {e}")
            break

    # 关闭浏览器
    driver.quit()
