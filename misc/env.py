import os
from PyCookieCloud import PyCookieCloud


def get_env():
    env = os.environ['env']
    print("machine env={}".format(env))
    return env


class CookerHelper:
    def __init__(self):
        cookie_cloud = PyCookieCloud('https://cookie.wesleyan.site', 'uMTz6qLwhiJrfSEffyC4mb', 'gw201221')
        self.decrypted_data = cookie_cloud.get_decrypted_data()

    def get_cookie(self, domain):
        items = self.decrypted_data[domain]
        all_cookie = []
        for item in items:
            all_cookie.append(item['name'] + '=' + item['value'])
        return ';'.join(all_cookie)