import json
import os
import sys
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta

from misc.db import MongoDBUtil
from crawlab import save_item

if __name__ == "__main__":
    today_collection_name = 'results_spider_tools.scripts.today'

    mongo_util = MongoDBUtil(ip="192.168.1.2", db_name="crawlab", port="27017")

    try:
        collection_names = mongo_util.list_collection_names()

        spider_collections = set()
        for collection_name in collection_names:
            if today_collection_name == collection_name:
                mongo_util.drop_collection(today_collection_name)
                print('清除历史数据成功，表名：{table_name}'.format(table_name=today_collection_name))
            elif 'results_spider_tools' in collection_name:
                spider_collections.add(collection_name)

        # 查询今天发布的文章
        today_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) - timedelta(days=1)  # 昨日10点
        end_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        query = {
            '$or': [
                {
                    'pub_time': {
                        "$gte": start_time.strftime("%Y-%m-%d %H:%M:%S"),  # 大于等于昨天的开始时间
                        "$lt": end_time.strftime("%Y-%m-%d %H:%M:%S")  # 小于今天的开始时间
                    }
                },
                {
                    '$and': [
                        {'pub_time': "无"},
                        {
                            'craw_time': {
                                "$gte": today_time.strftime("%Y-%m-%d %H:%M:%S"),
                                "$lt": end_time.strftime("%Y-%m-%d %H:%M:%S")
                            }
                        },
                    ]
                }
            ]
        }

        print(f'开始查询, 时间范围：【{start_time},{end_time}】...'.format(start_time=start_time, end_time=end_time))
        print('查询条件：' + json.dumps(query))
        all_cnt = 0
        for name in spider_collections:
            rows = mongo_util.find(name, query)
            cnt = mongo_util.count_documents(name, query)
            all_cnt = all_cnt + cnt
            if cnt > 0:
                for row in rows:
                    item = {
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
    except Exception as ex:
        traceback.print_exc()
        # 关闭链接
        mongo_util.close()
