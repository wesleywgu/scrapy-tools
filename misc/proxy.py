'''
This proxy is goagent/wallproxy
If you want to disable it, plz configure settings.py
'''
import requests

from misc.env import get_env

PROXIES = [
    # {"ip_port": "127.0.0.1:8087"}, #goagent
    # {"ip_port": "127.0.0.1:8118"}, #tor via privoxy
    {"ip_port": "127.0.0.1:7890"},  # tor via privoxy
]

FREE_PROXIES = [
    {"ip_port": "181.48.0.173:8081"},
    {"ip_port": "82.43.21.165:3128"},
    {"ip_port": "185.112.234.4:80"},
    {"ip_port": "118.189.13.178:8080"},
    {"ip_port": "37.187.117.157:3128"},
    {"ip_port": "62.201.200.17:80"},
    {"ip_port": "181.143.28.210:3128"},
    {"ip_port": "216.190.97.3:3128"},
    {"ip_port": "183.111.169.205:3128"},
]


# 代理池：https://github.com/jhao104/proxy_pool
def get_https_proxy():
    env = get_env()
    if env == 'online':
        return requests.get("http://192.168.1.253:5010/get?type=https").json()
    else:
        return requests.get("http://proxy.wesleyan.site/get?type=https").json()


if __name__ == '__main__':
    url = 'https://cip.cc'
    p = get_https_proxy()
    proxies = {
        "https": "https://" + p['proxy']
    }
    data = requests.get(url=url, proxies=proxies)
    print(data)
