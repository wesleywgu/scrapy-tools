import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta

from misc.db import MongoDBUtil
from crawlab import save_item

if __name__ == "__main__":
    today_collection_name = 'results_spider_tools.scripts.today'
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    pt = today.strftime('%Y-%m-%d')

    mongo_util = MongoDBUtil(ip="192.168.1.2", db_name="crawlab", port="27017")
    collection_names = mongo_util.list_collection_names()

    spider_collections = set()
    for collection_name in collection_names:
        if today_collection_name == collection_name:
            rs = mongo_util.delete_many(today_collection_name, {'pt': pt})
            print('清除历史数据成功，表名：{table_name}, pt={pt}, 条数：{num}'.format(table_name=today_collection_name,
                                                                                   pt=pt,
                                                                                   num=rs.deleted_count))
        elif 'results_spider_tools' in collection_name:
            spider_collections.add(collection_name)

    # 查询今天发布的文章
    query = {
        'pub_time': {
            "$gte": yesterday.isoformat(),  # 大于等于昨天的开始时间
            "$lt": (today + timedelta(days=1)).isoformat()  # 小于今天的开始时间
        }
    }

    print('开始查询...')
    all_cnt = 0
    for name in spider_collections:
        rows = mongo_util.find(name, query)
        cnt = mongo_util.count_documents(name, query)
        all_cnt = all_cnt + cnt
        if cnt > 0:
            for row in rows:
                item = {
                    'pt': pt,
                    'content': row['content'],
                    'craw_time': row['craw_time'],
                    'source_url': row['source_url'],
                    'author': row['author'] if 'author' in row else '',
                    'pub_time': row['pub_time'],
                    'url': row['url'],
                }
                save_item(item)
            print('表名:{tmp_table}, 今日行数:{num}，写入完成'.format(tmp_table=name, num=cnt))
        else:
            print('表名:{table}, 今日无新发文章.'.format(table=name))

    # 总计行数
    print('总计: {all_cnt}'.format(all_cnt=all_cnt))
    # 关闭链接
    mongo_util.close()
