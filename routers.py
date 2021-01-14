import time

import sanic.request
import sanic.response as response
from loguru import logger
from sanic import Sanic

import bus.company
import bus.department
import bus.employee
import bus.login as login
import bus.project
import pyutil.dbpool as dbpool
import pyutil.logconsts as logconsts
import pyutil.pretty as pretty
from bus.employeeproject import employee_project
from pyutil.pretty import Defer

_handlers = {}
app = Sanic("UHRS")
boot_time = time.time()


@app.middleware('request')
async def log_request(request: sanic.request.Request):
    if pretty.get_log_number(logconsts.LOG_HTTP):
        logger.info("%s\n%s" % (str(request.headers), str(request.body)))


@app.middleware('response')
async def log_response(request, response):
    if pretty.get_log_number(logconsts.LOG_HTTP):
        logger.info("%s:\n%s" % (request.url, str(response.output())))


async def uhrs_handle(request, name):
    conn = dbpool.connection("uhrs")
    df = Defer(conn.close)
    resp = response.HTTPResponse(status=404)
    if name == "login":
        resp = login.login_manager.login(conn, request)
    elif name == "ping":
        tm = time.localtime(boot_time)
        resp = response.json({"version": "1.1", "boot_time": "%d-%d-%d %d:%d" % (
            tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min)})
    else:
        check_ret, login_entry = login.login_manager.check(request)
        if check_ret.get("err_code") == 0:
            if name == "check":
                resp = response.json(check_ret)
            elif name == "company":
                resp = bus.company.company.handle_request(conn, request, login_entry)
            elif name == "department":
                resp = bus.department.department.handle_request(conn, request, login_entry)
            elif name == "employee":
                resp = bus.employee.employee.handle_request(conn, request, login_entry)
            elif name == "project":
                resp = bus.project.project.handle_request(conn, request, login_entry)
            elif name == "employee_project":
                resp = employee_project.handle_request(conn, request, login_entry)

        else:
            resp = response.json(check_ret)

    return resp


app.add_route(uhrs_handle, "/uhrs/<name>", methods=["GET", "POST"])
