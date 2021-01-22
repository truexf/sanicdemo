import pyutil.entity
import pyutil.pymysqlutil as sql
from bus.baseentity import BaseEntity


class Company(BaseEntity):
    def _before_insert(self, conn, entity: dict):
        manager_id = entity.get("manager_id")
        if manager_id is not None and manager_id > 1:
            ret = sql.select(conn, "select count(1) as cnt from uhrs.employee where id = %s and disabled = 0",
                             manager_id)
            print(ret)
            if len(ret) == 0 or ret[0]["cnt"] == 0:
                raise pyutil.entity.KeyNotFound("manager id %s not found" % manager_id)

    def _before_delete(self, conn, entity: dict):
        id = entity.get("id")
        if id is not None and id > 0:
            ret = sql.select(conn,
                             "select count(1) as cnt from uhrs.company where id = %s and id in (select company_id from uhrs.department where disabled = 0)",
                             id)
            if ret is not None and ret[0]["cnt"] > 0:
                raise pyutil.entity.ChildNotEmpty("this company has valid department")


company = Company("uhrs.company", ["id"])
