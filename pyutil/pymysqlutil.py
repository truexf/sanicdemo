import pyutil.pretty as pretty
import pyutil.logconsts as logconsts
from loguru import logger


def select(conn, sql, *args):
    '''
    pymysql sql query
    :param conn: pymysql connection
    :param sql: sql with %param
    :param args: param values
    :return: [{field_name1: field_value1, field_name2: field_value2},{...}]
    '''
    cur_data = conn.cursor()
    defer = pretty.Defer(cur_data.close)
    if pretty.get_log_number(logconsts.LOG_SQL):
        logger.info(cur_data.mogrify(sql, args))
    cur_data.execute(sql, args)
    data = cur_data.fetchall()
    key_list = []
    desc = cur_data.description
    for v in desc:
        key_list.append(v[0])
    ret = []
    for v in data:
        ret.append(dict(zip(key_list, v)))
    return ret

def execute(conn, sql, *args, commit=False):
    '''
    insert inton xxx values(%s,%s)
    pymysql sql execution
    :param conn: pymysql connection
    :param commit: bool, commit transction
    :param sql: sql with %param
    :param args: param values
    :return: effected records count
    '''
    cur = conn.cursor()
    defer = pretty.Defer(cur.close)
    if pretty.get_log_number(logconsts.LOG_SQL):
        logger.info(cur.mogrify(sql, args))
    ret = cur.execute(sql, args)
    if commit:
        conn.commit()
    return ret

def execute_many(conn, sql, *args, commit=False):
    '''
    insert into xxx values(%s,%s)
    pymysql sql execution
    :param conn: pymysql connection
    :param commit: bool, commit transction
    :param sql: sql with %param
    :param args: param values
    :return: effected records count
    '''
    cur = conn.cursor()
    defer = pretty.Defer(cur.close)
    ret = cur.executemany(sql, *args)
    if commit:
        conn.commit()
    return ret
