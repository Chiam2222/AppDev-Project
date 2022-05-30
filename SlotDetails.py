from __future__ import annotations
from uuid import uuid4

from Database import Database

class SlotDetails:
    db: Database[SlotDetails] = Database("slot_details")

    def __init__(self, _type, user_id):
        self.__id = str(uuid4())
        self.__user_id = user_id
        self.__type = _type

    def get_id(self):
        return self.__id
    def get_user_id(self):
        return self.__user_id
    def get_type(self):
        return self.__type

class ClassSlotDetails(SlotDetails):
    def __init__(self, user_id, class_selected, start_time, end_time, venue, date):
        super().__init__('class', user_id)
        self.__start_time = start_time
        self.__end_time = end_time
        self.__venue = venue
        self.__date = date
        self.__class_selected = class_selected
        SlotDetails.db.set(self.get_id(), self)

    def get_start_time(self):
        return self.__start_time
    def get_end_time(self):
        return self.__end_time
    def get_venue(self):
        return self.__venue
    def get_date(self):
        return self.__date
    def get_class_selected(self):
        return self.__class_selected

    def set_class_selected(self, class_selected):
        self.__class_selected = class_selected
    def set_venue(self, venue):
        self.__venue = venue
    def set_date(self, date):
        self.__date = date
