import getpass
import json
import socket

import psutil
from sanic.request import Request


class Defer:
    '''
    模拟golang的defer
    python的try...finally...和with语句都能实现函数结尾保证做一件事情，但是没有golang的defer那么优雅，比如说会增加缩进，
    这里参考c++的RAII技术实现一个类似golang的defer的功能：
    构造函数传入finally要执行的函数极其执行时要调用的参数
    '''

    def __init__(self, fn, *args):
        self.defer_func = fn
        self.defer_argv = args

    def __del__(self):
        if len(self.defer_argv) == 0:
            self.defer_func()
        else:
            self.defer_func(*self.defer_argv)


def clear_empty(dict_or_list, int_empty=0, float_empty=1e-5, clear_bool_false=True, str_empty='', list_empty=[],
                dict_empty={}):
    """
    清除list或dict中的空白值, 当把对象序列化之前先清理无意义的空白值，可用显著减少输出的字节数
    :param dict_or_list: 要清理的list或dict
    :param int_empty: int类型空值定义
    :param float_empty: float类型空值定义,由于浮点数不能以==比较，因此两个浮点数之差<=float_empty的认为是空值
    :param clear_bool_false: 是否清除false值
    :param str_empty: 空字符串的定义
    :param list_empty: 空list的定义
    :param dict_empty: 空dict的定义
    :return: dict or list,如果返回dict则返回入参dict_or_list,如果返回list，则返回一个新的list
    """
    if type(dict_or_list) is dict:
        remove_list = []
        update_list = {}
        for k, v in dict_or_list.items():
            v_type = type(v)
            if v_type is str and v == str_empty:
                remove_list.append(k)
            elif v_type is int and v == int_empty:
                remove_list.append(k)
            elif v_type is float and abs(v - 0.0) <= float_empty:
                remove_list.append(k)
            elif v_type is bool and not v and clear_bool_false:
                remove_list.append(k)
            elif v_type is dict:
                vv = clear_empty(v, int_empty, float_empty, clear_bool_false, str_empty, list_empty, dict_empty)
                if vv == dict_empty:
                    remove_list.append(k)
                else:
                    update_list[k] = vv
            elif v_type is list:
                vv = clear_empty(v, int_empty, float_empty, clear_bool_false, str_empty, list_empty, dict_empty)
                if vv == list_empty:
                    remove_list.append(k)
                else:
                    update_list[k] = vv
        for remove_key in remove_list:
            dict_or_list.pop(remove_key, 0)
        dict_or_list.update(update_list)
    elif type(dict_or_list) is list:
        ret = []
        for v in dict_or_list:
            v_type = type(v)
            if v_type is str and v != str_empty:
                ret.append(v)
            elif v_type is int and v != int_empty:
                ret.append(v)
            elif v_type is float and abs(v - 0.0) > float_empty:
                ret.append(v)
            elif v_type is bool and (v or not clear_bool_false):
                ret.append(v)
            elif v_type is dict:
                vv = clear_empty(v, int_empty, float_empty, clear_bool_false, str_empty, list_empty, dict_empty)
                if vv != dict_empty:
                    ret.append(vv)
            elif v_type is list:
                vv = clear_empty(v, int_empty, float_empty, clear_bool_false, str_empty, list_empty, dict_empty)
                if vv != list_empty:
                    ret.append(vv)
            else:
                ret.append(v)
        return ret
    return dict_or_list


def local_ip_v4():
    '''
    :return: local ipv4 list
    '''
    ret = []
    netCardList = psutil.net_if_addrs()
    for k, v in netCardList.items():
        for netCardInfo in v:
            if netCardInfo.family == 2 and netCardInfo.address != '127.0.0.1':
                return netCardInfo.address
    return ret


def local_ip_v6():
    '''
    :return: get local ipv6 list
    '''
    ret = []
    netCardList = psutil.net_if_addrs()
    for k, v in netCardList.items():
        for netCardInfo in v:
            if netCardInfo.family == 10 and netCardInfo.address != '::1':
                ls = netCardInfo.address.split("%", 2)
                if len(ls) > 1:
                    ret.append(ls[0])
                else:
                    ret.append(netCardInfo.address)
    return ret


host_name = socket.gethostname()
user_name = getpass.getuser()
ipv4s = local_ip_v4()
ipv6s = local_ip_v6()
log_number = {}


def set_log_number(i):
    global log_number
    log_number[i] = 1
    return


def unset_log_number(i):
    global log_number
    log_number.pop(i)
    return


def get_log_number(num):
    return num in log_number


def split_by_line(s):
    ret = []
    ls = s.split(sep="\r\n")
    for v in ls:
        line = v.strip("\r\n")
        ls2 = line.split("\n")
        for v2 in ls2:
            line2 = v2.strip("\n")
            ret.append(line2)
    return ret


