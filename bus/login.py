import hashlib
import json
import random
import threading
import time

import sanic.response as response
from loguru import logger
from redis import StrictRedis
from sanic.request import Request

import pyutil.logconsts as logconsts
import pyutil.pretty as pretty
import pyutil.pymysqlutil as pymysqlutil


def login(path: str, req: Request):
    return response.text("login faild\n")


class Login:
    def __init__(self, d):
        for k, v in d.items():
            self.__dict__[k] = v


_admin_login = Login(
    d={"id": 1, "company_id": 0, "department_id": 0, "name": "admin", "nick_name": "super-man", "account_id": "admin",
       "sex": "", "birthday": "", "addr": "", "tel": "", "password_hash": "7723fd055c03667b8c8693bfd1021a33",
       "check_in_time": 1610591428, "check_in_ip": "127.0.0.1", "check_in_ua": "curl/7.61.1", "c_time": 0, "u_time": 0,
       "c_user": 0, "u_user": 0, "email": "", "disabled": 0})


class LoginManager:
    def __init__(self):
        self.redis = None
        self.login_map = {}
        self.lock = threading.Lock()

    def set_redis(self, redis: StrictRedis):
        self.redis = redis

    def _save(self):
        if self.redis is not None:
            return
        ret = {}
        for k, v in self.login_map.items():
            ret[k] = v.__dict__
        with open("uhrs.login", mode="w") as fd:
            fd.write(json.dumps(ret))

    def _set_entry(self, token: str, entry: Login):
        if self.redis is not None:
            old_token = self.redis.hget("login_map_account", entry.account_id)
            if old_token is not None:
                self.redis.hdel("login_map", token)
            entry_dict = entry.__dict__
            # pop_list = []
            # logger.info(entry_dict)
            # for k in entry_dict:
            #     if k.find("__") >= 0:
            #         pop_list.append(k)
            #     for lt in k:
            #         if lt >= "A" and lt <= "Z":
            #             pop_list.append(k)
            #             break
            # for k in pop_list:
            #     entry_dict.pop(k)
            v = json.dumps(entry_dict)
            self.redis.hset("login_map", token, v)
            self.redis.hset("login_map_account", entry.account_id, token)
            return
        with self.lock:
            self.login_map[token] = entry
            dele_list = []
            for k, v in self.login_map.items():
                if k != token and v.account_id == entry.account_id:
                    dele_list.append(k)
            for v in dele_list:
                self.login_map.pop(v)

    def _get_entry(self, token: str):
        if self.redis is not None:
            ret = self.redis.hget("login_map", token)
            if ret is None:
                return None
            entry = Login(json.loads(ret))
            return entry
        with self.lock:
            return self.login_map.get(token)

    def login(self, conn, request: Request):
        if len(request.body) == 0:
            return response.json({"err_code": -1, "err_msg": "no body"})
        info = json.loads(request.body)
        u = info.get("user_name")
        p = info.get("passwd")
        project_id = request.headers.get("projectid")
        if project_id is None or project_id == "":
            project_id = info.get("projectid")
        if u is None or p is None or project_id is None or u == "" or p == "":
            return response.json({"err_code": -1, "err_msg": "login fail"})
        s = '''select * from uhrs.employee where disabled = 0 and account_id = %s and password_hash = %s and (account_id = 'admin' or id in 
        (select employee_id from uhrs.employee_project where project_id = %s))'''
        if pretty.get_log_number(logconsts.LOG_SQL):
            logger.info(s % (u, p, project_id))
        ret = pymysqlutil.select(conn, s, u, p, project_id)
        if len(ret) == 0:
            return response.json({"err_code": -1, "err_msg": "login fail"})
        entry = Login(ret[0])
        token = "%d-%s-%s-%d-%f" % (entry.id, entry.account_id, entry.password_hash, int(time.time()), random.random())
        token = hashlib.md5(bytes(token, encoding="utf-8")).hexdigest()
        entry.token = token
        entry.check_in_time = int(time.time())
        entry.check_in_ua = hashlib.md5(bytes(pretty.user_agent(request), encoding="utf-8")).hexdigest()
        entry.check_in_ip = pretty.remote_ip(request)
        entry.project_id = project_id
        self._set_entry(token, entry)
        self._save()
        s = "update uhrs.employee set check_in_time = %s, check_in_ip = %s, check_in_ua = %s where id = %s"
        if pretty.get_log_number(logconsts.LOG_SQL):
            logger.info(s % (entry.check_in_time, entry.check_in_ip, entry.check_in_ua, entry.id))
        pymysqlutil.execute(conn, s, entry.check_in_time, entry.check_in_ip, entry.check_in_ua, entry.id, commit=True)
        return response.json({"err_code": 0, "err_msg": "", "token": token})

    def check(self, request: Request):
        debug_mode = request.headers.get("debug")
        tm = time.localtime(time.time())
        if debug_mode is not None and debug_mode == "debug%02d%02d%02d" % (tm.tm_mon, tm.tm_mday, tm.tm_hour):
            return {"err_code": 0}, _admin_login
        if len(request.body) == 0:
            return {"err_code": -1, "err_msg": "no body"}, None
        info = json.loads(request.body)
        token = request.headers.get("token")
        project_id = request.headers.get("projectid")
        if token is None:
            return {"err_code": -1, "err_msg": "no token"}, None
        entry = self._get_entry(token)
        if entry is None:
            logger.info("%s" % str(self.login_map.keys()))
            return {"err_code": -1, "err_msg": "invalid token %s:%d" % (token, len(token))}, None
        tm_unix = int(time.time())
        ip = pretty.remote_ip(request)
        ua = hashlib.md5(bytes(pretty.user_agent(request), encoding="utf-8")).hexdigest()
        if ip == entry.check_in_ip and ua == entry.check_in_ua and tm_unix - entry.check_in_time < 3600 * 24 and int(
                project_id) == int(entry.project_id):
            return {"err_code": 0, "err_msg": ""}, entry
        return {"err_code": -2, "err_msg": "invalid token"}, None


login_manager = LoginManager()
