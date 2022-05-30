from __future__ import annotations
from typing import Optional, List

from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import redirect, url_for, flash
from functools import wraps

from Membership import Membership
from Database import Database
from uuid import uuid4
from SlotDetails import SlotDetails


class User(UserMixin):
    db = Database("users")
    max_gym_slots = 3

    @staticmethod
    def load_user(user_id: str):
        return User.db.get(user_id)

    @staticmethod
    def update_user(user_id: str, user: User):
        return User.db.set(user_id, user)

    @staticmethod
    def get_by_username(username: str):
        username = username.lower()
        with User.db.open() as db:
            for user in db.values():
                if user.username == username:
                    return user

    @staticmethod
    def authenticate(username: str, password: str) -> Optional[User]:
        user = User.get_by_username(username)
        if user is not None:
            if check_password_hash(user.password, password):
                return user
        return None

    def __init__(self, username: str, email: str, password: str, is_admin: bool):
        self.user_id = str(uuid4())
        self.is_admin = is_admin
        self.username = username  # is lowered in setter
        self.email = email
        self.password = password  # is hashed in setter
        self.__contact_id_list = []
        self.__slot_id_list = []
        membership = Membership("NIL")
        membership_id = membership.get_id()
        self.__membership_id = membership_id

        User.db.set(self.user_id, self)

    @property
    def is_admin(self) -> bool:
        return self.__is_admin

    @is_admin.setter
    def is_admin(self, is_admin):
        self.__is_admin = is_admin

    @property
    def username(self) -> str:
        return self.__username

    @username.setter
    def username(self, username):
        self.__username = username.lower()

    @property
    def email(self) -> str:
        return self.__email

    @email.setter
    def email(self, email):
        self.__email = email.lower()

    @property
    def password(self) -> str:
        return self.__password

    @password.setter
    def password(self, password):
        self.__password = generate_password_hash(password)

    @property
    def membership_id(self) -> str:
        return self.__membership_id

    @membership_id.setter
    def membership_id(self, membership_id):
        self.__membership_id = membership_id

    def get_membership(self) -> Membership:
        return Membership.db.get(self.membership_id)

    @property
    def contact_id_list(self) -> List[str]:
        return self.__contact_id_list

    def add_contact_id(self, contact_id):
        self.__contact_id_list.append(contact_id)
        User.db.set(self.get_id(), self)

    @property
    def slot_id_list(self) -> List[str]:
        return self.__slot_id_list

    def add_slot_id(self, slot_id):
        self.__slot_id_list.append(slot_id)
        User.db.set(self.get_id(), self)

    def remove_slot_id(self, slot_id):
        self.__slot_id_list.remove(slot_id)
        User.db.set(self.get_id(), self)

    def get_gym_slot_count(self) -> int:
        gym_count = 0
        for slot_id in self.slot_id_list:
            slot = SlotDetails.db.get(slot_id)
            if slot.get_type() == 'gym':
                gym_count += 1
        return gym_count

    def is_gym_maxed(self) -> bool:
        return self.get_gym_slot_count() >= User.max_gym_slots

    def get_id(self) -> str:
        return self.user_id

    def __str__(self):
        return f"[{self.user_id}] {self.username}, {self.email}, {self.password}"


def create_admin_user(username, password):
    user = User(username, "", password, True)
    return user


def generate_admin_user():
    admin_exists = False
    for user in User.db.dict().values():
        if user.is_admin:
            admin_exists = True
            break

    if not admin_exists:
        create_admin_user("admin", "123456")


current_user: User = current_user


def admin_required(func):
    @wraps(func)
    def admin_required_func(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Unauthorized access", "error")
            return redirect(url_for("profile"))
        return func(*args, **kwargs)
    return admin_required_func

