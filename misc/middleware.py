import os
import sys
from time import sleep

sys.path.append(os.getcwd())
from .proxy import PROXIES, FREE_PROXIES
from .agents import AGENTS
from .requests import SeleniumRequest
import logging as log

import random

from importlib import import_module

from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse
from selenium.webdriver.support.ui import WebDriverWait


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


class CustomHttpProxyFromMysqlMiddleware(object):
    proxies = FREE_PROXIES

    def process_request(self, request, spider):
        # TODO implement complex proxy providing algorithm
        if self.use_proxy(request):
            p = random.choice(self.proxies)
            try:
                request.meta['proxy'] = "http://%s" % p['ip_port']
                print(request.meta['proxy'])
            except Exception as e:
                # log.msg("Exception %s" % e, _level=log.CRITICAL)
                log.critical("Exception %s" % e)

    def use_proxy(self, request):
        """
        using direct download for depth <= 2
        using proxy with probability 0.3
        """
        # if "depth" in request.meta and int(request.meta['depth']) <= 2:
        #    return False
        # i = random.randint(1, 10)
        # return i <= 2
        return True


class CustomHttpProxyMiddleware(object):

    def process_request(self, request, spider):
        # TODO implement complex proxy providing algorithm
        if self.use_proxy(request):
            p = random.choice(PROXIES)
            try:
                request.meta['proxy'] = "http://%s" % p['ip_port']
            except Exception as e:
                # log.msg("Exception %s" % e, _level=log.CRITICAL)
                log.critical("Exception %s" % e)

    def use_proxy(self, request):
        """
        using direct download for depth <= 2
        using proxy with probability 0.3
        """
        # if "depth" in request.meta and int(request.meta['depth']) <= 2:
        #    return False
        # i = random.randint(1, 10)
        # return i <= 2
        return True


class LocalHttpProxyMiddleware(object):
    def process_request(self, request, spider):
        # request.meta['proxy'] = 'http://127.0.0.1:7890'
        request.meta['proxy'] = 'http://192.168.1.254:7890'


class CustomUserAgentMiddleware(object):
    def process_request(self, request, spider):
        agent = random.choice(AGENTS)
        request.headers['User-Agent'] = agent


class WeiboUserAgentMiddleware(object):
    def process_request(self, request, spider):
        DEFAULT_REQUEST_HEADERS = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
            'Cookie': 'WBtopGlobal_register_version=2023111214;SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5_O.oej.39ZcWLp6oDWTkx5JpX5KzhUgL.FoM7eo.4ehzNeoe2dJLoI7_N9PSj9PLkUfvrUBtt;SCF=AmcpWYdzMxEhUWLHtPDTlbQwfWmdXoXXSAVDE3zNSqAnongJh_1R04emj0dDgaebWYf4Bv11mto8nfW35Xvr3kc.;_s_tentry=www.amz123.com;UOR=,,www.amz123.com;SUB=_2A25IVApEDeRhGeFO6VsY8CzLyT-IHXVrKAOMrDV8PUNbmtANLWz-kW9NQWztmZkmYhNmjW5A0cgGP8Z8CjOvoPkG;Apache=2559002441077.0586.1699597577296;ALF=1731308948;PC_TOKEN=bc73529cb3;SINAGLOBAL=8684552721605.112.1696770171512;SSOLoginState=1699597596;ULV=1699597577339:7:3:2:2559002441077.0586.1699597577296:1699518952747'
        }
        agent = random.choice(AGENTS)
        request.headers['User-Agent'] = agent
        request.headers['Accept'] = DEFAULT_REQUEST_HEADERS['Accept']
        request.headers['Accept-Language'] = DEFAULT_REQUEST_HEADERS['Accept-Language']
        request.headers['Cookie'] = DEFAULT_REQUEST_HEADERS['Cookie']


