import json

import pymysql
import sanic.response
from loguru import logger
from sanic.request import Request

import pyutil.logconsts as logconsts
import pyutil.pretty as pretty


class KeyNotFound(Exception):
    pass


class Entity:
    def __init__(self, table_name: str, key_field_list: []):
        self._table_name = table_name
        self._key_field_list = key_field_list
        self._key_field_dict = dict(zip(key_field_list, key_field_list))
        self.login_entry = None

    def set_login(self, login_entry):
        self.login_entry = login_entry

    def _insert_sql(self, entity: dict, update_when_exists: bool):
        keys = ""
        values_holder = ""
        values = []
        # on duplicate key update request = request + %d
        dup_update = ""
        dup_update_values = []
        for k, v in entity.items():
            if v is None:
                continue
            if keys != "":
                keys += ", "
                values_holder += ", "
                dup_update += ", "
            keys += k
            values_holder += "%s"
            values.append(v)
            if update_when_exists:
                dup_update = dup_update + k + " = %s"
                dup_update_values.append(v)
        sql = "insert into %s (%s) values (%s)" % (self._table_name, keys, values_holder)
        if update_when_exists and len(dup_update_values) > 0:
            sql += " on duplicate key update %s " % dup_update
            values.extend(dup_update_values)
        return sql, values

    def _update_sql(self, entity: dict):
        update = ""
        update_values = []
        where = ""
        where_values = []
        for key in self._key_field_list:
            key_exists = False
            for k, v in entity.items():
                if k == key:
                    key_exists = True
                    where_values.append(v)
                    break
            if not key_exists:
                raise KeyNotFound
            if where != "":
                where += " and "
            where = where + key + " = %s"
        for k, v in entity.items():
            if k in self._key_field_dict:
                continue
            if v is None:
                continue
            if update != "":
                update += ", "
            update = update + k + "= %s"
            update_values.append(v)
        sql = "update %s set %s where %s" % (self._table_name, update, where)
        return sql, update_values + where_values

    def _delete_sql(self, entity: dict):
        where = ""
        where_values = []
        for key in self._key_field_list:
            key_exists = False
            for k, v in entity.items():
                if v is None:
                    continue
                if k == key:
                    key_exists = True
                    where_values.append(v)
                    break
            if not key_exists:
                raise KeyNotFound
            if where != "":
                where += " and "
            where = where + key + " = %s"
        sql = "delete from %s where %s" % (self._table_name, where)
        return sql, where_values

    def _select_sql(self, entity: dict):
        where = ""
        where_values = []
        for k, v in entity.items():
            if v is None:
                continue
            if where != "":
                where += " and "
            where = where + k + " = %s"
            where_values.append(v)
        sql = "select * from %s where %s" % (self._table_name, where)
        return sql, where_values

    def _before_insert(self, conn, entity: dict):
        pass

    def _before_update(self, conn, entity: dict):
        pass

    def _before_delete(self, conn, entity: dict):
        pass

    def _before_select(self, conn, entity: dict):
        pass

    def _after_insert(self, conn, entity: dict):
        pass

    def _after_update(self, conn, entity: dict):
        pass

    def _after_delete(self, conn, entity: dict):
        pass

    def _after_select(self, conn: pymysql.Connection, entity: dict):
        pass

    def handle_request(self, conn, request: Request, login_entry):
        # print(request.url)
        self.set_login(login_entry)
        action = request.args.get("action")
        if action is None or len(action) == 0:
            return sanic.response.json({"err_code": -1, "err_msg": "no action"})
        if type(action) is list:
            action = action[0]
        if len(request.body) == 0:
            return sanic.response.json({"err_code": -2, "err_msg": "no body"})
        if action == "new":
            entity = json.loads(request.body)
            err_msg = ""
            n = 0
            id = 0
            try:
                n, id = self.insert(conn, entity)
            except Exception as e:
                err_msg = str(e)
            if n > 0 and id > 0:
                return sanic.response.json({"err_code": 0, "_id": id})
            return sanic.response.json({"err_code": -1, "err_msg": err_msg})
        elif action == "modify":
            entity = json.loads(request.body)
            err_msg = ""
            n = 0
            try:
                n = self.update(conn, entity)
            except Exception as e:
                err_msg = str(e)
            if n > 0:
                return sanic.response.json({"err_code": 0})
            return sanic.response.json({"err_code": -1, "err_msg": err_msg})
        elif action == "delete":
            entity = json.loads(request.body)
            err_msg = ""
            n = 0
            try:
                n = self.delete(conn, entity)
            except Exception as e:
                err_msg = str(e)
            if n > 0:
                return sanic.response.json({"err_code": 0})
            return sanic.response.json({"err_code": -1, "err_msg": err_msg})
        elif action == "query":
            entity = json.loads(request.body)
            err_msg = ""
            ret = []
            try:
                ret = self.select(conn, entity)
            except Exception as e:
                err_msg = str(e)
            if err_msg == "":
                return sanic.response.json({"err_code": 0, "data_list": ret})
            return sanic.response.json({"err_code": -1, "err_msg": err_msg})
        else:
            return sanic.response.json({"err_code": -1, "err_msg": "action: %s not support" % action})

    def insert(self, conn, entity: dict, update_when_exists=False):
        # return effected rows, inserted rowid
        self._before_insert(conn, entity)
        sql, values = self._insert_sql(entity, update_when_exists)
        cur = conn.cursor()
        df = pretty.Defer(cur.close)
        if pretty.get_log_number(logconsts.LOG_SQL):
            logger.info(cur.mogrify(sql, values))
        cur.execute(sql, values)

        self._after_insert(conn, entity)
        conn.commit()
        effected_rows, inserted_id = cur.rowcount, cur.lastrowid
        return effected_rows, inserted_id

    def update(self, conn, entity: dict):
        # return effected rows
        self._before_update(conn, entity)
        sql, values = self._update_sql(entity)
        cur = conn.cursor()
        df = pretty.Defer(cur.close)
        if pretty.get_log_number(logconsts.LOG_SQL):
            logger.info(cur.mogrify(sql, values))
        cur.execute(sql, values)

        effected_rows = cur.rowcount
        self._after_update(conn, entity)
        conn.commit()

        return effected_rows

    def delete(self, conn, entity: dict):
        # return effected rows
        self._before_delete(conn, entity)
        sql, values = self._delete_sql(entity)
        cur = conn.cursor()
        df = pretty.Defer(cur.close)
        if pretty.get_log_number(logconsts.LOG_SQL):
            logger.info(cur.mogrify(sql, values))
        cur.execute(sql, values)
        effected_rows = cur.rowcount

        self._after_delete(conn, entity)
        conn.commit()

        return effected_rows

    def select(self, conn, entity: dict):
        # return [entities]
        self._before_select(conn, entity)
        sql, values = self._select_sql(entity)
        cur = conn.cursor()
        df = pretty.Defer(cur.close)
        if pretty.get_log_number(logconsts.LOG_SQL):
            logger.info(cur.mogrify(sql, values))
        cur.execute(sql, values)

        self._after_select(conn, entity)
        conn.commit()
        data = cur.fetchall()
        key_list = []
        desc = cur.description
        for v in desc:
            key_list.append(v[0])
        ret = []
        for v in data:
            ret.append(dict(zip(key_list, v)))
        return ret
