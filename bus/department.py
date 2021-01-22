import pyutil.entity
import pyutil.pymysqlutil as sql
from bus.baseentity import BaseEntity


class Department(BaseEntity):
    def _before_insert(self, conn, entity: dict):
        company_id = entity.get("company_id")
        if company_id is None:
            raise pyutil.entity.KeyNotFound("company_id is null")
        ret = sql.select(conn, "select count(1) as cnt from uhrs.company where id = %s and disabled = 0", company_id)
        if len(ret) == 0 or ret[0]["cnt"] == 0:
            raise pyutil.entity.KeyNotFound("company_id %s not found" % company_id)
        manager_id = entity.get("manager_id")
        if manager_id is not None and manager_id > 1:
            ret = sql.select(conn,
                             "select count(1) as cnt from uhrs.employee where id = %s and company_id = %s and disabled = 0",
                             manager_id, company_id)
            if len(ret) == 0 or ret[0]["cnt"] == 0:
                raise pyutil.entity.KeyNotFound("manager_id %s not found" % manager_id)

    def _before_delete(self, conn, entity: dict):
        id = entity.get("id")
        if id is not None and id > 0:
            ret = sql.select(conn,
                             "select count(1) as cnt from uhrs.department where id = %s and id in (select department_id from uhrs.employee where disabled = 0)",
                             id)
            if ret is not None and ret[0]["cnt"] > 0:
                raise pyutil.entity.ChildNotEmpty("this department has valid employees")


department = Department("uhrs.department", ["id"])
