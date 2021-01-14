import bus.baseentity


class EmployeeProject(bus.baseentity.BaseEntity):
    def _before_insert(self, conn, entity: dict):
        pass

    def _before_update(self, conn, entity: dict):
        pass


employee_project = EmployeeProject(table_name="uhrs.employee_project", key_field_list=["employee_id", "project_id"])
