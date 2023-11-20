import pymysql


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
