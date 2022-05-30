from __future__ import annotations
from Database import Database
from uuid import uuid4


class Membership():
    db: Database[Membership] = Database("membership")

    def __init__(self,tier_name):
        self.__id = str(uuid4())
        self.__tier_name = tier_name
        Membership.db.set(self.__id,self)

    def get_tier_name(self):
        return self.__tier_name

    def get_id(self):
        return self.__id

    def set_tier_name(self,tier_name):
        self.__tier_name = tier_name