class BaiduUserAgentMiddleware(object):
    def process_request(self, request, spider):
        DEFAULT_REQUEST_HEADERS = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
            'Cookie': 'PSINO=2;BD_UPN=123253;BAIDUID=4148AC0C82DD086DBD0EAB6A34FEFAE1:SL=0:NR=10:FG=1;BDUSS_BFESS=NTdzloU1c4Q0dKclJjclhod2dYd3J5UmxsSmQ2Y2NaMWZSLVA3TGNTeE1xMzVsSVFBQUFBJCQAAAAAAAAAAAEAAAAUTzM-Z3dwb3N0MTk5MQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEweV2VMHldlTG;__bid_n=18b9fb80cf4491295e9b4e;H_PS_645EC=4f9fvCfHPhthvl1dXgd4tclYbw6uWHUSZAGSugHtaul8klC7m0dkgHO8Cw;ZFY=Xk5iY9dO8fBhC1BxcEkF69w12BVfWHP4FG9XTb0BM0k:C;sug=3;delPer=0;ORIGIN=0;BAIDUID_BFESS=4148AC0C82DD086DBD0EAB6A34FEFAE1:SL=0:NR=10:FG=1;BD_CK_SAM=1;sugstore=0;BA_HECTOR=ak0h240180258k8gag0505a51ile7f71q;ispeed_lsm=2;newlogin=1;BIDUPSID=4148AC0C82DD086DBD0EAB6A34FEFAE1;bdime=0;BDORZ=B490B5EBF6F3CD402E515D22BCDA1598;BDRCVFR[C0p6oIjvx-c]=OewyZereRT6mydlnHc1QhPEUf;BDRCVFR[feWj1Vr5u3D]=I67x6TjHwwYf0;BDRCVFR[gUg2cUtcsBT]=_M5urk4djP3fA4-ILn;BDSVRTM=832;BDUSS=NTdzloU1c4Q0dKclJjclhod2dYd3J5UmxsSmQ2Y2NaMWZSLVA3TGNTeE1xMzVsSVFBQUFBJCQAAAAAAAAAAAEAAAAUTzM-Z3dwb3N0MTk5MQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEweV2VMHldlTG;H_PS_PSSID=39648_39669_39663_39688_39693_39695_39676;Hmery-Time=2164186134;MCITY=-289%3A;PSTM=1696470884;RT="z=1&dm=baidu.com&si=584a1bea-ddb1-4535-8972-c05d34b02755&ss=loz5zare&sl=3&tt=9na&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=ahgd&ul=ai1l&hd=ai3t"'
        }
        agent = random.choice(AGENTS)
        request.headers[
            'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        request.headers['Accept'] = DEFAULT_REQUEST_HEADERS['Accept']
        request.headers['Accept-Language'] = DEFAULT_REQUEST_HEADERS['Accept-Language']
        request.headers['Cookie'] = DEFAULT_REQUEST_HEADERS['Cookie']

class GoogleUserAgentMiddleware(object):
    def process_request(self, request, spider):
        DEFAULT_REQUEST_HEADERS = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
            'Cookie':'SAPISID=WQYRonAa1WEO_9N9/AIIaCL8N96qOFocbI;__Secure-3PAPISID=WQYRonAa1WEO_9N9/AIIaCL8N96qOFocbI;AEC=Ackid1T9WGly4WBzbps13ab_kmdw_39k5umQcOU2j3I040PUjD4F9trqKw;NID=511=r_Nd0jSHDJwigBMqs_qERsb5gRMjMrVDKcs4fHBLStZuUpN2tZmzncn_XBDchvI9KO_oCcdmjJguY8HUFN8cyLQs4MI-FGgeyYf7l0YmILo_kywFxUdR0bl9LAylborTjlAa5EHRRgr57mOxX8clzv4AyRgPSOmcvkC0wp-VZv9EVYdmYW7LFpDCt2G_zKAyNx5aKGcWrtob7dxWUtGWCtXWTt0EFtnokSERyuteFkBqYEyRir1DMq1OrvxXxBg8K3czpofE-FMCzKpME_nbiYdZyIg_Jl_GwKE-CSIBMXcXi7nrLsZiH1fAyaaCJ79C6QosyyOdxEfeROiGC0dke5NtBRJIwjDIYDummw3hG-lGRs4JhbVZq0ti6g8oxYqeF6uf8hrdDICGVOpkYhOwxtVImmsQM7cWRukZjCNAfw6fRsthHRgasusH4m0lkPIRjk8NaYDCdCNUKhVXHYMg3RbqPX8ifnzWJkDKrr4XJaNe4fXxu3leqE7eqHx6PtR6XQRp-9rbNbi_TBNNDean3vbd9s29Fc6VkeXxCij-sw5oCFYcTJzJszWj5MmwT7VnzP4laOWspGdblGo;APISID=BCS7mxAkCNE1Dk64/AriD-EP9rouzR4W1o;__Secure-1PSIDTS=sidts-CjIBNiGH7gCqdsShJUqEA5fqFre4NH1XHSn2nn68I-L-vZ96SXsVx59nAnWnSEszYAiTshAA;GOOGLE_ABUSE_EXEMPTION=ID=d17133ecbd295396:TM=1700365245:C=r:IP=2406:4440:0:103:1:0:9:a-:S=ceNZmTeO8rCL6hHgnGjzgZk;OTZ=7281490_24_24__24_;__Secure-1PAPISID=WQYRonAa1WEO_9N9/AIIaCL8N96qOFocbI;__Secure-3PSID=cwgq-kaHG9OVj6qb741Afen5jmbrPS8eC6X_momWAhcVcGyMHQc9Y5gkOFlizloQaYjCZg.;1P_JAR=2023-11-19-03;__Secure-1PSID=cwgq-kaHG9OVj6qb741Afen5jmbrPS8eC6X_momWAhcVcGyMVamZOTnv5s8x6pGILoeEzQ.;__Secure-1PSIDCC=ACA-OxPA9kOMe4QqsPFTUzkQfOfKQ035XjC0m1L-JNTYQHeu4Vy1NEZaHT0XcvDuQbVyc3jrp6M;__Secure-3PSIDCC=ACA-OxPh-YabCAJIJ0wVm6PF2T8Kpon2bhbafIq3C5NwQuyqSs_T73q3GyXxBRqoETFVgzjTEWU;__Secure-3PSIDTS=sidts-CjIBNiGH7gCqdsShJUqEA5fqFre4NH1XHSn2nn68I-L-vZ96SXsVx59nAnWnSEszYAiTshAA;DV=o4Yt_wY8R4lTUAuW96t36_5O1rVavpj-BnbWayEtigEAAICGSTB--aTysAAAAASIm0L1K13fLQAAAGnw0XD9ZnENEQAAAA;HSID=AuVL9Nb08ll8F7qc4;SEARCH_SAMESITE=CgQI4JkB;SID=cwgq-kaHG9OVj6qb741Afen5jmbrPS8eC6X_momWAhcVcGyM85rtzU7jbtSbZyZTWkW7gw.;SIDCC=ACA-OxNhDuK9DBGye0yjSh6t5_XmkoXHKqXjhvI-PRFzRM5M5jISRM5U2PMNmbBGGirNOqEpOjU;SSID=AbHEKrhLcnzJNuIQX',
        }
        agent = random.choice(AGENTS)
        request.headers[
            'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        request.headers['Accept'] = DEFAULT_REQUEST_HEADERS['Accept']
        request.headers['Accept-Language'] = DEFAULT_REQUEST_HEADERS['Accept-Language']
        request.headers['Cookie'] = DEFAULT_REQUEST_HEADERS['Cookie']
