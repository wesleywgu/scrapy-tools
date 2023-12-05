import json
import os
import sys
from time import sleep

from .env import CookerHelper

sys.path.append(os.getcwd())
from .proxy import PROXIES, FREE_PROXIES, get_https_proxy
from .agents import AGENTS
from .reqs import SeleniumRequest
import logging as log

import random

from importlib import import_module
from scrapy import signals
import time

from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse
from selenium.webdriver.support.ui import WebDriverWait
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message


class TooManyRequestsRetryMiddleware(RetryMiddleware):
    def __init__(self, crawler):
        super(TooManyRequestsRetryMiddleware, self).__init__(crawler.settings)
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        elif response.status == 429:
            self.crawler.engine.pause()
            print("Response code is {code} Craw too fast, pase 60 seconds".format(code=response.status))
            time.sleep(60)  # If the rate limit is renewed in a minute, put 60 seconds, and so on.
            self.crawler.engine.unpause()
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        elif response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        return response


class SeleniumMiddleware:
    """Scrapy middleware handling the requests using selenium"""

    def __init__(self, driver_name, driver_executable_path,
                 browser_executable_path, command_executor, driver_arguments):
        """Initialize the selenium webdriver

        Parameters
        ----------
        driver_name: str
            The selenium ``WebDriver`` to use
        driver_executable_path: str
            The path of the executable binary of the driver
        driver_arguments: list
            A list of arguments to initialize the driver
        browser_executable_path: str
            The path of the executable binary of the browser
        command_executor: str
            Selenium remote server endpoint
        """

        webdriver_base_path = f'selenium.webdriver.{driver_name}'

        driver_klass_module = import_module(f'{webdriver_base_path}.webdriver')
        driver_klass = getattr(driver_klass_module, 'WebDriver')

        driver_options_module = import_module(f'{webdriver_base_path}.options')
        driver_options_klass = getattr(driver_options_module, 'Options')

        driver_options = driver_options_klass()

        if browser_executable_path:
            driver_options.binary_location = browser_executable_path
        for argument in driver_arguments:
            driver_options.add_argument(argument)

        # locally installed driver
        if driver_executable_path is not None:
            service_module = import_module(f'{webdriver_base_path}.service')
            service_klass = getattr(service_module, 'Service')
            service_kwargs = {
                'executable_path': driver_executable_path,
            }
            service = service_klass(**service_kwargs)
            driver_kwargs = {
                'service': service,
                'options': driver_options
            }
            self.driver = driver_klass(**driver_kwargs)
        # remote driver
        elif command_executor is not None:
            from selenium import webdriver
            self.driver = webdriver.Remote(command_executor=command_executor,
                                           options=driver_options)
        # 最大化
        self.driver.maximize_window()

    @classmethod
    def from_crawler(cls, crawler):
        """Initialize the middleware with the crawler settings"""

        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME')
        driver_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        browser_executable_path = crawler.settings.get('SELENIUM_BROWSER_EXECUTABLE_PATH')
        command_executor = crawler.settings.get('SELENIUM_COMMAND_EXECUTOR')
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS')

        if driver_name is None:
            raise NotConfigured('SELENIUM_DRIVER_NAME must be set')

        if driver_executable_path is None and command_executor is None:
            raise NotConfigured('Either SELENIUM_DRIVER_EXECUTABLE_PATH '
                                'or SELENIUM_COMMAND_EXECUTOR must be set')

        middleware = cls(
            driver_name=driver_name,
            driver_executable_path=driver_executable_path,
            browser_executable_path=browser_executable_path,
            command_executor=command_executor,
            driver_arguments=driver_arguments
        )

        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)

        return middleware

    def process_request(self, request, spider):
        """Process a request using the selenium driver if applicable"""

        if not isinstance(request, SeleniumRequest):
            return None

        if len(request.cookies.items()) > 0:
            # 设置cookies前必须访问一次登录的页面
            is_login = self.driver.get_cookie('is_login')
            if not is_login:
                self.driver.get(request.url)
                sleep(20)

                # 手动设置cookie
                for cookie_name, cookie_value in request.cookies.items():
                    self.driver.add_cookie(
                        {
                            'name': cookie_name,
                            'value': cookie_value
                        }
                    )
        # 如果有cookie, 设置完cookie后打开页面
        self.driver.get(request.url)

        if request.wait_until:
            WebDriverWait(self.driver, request.wait_time).until(
                request.wait_until
            )

        if request.screenshot:
            request.meta['screenshot'] = self.driver.get_screenshot_as_png()

        if request.script:
            self.driver.execute_script(request.script)

        body = str.encode(self.driver.page_source)

        # Expose the driver via the "meta" attribute
        request.meta.update({'driver': self.driver})

        return HtmlResponse(
            self.driver.current_url,
            body=body,
            encoding='utf-8',
            request=request
        )

    def spider_closed(self):
        """Shutdown the driver when spider is closed"""

        self.driver.quit()


