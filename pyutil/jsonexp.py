import json


class Dictionary:
    def __init__(self):
        self.__var_list = {}
        self.__assign_list = {}
        self.__compare_list = {}

    def register_var(self, var_name, fn):
        if (not type(var_name) is str) or (var_name == "") or (var_name[0] != "$") or (not hasattr(fn, "__call__")):
            return
        self.__var_list[var_name] = fn

    def register_compare(self, compare_name, fn):
        if (not type(compare_name) is str) or (compare_name == "") or (not hasattr(fn, "__call__")):
            return
        self.__compare_list[compare_name] = fn

    def register_assign(self, assign_name, fn):
        if (not type(assign_name) is str) or (assign_name == "") or (not hasattr(fn, "__call__")):
            return
        self.__assign_list[assign_name] = fn

    def get_var_value(self, var_name, context_dict):
        if not type(var_name) is str or var_name == "" or not type(context_dict) is dict:
            return None
        if var_name[0] != "$":
            return None
        var_parts = var_name.split(sep=".")
        fn = self.__var_list.get(var_parts[0])
        if fn is None:
            return None
        ret = fn(context_dict)
        if len(var_parts) > 1:
            if var_parts[1] == "lower":
                return str(ret).lower()
            if var_parts[1] == "upper":
                return str(ret).upper()
            if var_parts[1] == "len":
                return len(str(ret))
        return ret

    def compare(self, compare_name, left, right, context_dict):
        if left is None or right is None or not type(compare_name) is str:
            return None
        fn = self.__compare_list.get(compare_name)
        if fn is None:
            return None
        if type(left) is str and left != "" and left[0] == "$":
            left_value = self.get_var_value(left, context_dict)
        else:
            left_value = left
        if type(right) is str and right != "" and right[0] == "$":
            right_value = self.get_var_value(right, context_dict)
        else:
            right_value = right
        return fn(left_value, right_value, context_dict)

    def assign(self, assign_name, left, right, context_dict):
        # print(assign_name,left,right)
        if not type(left) is str or left == "" or left[0] != "$" or right is None or not type(
                assign_name) is str or not type(context_dict) is dict:
            return
        fn = self.__assign_list.get(assign_name)
        if fn is None:
            # print("%s not found", assign_name)
            return
        if not type(left) is str or str == "" or left[0] != "$":
            return
        if type(right) is str and right != "" and right[0] == "$":
            right_value = self.get_var_value(right, context_dict)
        else:
            right_value = right
        fn(left, right_value, context_dict)

    def get_var(self, var_name):
        return self.__var_list.get(var_name)

    def get_compare(self, compare_name):
        return self.__compare_list.get(compare_name)

    def get_assign(self, assign_name):
        return self.__assign_list.get(assign_name)

    def list_var(self):
        return self.__var_list

    def list_compare(self):
        return self.__compare_list

    def list_assign(self):
        return self.__assign_list


class NameValue:
    def __init__(self):
        self.name = ""
        self.value = None


class AssignExp:
    def __init__(self, l, r, assign_name):
        self.l, self.r, self.assign_name = l, r, assign_name


class CompareExp:
    def __init__(self, l, r, compare_name):
        self.l, self.r, self.compare_name = l, r, compare_name


class JsonExp:
    def __init__(self, compare_exp_list, assign_exp_list, dictionary):
        self.__compare_exp_list = compare_exp_list
        self.__assign_exp_list = assign_exp_list
        self.__dictionary = dictionary

    def execute(self, context_dict):
        for v in self.__compare_exp_list:
            comp = self.__dictionary.compare(v.compare_name, v.l, v.r, context_dict)
            if not comp:
                return
        for v in self.__assign_exp_list:
            self.__dictionary.assign(v.assign_name, v.l, v.r, context_dict)

    def compare_list(self):
        return self.__compare_exp_list

    def assign_list(self):
        return self.__assign_exp_list


