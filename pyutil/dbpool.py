import configparser

import pymysql
from dbutils.pooled_db import PooledDB

_pool_dict = {}


def _create_pool(pool_name, host, port, db, user, password, charset="utf8", max_conn=100):
    ret = PooledDB(
        creator=pymysql,  # 使用链接数据库的模块
        maxconnections=max_conn,  # 连接池允许的最大连接数，0和None表示不限制连接数
        mincached=0,  # 初始化时，链接池中至少创建的空闲的链接，0表示不创建
        maxcached=5,  # 链接池中最多闲置的链接，0和None不限制
        blocking=False,  # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待然后报错
        maxusage=None,  # 一个链接最多被重复使用的次数，None表示无限制
        setsession=[],  # 开始会话前执行的命令列表。如：["set datestyle to ...", "set time zone ..."]
        ping=0,
        # ping MySQL服务端，检查是否服务可用。# 如：0 = None = never, 1 = default = whenever it is requested, 2 = when a cursor is created, 4 = when a query is executed, 7 = always
        host=host,
        port=port,
        user=user,
        password=password,
        database=db,
        charset=charset
    )
    _pool_dict[pool_name] = ret


def connection(pool_name):
    return _pool_dict.get(pool_name).connection()


def init_db_pool(conf: configparser.ConfigParser):
    pools = conf.get("db", "pool-list")
    pool_list = pools.split(sep=",")
    for v in pool_list:
        sec = "dbpool." + v
        host = conf.get(sec, "host", fallback="127.0.0.1")
        port = conf.getint(sec, "port", fallback=3306)
        user = conf.get(sec, "user", fallback="unknown")
        passwd = conf.get(sec, "password", fallback="unknown")
        db = conf.get(sec, "db", fallback="unknown")
        max_conn = conf.getint(sec, "max-conn", fallback=100)
        _create_pool(v, host=host, port=port, user=user, password=passwd, db=db, max_conn=max_conn)
    return