class CustomHttpsProxyMiddleware(object):

    def process_request(self, request, spider):
        if self.use_proxy(request):
            p = get_https_proxy()
            try:
                request.meta['proxy'] = "https://%s" % p['proxy']
                log.debug("https proxy=" + json.dumps(p))
            except Exception as e:
                log.critical("Exception %s" % e)

    def use_proxy(self, request):
        """
        using direct download for depth <= 2
        using proxy with probability 0.3
        """
        if "depth" in request.meta and int(request.meta['depth']) <= 2:
            return False
        i = random.randint(1, 10)
        return i <= 2
        # return True


class LocalHttpProxyMiddleware(object):
    def process_request(self, request, spider):
        request.meta['proxy'] = 'http://127.0.0.1:7890'


class CustomUserAgentMiddleware(object):
    def process_request(self, request, spider):
        agent = random.choice(AGENTS)
        request.headers['User-Agent'] = agent


class WeiboUserAgentMiddleware(object):
    cookie_helper = CookerHelper()

    def process_request(self, request, spider):
        DEFAULT_REQUEST_HEADERS = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
            # 'Cookie': 'XSRF-TOKEN=eed8b6;SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5_O.oej.39ZcWLp6oDWTkx5JpX5KMhUgL.FoM7eo.4ehzNeoe2dJLoI7_N9PSj9PLkUfvrUBtt;MLOGIN=1;SUB=_2A25IVpDYDeRhGeFO6VsY8CzLyT-IHXVrLawQrDV6PUNbktAGLUXlkW1NQWztmWxNb9rt61yCFPkwNjX2-bV2Dgob;ALF=1702522248;_T_WM=88490918922;M_WEIBOCN_PARAMS=uicode%3D20000174;mweibo_short_token=635cdad34e;SCF=AmcpWYdzMxEhUWLHtPDTlbQwfWmdXoXXSAVDE3zNSqAnV4JAbsgvgN5zcVxF08F5CrUKyVsgWGEcze7Ztr3eris.;SSOLoginState=1699930248;WEIBOCN_FROM=1110006030'
        }
        agent = random.choice(AGENTS)
        request.headers['User-Agent'] = agent
        request.headers['Accept'] = DEFAULT_REQUEST_HEADERS['Accept']
        request.headers['Accept-Language'] = DEFAULT_REQUEST_HEADERS['Accept-Language']
        request.headers['Cookie'] = self.cookie_helper.get_cookie('.weibo.com')


