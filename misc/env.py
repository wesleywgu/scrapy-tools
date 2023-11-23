import os
from PyCookieCloud import PyCookieCloud


def get_env():
    env = os.environ.get('env', 'dev')
    print("machine env={}".format(env))
    return env


class CookerHelper:
    decrypted_data = None

    def __init__(self):
        env = os.environ.get('env', 'dev')
        if env == 'online':
            cookie_cloud = PyCookieCloud('http://192.168.1.2:8088', 'uMTz6qLwhiJrfSEffyC4mb', 'gw201221')
            self.decrypted_data = cookie_cloud.get_decrypted_data()
            print('cookie加载成功')
        else:
            cookie_cloud = PyCookieCloud('https://cookie.wesleyan.site', 'uMTz6qLwhiJrfSEffyC4mb', 'gw201221')
            self.decrypted_data = cookie_cloud.get_decrypted_data()
            print('cookie加载成功')

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
