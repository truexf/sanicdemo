import configparser
import os
import sys

from loguru import logger
from redis import StrictRedis

import bus.login
import pyutil.daemon as daemon
import pyutil.dbpool as dbpool
import pyutil.pretty as pretty
import routers

if __name__ == "__main__":
    # disable stdin, redirect stdout/stderr to uhrs.out
    stdout = open(file="uhrs.out", mode="a", encoding="utf-8")
    stdin = open(file="/dev/null")
    os.dup2(stdin.fileno(), sys.stdin.fileno())
    os.dup2(stdout.fileno(), sys.stderr.fileno())
    os.dup2(stdout.fileno(), sys.stdout.fileno())

    # become a daemon process
    daemon.daemonize(pid_file="uhrs.pid")

    # init loguru
    logger.remove(None)
    # logger.add(sink="uhrs_{time}.log", rotation="00:00", retention="10 days")
    logger.add(sink="uhrs.log")
    logger.info("starting uhrs service...")
    conf = configparser.ConfigParser()
    conf.read(filenames="uhrs.cfg", encoding="utf-8")
    log_num_list = conf.get("server", "log_num_list", fallback="")
    for num in log_num_list.split(","):
        pretty.set_log_number(int(num))

    # init db pool
    dbpool.init_db_pool(conf)

    # init redis
    redis_on = conf.has_section("redis")
    if redis_on:
        redis = StrictRedis(host=conf.get("redis", "host"), port=conf.getint("redis", "port"),
                            db=conf.getint("redis", "db"), password=conf.get("redis", "password"))
    bus.login.login_manager.set_redis(redis)

    # startup http server
    if redis_on:
        worker_num = conf.getint("server", "worker_num")
    else:
        worker_num = 1  # multi-process can not share global dict
    routers.app.run(host=conf.get("net", "host"), port=conf.getint("net", "port"),
                    workers=worker_num, access_log=False)
