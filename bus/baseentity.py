import time

import pymysql

from pyutil.entity import Entity


class BaseEntity(Entity):
    def __init__(self, table_name: str, key_field_list: list):
        Entity.__init__(self, table_name, key_field_list)

    def _before_insert(self, conn, entity: dict):
        entity["c_user"] = self.login_entry.__dict__.get("id")
        entity["c_time"] = int(time.time())

    def _before_update(self, conn, entity: dict):
        entity["u_user"] = self.login_entry.__dict__.get("id")
        entity["u_time"] = int(time.time())