class BaiduUserAgentMiddleware(object):
    cookie_helper = CookerHelper()

    def process_request(self, request, spider):
        DEFAULT_REQUEST_HEADERS = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
            'Host': 'www.baidu.com',
            'sec-ch-ua': 'Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24',
            'sec-ch-ua-platform': 'macOS',
            # 'Cookie':'PSINO=7;BD_UPN=123253;BAIDUID=4148AC0C82DD086DBD0EAB6A34FEFAE1:SL=0:NR=10:FG=1;BDUSS_BFESS=NTdzloU1c4Q0dKclJjclhod2dYd3J5UmxsSmQ2Y2NaMWZSLVA3TGNTeE1xMzVsSVFBQUFBJCQAAAAAAAAAAAEAAAAUTzM-Z3dwb3N0MTk5MQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEweV2VMHldlTG;__bid_n=18b9fb80cf4491295e9b4e;H_PS_645EC=44b6im%2FJIJIqJTk3q0CizP5ASrxgdJ8pNIXPYJAoS7dhpo8kxLDcikBpzVf2d4sx7d4k;ZFY=XKJqzdacFysubFfAHOZOZK:AoNqufZXskhjfd:Ad8xiDU:C;sug=3;delPer=0;ORIGIN=0;ab_sr=1.0.1_YjFhNWQ2ZTQ4MDIxOTAyZGFiODY2ODRmNzRkNmU1YmUwMjExY2VhZWVjNmJlNmZjODBlNDczZmE0MGYyOTY0Zjc1YzdlMmYzYjUyMjQ2NDhhMjlkZGMzMjkwNjZlYzI1ZTNhOWY5NmY1NDcyNTM4MjM5NjU4N2VhODEyMjg1NzQ2Nzc0OTIxOTQzYjUxZjg2NmFjMTBmOWYzZWJhNjM3Mw==;BAIDUID_BFESS=4148AC0C82DD086DBD0EAB6A34FEFAE1:SL=0:NR=10:FG=1;BD_CK_SAM=1;sugstore=0;BA_HECTOR=25ah25ag0galal8g8k8401241im0i9j1r;ispeed_lsm=2;BIDUPSID=4148AC0C82DD086DBD0EAB6A34FEFAE1;bdime=0;BDORZ=B490B5EBF6F3CD402E515D22BCDA1598;BDRCVFR[C0p6oIjvx-c]=mk3SLVN4HKm;BDRCVFR[feWj1Vr5u3D]=I67x6TjHwwYf0;BDSVRTM=236;BDUSS=NTdzloU1c4Q0dKclJjclhod2dYd3J5UmxsSmQ2Y2NaMWZSLVA3TGNTeE1xMzVsSVFBQUFBJCQAAAAAAAAAAAEAAAAUTzM-Z3dwb3N0MTk5MQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEweV2VMHldlTG;COOKIE_SESSION=709_0_4_4_1_19_1_0_2_4_1_0_0_0_2_0_1699057111_0_1699057109%7C4%230_0_1700745608%7C1%7C1;H_PS_PSSID=39648_39669_39663_39693_39695_39676_39712_39739_39780_39703_39685_39661_39678_39820_39817;H_WISE_SIDS=110085_265881_263619_275733_259642_256739_278414_281190_281234_279702_281810_281866_281897_281682_281828_281993_275097_274948_280650_282194_282521_282572_282604_280272_253022_282941_280292_282962_282402_282996_236312_280722_283355_283222_251972_283364_283596_283498_283633_281704_281051_282887_256223_279610_283867_283782_283897_283820_203518_283925_283923_283886_283981_284007_284024_284016_278388_284114_283950_284131_283946_284196_273241_284039_281839_284282_284284_281182_283356_284143_284409_276929_283932_284451_284602;H_WISE_SIDS_BFESS=110085_265881_263619_275733_259642_256739_278414_281190_281234_279702_281810_281866_281897_281682_281828_281993_275097_274948_280650_282194_282521_282572_282604_280272_253022_282941_280292_282962_282402_282996_236312_280722_283355_283222_251972_283364_283596_283498_283633_281704_281051_282887_256223_279610_283867_283782_283897_283820_203518_283925_283923_283886_283981_284007_284024_284016_278388_284114_283950_284131_283946_284196_273241_284039_281839_284282_284284_281182_283356_284143_284409_276929_283932_284451_284602;kleck=9dc6cb367c67e23a562bc4178537a2d5;MCITY=-289%3A;PSTM=1696470884;RT="z=1&dm=baidu.com&si=584a1bea-ddb1-4535-8972-c05d34b02755&ss=lp6b324a&sl=2&tt=1pk5&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=1rzv&ul=1srd&hd=1ss4"',
        }
        request.headers[
            'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        request.headers['Accept'] = DEFAULT_REQUEST_HEADERS['Accept']
        request.headers['Accept-Language'] = DEFAULT_REQUEST_HEADERS['Accept-Language']
        request.headers['Host'] = DEFAULT_REQUEST_HEADERS['Host']
        request.headers['sec-ch-ua'] = DEFAULT_REQUEST_HEADERS['sec-ch-ua']
        request.headers['sec-ch-ua-platform'] = DEFAULT_REQUEST_HEADERS['sec-ch-ua-platform']
        request.headers['Cookie'] = self.cookie_helper.get_cookie('.baidu.com')
        # request.headers['Cookie'] = DEFAULT_REQUEST_HEADERS['Cookie']


class GoogleUserAgentMiddleware(object):
    cookie_helper = CookerHelper()

    def process_request(self, request, spider):
        DEFAULT_REQUEST_HEADERS = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
        }
        request.headers[
            'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        request.headers['Accept'] = DEFAULT_REQUEST_HEADERS['Accept']
        request.headers['Accept-Language'] = DEFAULT_REQUEST_HEADERS['Accept-Language']
        request.headers['Cookie'] = self.cookie_helper.get_cookie('.google.com')
