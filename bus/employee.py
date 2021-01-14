from bus.baseentity import BaseEntity


class Employee(BaseEntity):
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