def trim_json_comment(jsn):
    if len(jsn) == "":
        return ""
    ret = ""
    lines = split_by_line(jsn)
    for v in lines:
        s = v.strip()
        if s[:2] == "//":
            continue
        if ret != "":
            ret += "\n"
        ret += v
    return ret


def base64_padding(b64str):
    n = len(b64str) % 4
    if n == 3:
        return b64str + "="
    if n == 2:
        return b64str + "=="
    return b64str


def ipv4_int(ipv4str):
    ls = ipv4str.split(sep=".")
    if len(ls) != 4:
        return 0
    b1 = int(ls[0])
    b2 = int(ls[1])
    b3 = int(ls[2])
    b4 = int(ls[3])
    return b1 << 24 | b2 << 16 << b3 << 8 | b4


def is_private_ip(ipv4):
    """
    局域网可使用的网段（私网地址段）有三大段：
    10.0.0.0~10.255.255.255（A类）
    172.16.0.0~172.31.255.255（B类）
    192.168.0.0~192.168.255.255（C类）
    :return: True or False
    """
    ipv4int = ipv4_int(ipv4)
    if ipv4int == 0:
        return False
    if 167772160 < ipv4int < 184549375:
        return True
    if 2886729728 < ipv4int < 2887778303:
        return True
    if 3232235520 < ipv4int < 3232301055:
        return True
    return False


def format_numeric_thousands(num):
    tp = type(num)
    s = ""
    if tp == int:
        s = ("%d" % num)
    elif tp == float:
        s = ("%.2f" % num)
    else:
        return ""
    ls = s.split(sep=".", maxsplit=1)
    tail = ""
    if len(ls) > 1:
        tail = ls[1]
        s = ls[0]
    sign = (s[0] == "-")
    if sign:
        s = s[1:]
    n = len(s) % 3
    ret = ""
    b = 0
    i = n
    if n == 0:
        i == 3
    while i <= len(s):
        if ret != "":
            ret += ","
        ret += s[b:i]
        b = i
        i += 3
    if sign:
        ret = "-" + ret
    if tail != "":
        ret = ret + "." + tail
    return ret


def replace_str_list(str_list, replacement_dict):
    if len(str_list) == 0 or len(replacement_dict) == 0:
        return str_list
    ret = []
    for v in str_list:
        s = v
        for old, new in replacement_dict.items():
            s = s.replace(old, new)
        ret.append(s)
    return ret


def replace_str(s, replacement_dict):
    if len(s) == 0 or len(replacement_dict) == 0:
        return s
    ret = s
    for old, new in replacement_dict.items():
        ret = ret.replace(old, new)
    return ret


class JsonDupException(Exception):
    pass


def check_json_dup_hook(lst):
    d = {}
    for v in lst:
        if v[0] in d:
            raise JsonDupException
        else:
            d[v[0]] = 1
    return {}


def check_json_dup(json_str):
    try:
        json.loads(json_str, object_pairs_hook=check_json_dup_hook)
    except JsonDupException:
        return False
    return True


def simple_obj_to_str(obj):
    if type(obj) is str:
        return '\"' + str(obj) + '\"'
    else:
        return str(obj)


def object_dump_json(obj, indent=4):
    ret = ""
    tp = type(obj)
    if not hasattr(obj, "__dict__") and not tp is dict and not tp is list:
        ret = simple_obj_to_str(obj)
        return ret
    if tp is dict:
        line = 0
        for k, v in obj.items():
            indent_str = " "
            indent_str *= indent
            lines = '"%s": %s' % (str(k), object_dump_json(v, indent + 4))
            lines = indent_str + lines
            if line == 0:
                ret += lines
            else:
                ret = ret + ",\n" + lines
            line += 1
    elif hasattr(obj, "__dict__"):
        line = 0
        for k, v in obj.__dict__.items():
            indent_str = " "
            indent_str *= indent
            lines = '"%s": %s' % (str(k), object_dump_json(v, indent + 4))
            lines = indent_str + lines
            if line == 0:
                ret += lines
            else:
                ret = ret + ",\n" + lines
            line += 1
    elif tp is list:
        line = 0
        for v in obj:
            indent_str = " "
            indent_str *= indent
            lines = '%s' % (object_dump_json(v, indent + 4))
            lines = indent_str + lines
            if line == 0:
                ret += lines
            else:
                ret = ret + ",\n" + lines
            line += 1

    ret = "{%s}" % ret
    return ret


def remote_ip(request: Request):
    for k, v in request.headers.items():
        if k.lower() == "x-real-ip":
            return str(v)
    for k, v in request.headers.items():
        if k.lower() == "x-forwarded-for":
            return str(v)
    return request.ip


def user_agent(request: Request):
    for k, v in request.headers.items():
        if k.lower() == "user-agent":
            return str(v)
    return ""
