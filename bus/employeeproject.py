import bus.baseentity
import pyutil.entity
import pyutil.pymysqlutil as sql


class EmployeeProject(bus.baseentity.BaseEntity):
    def _before_insert(self, conn, entity: dict):
        employee_id = entity.get("employee_id")
        project_id = entity.get("project_id")
        if employee_id is None:
            raise pyutil.entity.KeyNotFound("employee_id is null")
        if project_id is None:
            raise pyutil.entity.KeyNotFound("project_id is null")
        ret = sql.select(conn, "select count(1) as cnt from uhrs.employee where id = %s and disabled = 0", employee_id)
        if len(ret) == 0 or ret[0].cnt == 0:
            raise pyutil.entity.KeyNotFound("employee_id %s not found" % employee_id)
        ret = sql.select(conn, "select count(1) as cnt from uhrs.project where id = %s and disabled = 0", project_id)
        if len(ret) == 0 or ret[0].cnt == 0:
            raise pyutil.entity.KeyNotFound("employee_id %s not found" % project_id)

    def _before_update(self, conn, entity: dict):
        pass


employee_project = EmployeeProject(table_name="uhrs.employee_project", key_field_list=["employee_id", "project_id"])
