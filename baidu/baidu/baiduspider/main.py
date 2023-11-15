from baiduspider import BaiduSpider
from pprint import pprint

if __name__ == '__main__':

    pprint(BaiduSpider().search_news("拼多多", pn=2).plain)