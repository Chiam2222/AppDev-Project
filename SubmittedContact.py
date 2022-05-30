# Bryan
# - admins can reply, so need to have some sort of replies attribute
# - need to know the user who submitted, so a user_id attribute
# - needs attributes for the user’s submitted input (their feedback text and rating)
# - anything else
from __future__ import annotations
from Database import Database
from uuid import uuid4

class SubmittedContact:
    db: Database[SubmittedContact] = Database("submitted_contact")
    count_id = 0
    def __init__(self, first_name, last_name, region, email, phone_no, category, reply):
        SubmittedContact.count_id += 1
        self.__id = str(uuid4())
        self.__user_id = ''
        self.__first_name = first_name
        self.__last_name = last_name
        self.__region = region
        self.__email = email
        self.__phone_no = phone_no
        self.__category = category
        self.__reply = reply
        self.__admin_reply = ""
        SubmittedContact.db.set(self.__id, self)

    def get_user_id(self):
        return self.__user_id
    def get_first_name(self):
        return self.__first_name
    def get_last_name(self):
        return self.__last_name
    def get_region(self):
        return self.__region
    def get_email(self):
        return  self.__email
    def get_phone_no(self):
        return self.__phone_no
    def get_category(self):
        return self.__category
    def get_reply(self):
        return self.__reply
    def get_id(self):
        return self.__id
    def get_admin_reply(self):
        return self.__admin_reply

    def set_first_name(self, first_name):
        self.__first_name = first_name
    def set_last_name(self, last_name):
        self.__last_name = last_name
    def set_region(self, region):
        self.__region = region
    def set_email(self, email):
        self.__email = email
    def set_phone_no(self, phone_no):
        self.__phone_no = phone_no
    def set_category(self, category):
        self.__category = category
    def set_reply(self, reply):
        self.__reply = reply
    def set_admin_reply(self, admin_reply):
        self.__admin_reply = admin_reply