class JsonExpGroup:
    def __init__(self, exp_group, dictionary):
        self.__dictionary = dictionary
        self.__json_exp_list = []
        self.valid = False
        for i in range(len(exp_group)):
            exp_node = exp_group[i]
            assign_list = []
            compare_list = []
            if not type(exp_node) is list:
                return
            for j in range(len(exp_node)):
                if j == len(exp_node) - 1:
                    assign_exp = exp_node[j]
                    if not type(assign_exp) is list:
                        return
                    if len(assign_exp) == 3 and type(assign_exp[0]) is str and assign_exp[0] != "" and assign_exp[0][
                        0] == "$" and type(assign_exp[1]) is str and not dictionary.get_assign(assign_exp[1]) is None:
                        assign_list.append(AssignExp(assign_exp[0], assign_exp[2], assign_exp[1]))
                    else:
                        for k in range(len(assign_exp)):
                            assign_exp_inner = assign_exp[k]
                            if not type(assign_exp_inner) is list:
                                return
                            if len(assign_exp_inner) == 3 and type(assign_exp_inner[0]) is str and assign_exp_inner[
                                0] != "" and \
                                    assign_exp_inner[0][0] == "$" and type(
                                assign_exp_inner[1]) is str and not dictionary.get_assign(assign_exp_inner[1]) is None:
                                assign_list.append(
                                    AssignExp(assign_exp_inner[0], assign_exp_inner[2], assign_exp_inner[1]))
                else:
                    compare_exp = exp_node[j]
                    if not type(compare_exp) is list:
                        return
                    if len(compare_exp) == 3 and type(compare_exp[1]) is str and not dictionary.get_compare(
                            compare_exp[1]) is None:
                        compare_list.append(CompareExp(compare_exp[0], compare_exp[2], compare_exp[1]))

            if len(assign_list) > 0:
                self.__json_exp_list.append(JsonExp(compare_list, assign_list, dictionary))

        if len(self.__json_exp_list) == 0:
            return
        self.valid = True

    def list(self):
        return self.__json_exp_list


class Configuration:
    def __init__(self, jsn_str, dictionary):
        self.__jsn = jsn_str
        self.__exp_dict = {}
        self.__name_value_dict = {}
        self.__dictionary = dictionary
        self.__parse()

    def __parse(self):
        d = json.loads(self.__jsn)
        for k, v in d.items():
            if not type(v) is list:
                self.__name_value_dict[k] = v
            else:
                exp_group = JsonExpGroup(v, self.__dictionary)
                if exp_group.valid:
                    self.__exp_dict[k] = exp_group
                else:
                    self.__name_value_dict[k] = v

    def exp_dict(self):
        return self.__exp_dict

    def name_value_dict(self):
        return self.__name_value_dict

    def execute_exp_group(self, group_name: str, content_dict: dict):
        if group_name == "":
            return
        exp_group = self.__exp_dict.get(group_name)
        if exp_group is None:
            return
        for exp in exp_group.list():
            exp.execute(content_dict)

    def execute_all_exp_group(self, content_dict: dict):
        for group in self.__exp_dict.values():
            for exp in group.list():
                exp.execute(content_dict)

    def calc_name_values(self, content_dict: dict):
        for k, v in self.__name_value_dict.items():
            if k == "":
                continue
            if type(v) is str and v != "" and v[0] == "$":
                value = self.__dictionary.get_var_value(v, content_dict)
                if value is not None:
                    content_dict[k] = value
                    continue
            content_dict[k] = v

    def get_name_value(self, key: str, content_dict: dict):
        v = self.__name_value_dict.get(key)
        if v is None:
            return None
        if type(v) is str and v != "" and v[0] == "$":
            value = self.__dictionary.get_var_value(v, content_dict)
            if value is not None:
                return value
        return v


# compares
def more(l, r, context_dict):
    return l > r


def more_equal(l, r, context_dict):
    return l >= r


def equal(l, r, context_dict):
    return l == r


def less(l, r, context_dict):
    return l < r


def less_equal(l, r, context_dict):
    return l <= r


def not_equal(l, r, context_dict):
    return l != r


def between(v, begin_end, context_dict):
    if not type(begin_end) is list:
        return False
    if len(begin_end) != 2:
        return False
    return begin_end[0] <= v <= begin_end[1]


def not_between(v, begin_end, context_dict):
    if not type(begin_end) is list:
        return False
    if len(begin_end) != 2:
        return False
    return not between(v, begin_end)


def inn(v, arg_list, context_dict):
    if not type(arg_list) is list:
        return False
    return v in arg_list


def not_inn(v, arg_list, context_dict):
    if not type(arg_list) is list:
        return False
    return not inn(v, arg_list)


def has(v, e, context_dict):
    return inn(e, v)


def any(v, e, context_dict):
    if type(e) is list:
        for x in e:
            if inn(e, v):
                return True
    else:
        return inn(e, v)
    return False


def none(v, e, context_dict):
    if type(e) is list:
        for x in e:
            if inn(x, v):
                return False
        return True
    else:
        return not inn(e, v)
    return False


def contain(l, r, context_dict):
    if type(l) is str:
        return l.find(str(r)) >= 0
    if type(r) is list:
        for x in r:
            if x not in l:
                return False
        return True
    else:
        return inn(r, l)
    return False


def begin_with(l, r, context_dict):
    return str(l).find(str(r)) == 0


def end_with(l, r, context_dict):
    ls = str(l)
    rs = str(r)
    return ls.rfind(rs) == len(ls) - len(rs)


# assignment
def assign(l, r, ret_dict):
    ret_dict[l] = r


