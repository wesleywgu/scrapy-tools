import json
import os
import logging
from PyCookieCloud import PyCookieCloud

logger = logging.getLogger(__name__)


def get_env():
    env = os.environ.get('env', 'dev')
    logger.info("machine env={}".format(env))
    return env


class CookerHelper:
    decrypted_data = None
    logger = logging.getLogger(__name__)

    def __init__(self):
        env = os.environ.get('env', 'dev')

        if env == 'online':
            url = 'http://192.168.1.2:8088'
        else:
            url = 'https://cookie.wesleyan.site'

        cookie_cloud = PyCookieCloud(url, 'uMTz6qLwhiJrfSEffyC4mb', 'gw201221')
        self.decrypted_data = cookie_cloud.get_decrypted_data()
        if self.decrypted_data:
            self.logger.info('cookie加载成功, cookie=' + json.dumps(self.decrypted_data))
        else:
            self.logger.error('cookie加载失败')

    def get_cookie(self, domain):
        items = self.decrypted_data[domain]
        all_cookie = []
        for item in items:
            all_cookie.append(item['name'] + '=' + item['value'])
        return ';'.join(all_cookie)

    def get_cookie_dict(self, domain):
        items = self.decrypted_data[domain]
        cookie_dict = {}
        for item in items:
            cookie_dict[item['name']] = item['value']
        return cookie_dict
