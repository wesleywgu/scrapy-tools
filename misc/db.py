import pymysql
import pymongo


class MySQLUtil:
    """
    MySQL工具类
    """

    def __init__(self, host="127.0.0.1", port=3306, user=None, passwd=None, db=None, charset="utf8", *args, **kwargs):
        """构造函数"""
        self.__host = host
        self.__user = user
        self.__passwd = passwd
        self.__db = db
        self.__conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db, charset=charset, *args,
                                      **kwargs)
        self.__cursor = self.__conn.cursor()

    def __del__(self):
        """析构函数"""
        self.__cursor.close()
        self.__conn.close()

    def close(self):
        self.__cursor.close()
        self.__conn.close()

    def get_conn(self):
        """获取连接"""
        return self.__conn

    def get_cursor(self, cursor=None):
        """获取游标"""
        return self.__conn.cursor(cursor)

    def select_db(self, db):
        """选择数据库"""
        self.__conn.select_db(db)

    def list_databases(self, args=None):
        """查询所有数据库"""
        self.__cursor.execute("SHOW DATABASES", args)
        dbs = []
        for db in self.__cursor.fetchall():
            dbs.append(db[0])
        return dbs

    def list_tables(self, args=None):
        """查询所有表"""
        self.__cursor.execute("SHOW TABLES", args)
        tables = []
        for table in self.__cursor.fetchall():
            tables.append(table[0])
        return tables

    def execute(self, sql, args=None):
        """获取SQL执行结果"""
        self.__cursor.execute(sql, args)
        return self.__cursor.fetchall()

    def get_version(self, args=None):
        """获取MySQL版本"""
        self.__cursor.execute("SELECT VERSION()", args)
        version = self.__cursor.fetchone()
        print("MySQL Version : %s" % version)
        return version

    def list_table_metadata(self, args=None):
        """查询所有表的元数据信息"""
        sql = "SELECT * FROM information_schema.TABLES WHERE TABLE_TYPE !='SYSTEM VIEW' AND TABLE_SCHEMA NOT IN ('sys','mysql','information_schema','performance_schema')"
        self.__cursor.execute(sql, args)
        return self.__cursor.fetchall()

    def get_table_fields(self, db, table, args=None):
        """获取表字段信息"""
        sql = 'SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE table_schema="' + db + '" AND table_name="' + table + '"'
        self.__cursor.execute(sql, args)
        fields = []
        for field in self.__cursor.fetchall():
            fields.append(field[0])
        return fields

    def table_metadata(self, db, table, args=None):
        """查询表字段的元数据信息"""
        db = "'" + db + "'"
        table = "'" + table + "'"
        sql = "SELECT column_name,column_type,ordinal_position,column_comment,column_default FROM information_schema.COLUMNS WHERE table_schema = %s AND table_name = %s;" % (
            db, table)
        self.__cursor.execute(sql, args)
        return self.__cursor.fetchall()


class MongoDBUtil:
    """
    MongoDB工具类
    """

    def __init__(self, ip="127.0.0.1", db_name=None, port="27017"):
        """构造函数"""
        self.client = pymongo.MongoClient("mongodb://" + ip + ":" + port)
        self.database = self.client[db_name]

    def __del__(self):
        """析构函数"""
        # print("__del__")
        self.client.close()

    def close(self):
        self.client.close()

    def create_database(self, db_name):
        """创建数据库"""
        return self.client.get_database(db_name)

    def drop_database(self, db_name):
        """删除数据库"""
        return self.client.drop_database(db_name)

    def select_database(self, db_name):
        """使用数据库"""
        self.database = self.client[db_name]
        return self.database

    def get_database(self, db_name):
        """使用数据库"""
        # return self.client[db_name]
        return self.client.get_database(db_name)

    def list_database_names(self):
        """获取所有数据库列表"""
        return self.client.list_database_names()

    def create_collection(self, collect_name):
        """创建集合"""
        collect = self.database.get_collection(collect_name)
        if (collect is not None):
            print("collection %s already exists" % collect_name)
            return collect
        return self.database.create_collection(collect_name)

    def drop_collection(self, collect_name):
        """获取所有集合名称"""
        return self.database.drop_collection(collect_name)

    def get_collection(self, collect_name):
        """获取集合"""
        return self.database.get_collection(collect_name)

    def list_collection_names(self):
        """获取所有集合名称"""
        return self.database.list_collection_names()

    def insert(self, collect_name, documents):
        """插入单条或多条数据"""
        return self.database.get_collection(collect_name).insert(documents)

    def insert_one(self, collect_name, document):
        """插入一条数据"""
        return self.database.get_collection(collect_name).insert_one(document)

    def insert_many(self, collect_name, documents):
        """插入多条数据"""
        return self.database.get_collection(collect_name).insert_many(documents)

    def delete_one(self, collect_name, filter, collation=None, hint=None, session=None):
        """删除一条记录"""
        return self.database.get_collection(collect_name).delete_one(filter, collation, hint, session)

    def delete_many(self, collect_name, filter, collation=None, hint=None, session=None):
        """删除所有记录"""
        return self.database.get_collection(collect_name).delete_many(filter, collation, hint, session)

    def find_one_and_delete(self, collect_name, filter, projection=None, sort=None, hint=None, session=None, **kwargs):
        """查询并删除一条记录"""
        return self.database.get_collection(collect_name).find_one_and_delete(filter, projection, sort, hint, session,
                                                                              **kwargs)

    def count_documents(self, collect_name, filter, session=None, **kwargs):
        """查询文档数目"""
        return self.database.get_collection(collect_name).count_documents(filter, session, **kwargs)

    def find_one(self, collect_name, filter=None, *args, **kwargs):
        """查询一条记录"""
        return self.database.get_collection(collect_name).find_one(filter, *args, **kwargs)

    def find(self, collect_name, *args, **kwargs):
        """查询所有记录"""
        return self.database.get_collection(collect_name).find(*args, **kwargs)

    def update(self, collect_name, spec, document, upsert=False, manipulate=False,
               multi=False, check_keys=True, **kwargs):
        """更新所有记录"""
        return self.database.get_collection(collect_name).update(spec, document,
                                                                 upsert, manipulate, multi, check_keys, **kwargs)

    def update_one(self, collect_name, filter, update, upsert=False, bypass_document_validation=False,
                   collation=None, array_filters=None, hint=None, session=None):
        """更新一条记录"""
        return self.database.get_collection(collect_name).update_one(filter, update,
                                                                     upsert, bypass_document_validation, collation,
                                                                     array_filters, hint, session)

    def update_many(self, collect_name, filter, update, upsert=False, array_filters=None,
                    bypass_document_validation=False, collation=None, hint=None, session=None):
        """更新所有记录"""
        return self.database.get_collection(collect_name).update_many(filter, update,
                                                                      upsert, array_filters, bypass_document_validation,
                                                                      collation, hint, session)

    def find_one_and_update(self, collect_name, filter, update, projection=None, sort=None, upsert=False,
                            return_document=False, array_filters=None, hint=None, session=None, **kwargs):
        """查询并更新一条记录"""
        return self.database.get_collection(collect_name).find_one_and_update(filter, update, projection,
                                                                              sort, upsert, return_document,
                                                                              array_filters, hint, session, **kwargs)