def add_assign(l, r, ret_dict):
    ret = ret_dict.get(l)
    if ret is None:
        ret_dict[l] = r
    else:
        ret_dict[l] = ret + r


def sub_assign(l, r, ret_dict):
    ret = ret_dict.get(l)
    if ret is None:
        ret_dict[l] = r
    else:
        ret_dict[l] = ret - r


def mul_assign(l, r, ret_dict):
    ret = ret_dict.get(l)
    if ret is None:
        ret_dict[l] = r
    else:
        ret_dict[l] = ret * r


def div_assign(l, r, ret_dict):
    ret = ret_dict.get(l)
    if ret is None:
        ret_dict[l] = r
    else:
        ret_dict[l] = ret / r


def mod_assign(l, r, ret_dict):
    ret = ret_dict.get(l)
    if ret is None:
        ret_dict[l] = r
    else:
        ret_dict[l] = ret % r


# variables
def datetime(context_dict):
    import time
    tm = time.localtime(time.time())
    return "%04d-%02d-%02d %02d:%02d:%02d" % (tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec)


def date(context_dict):
    import time
    tm = time.localtime(time.time())
    return "%04d-%02d-%02d" % (tm.tm_year, tm.tm_mon, tm.tm_mday)


def time(context_dict):
    import time
    tm = time.localtime(time.time())
    return "%02d:%02d:%02d" % (tm.tm_hour, tm.tm_min, tm.tm_sec)


def short_time(context_dict):
    import time
    tm = time.localtime(time.time())
    return "%02d:%02d" % (tm.tm_hour, tm.tm_min)


def year(context_dict):
    import time
    tm = time.localtime(time.time())
    return tm.tm_year


def month(context_dict):
    import time
    tm = time.localtime(time.time())
    return tm.tm_mon


def day(context_dict):
    import time
    tm = time.localtime(time.time())
    return tm.tm_mday


def hour(context_dict):
    import time
    tm = time.localtime(time.time())
    return tm.tm_hour


def minute(context_dict):
    import time
    tm = time.localtime(time.time())
    return tm.tm_min


def second(context_dict):
    import time
    tm = time.localtime(time.time())
    return tm.tm_sec


# [1,100]
def rand(context_dict):
    import random
    if type(context_dict) is dict:
        ret = context_dict.get("$__rand__")
        if ret is not None:
            return ret
    return int(random.random() * 100) + 1


# create default dictionary & register common variants/compares/assignments
DEFAULT_DICTIONARY = Dictionary()
DEFAULT_DICTIONARY.register_compare(">", more)
DEFAULT_DICTIONARY.register_compare(">=", more_equal)
DEFAULT_DICTIONARY.register_compare("=", equal)
DEFAULT_DICTIONARY.register_compare("<=", less_equal)
DEFAULT_DICTIONARY.register_compare("<", less)
DEFAULT_DICTIONARY.register_compare("!=", not_equal)
DEFAULT_DICTIONARY.register_compare("<>", not_equal)
DEFAULT_DICTIONARY.register_compare("between", between)
DEFAULT_DICTIONARY.register_compare("not between", not_between)
DEFAULT_DICTIONARY.register_compare("in", inn)
DEFAULT_DICTIONARY.register_compare("not in", not_inn)
DEFAULT_DICTIONARY.register_compare("has", has)
DEFAULT_DICTIONARY.register_compare("any", any)
DEFAULT_DICTIONARY.register_compare("none", none)
DEFAULT_DICTIONARY.register_compare("contain", contain)
DEFAULT_DICTIONARY.register_compare("^*", begin_with)
DEFAULT_DICTIONARY.register_compare("*$", end_with)

DEFAULT_DICTIONARY.register_assign("=", assign)
DEFAULT_DICTIONARY.register_assign("+=", add_assign)
DEFAULT_DICTIONARY.register_assign("-=", sub_assign)
DEFAULT_DICTIONARY.register_assign("*=", mul_assign)
DEFAULT_DICTIONARY.register_assign("/=", div_assign)
DEFAULT_DICTIONARY.register_assign("%=", mod_assign)

DEFAULT_DICTIONARY.register_var("$datetime", datetime)
DEFAULT_DICTIONARY.register_var("$date", date)
DEFAULT_DICTIONARY.register_var("$time", time)
DEFAULT_DICTIONARY.register_var("$stime", short_time)
DEFAULT_DICTIONARY.register_var("$year", year)
DEFAULT_DICTIONARY.register_var("$month", month)
DEFAULT_DICTIONARY.register_var("$day", day)
DEFAULT_DICTIONARY.register_var("$hour", hour)
DEFAULT_DICTIONARY.register_var("$minute", minute)
DEFAULT_DICTIONARY.register_var("$second", second)
DEFAULT_DICTIONARY.register_var("$rand", rand)
