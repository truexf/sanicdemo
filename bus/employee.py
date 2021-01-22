import pyutil.entity
import pyutil.pymysqlutil as sql
from bus.baseentity import BaseEntity


class Employee(BaseEntity):
    def _field_filter(self, action: str, key: str):
        if key == "project_id_list":
            return False
        return True

    def _before_insert(self, conn, entity: dict):
        company_id = entity.get("company_id")
        if company_id is None:
            raise pyutil.entity.KeyNotFound("company_id is null")
        ret = sql.select(conn, "select count(1) as cnt from uhrs.company where id = %s and disabled = 0", company_id)
        if len(ret) == 0 or ret[0]["cnt"] == 0:
            raise pyutil.entity.KeyNotFound("company_id %s not found" % company_id)
        department_id = entity.get("department_id")
        if department_id is None:
            raise pyutil.entity.KeyNotFound("department_id is null")
        ret = sql.select(conn,
                         "select count(1) as cnt from uhrs.department where id = %s and company_id = %s and disabled = 0",
                         department_id, company_id)
        if len(ret) == 0 or ret[0]["cnt"] == 0:
            raise pyutil.entity.KeyNotFound("department_id %s not found" % department_id)

    def _after_insert(self, conn, entity: dict, effect_row_count: int, inserted_id: int):
        if effect_row_count <= 0 or inserted_id <= 0:
            return
        sql.execute(conn, "delete from uhrs.employee_project where employee_id = %s", inserted_id)
        project_id_list = entity.get("project_id_list")
        if project_id_list is not None and len(project_id_list) > 0:
            for id in project_id_list:
                sql.execute(conn, "insert ignore into uhrs.employee_project (employee_id, project_id) values (%s, %s)",
                            inserted_id, id)

    def _after_update(self, conn, entity: dict):
        id = entity.get("id")
        if id is None or id <= 0:
            return
        project_id_list = entity.get("project_id_list")
        sql.execute(conn, "delete from uhrs.employee_project where employee_id = %s", id)
        if project_id_list is not None and len(project_id_list) > 0:
            for prj_id in project_id_list:
                sql.execute(conn, "insert ignore into uhrs.employee_project (employee_id, project_id) values (%s, %s)",
                            id, prj_id)

    def _after_delete(self, conn, entity: dict):
        id = entity.get("id")
        if id is None or id <= 0:
            return
        sql.execute(conn, "delete from uhrs.employee_project where employee_id = %s", id)

    def _select_sql(self, entity: dict):
        project_id = entity.get("project_id")
        if project_id is None:
            return BaseEntity._select_sql(self, entity)
        else:
            where = ""
            where_values = []
            for k, v in entity.items():
                if v is None:
                    continue
                if where != "":
                    where += " and "
                if k != "project_id":
                    where = where + k + " = %s"
                    where_values.append(v)
                else:
                    where = where + ''' id in (select employee_id from uhrs.employee_project where project_id = %s)'''
                    where_values.append(v)
            sql = "select * from %s where %s" % (self._table_name, where)
            return sql, where_values


employee = Employee("uhrs.employee", ["id"])
