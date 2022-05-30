from __future__ import annotations
from typing import List

from datetime import datetime
from uuid import uuid4

from Database import Database
from GymLocation import GymLocation
from TimeSlot import TimeSlot
from User import User
from util import get_nearest_date_from_day


class BookedGymSlot:
    db: Database[BookedGymSlot] = Database("gym_slot_details")

    @staticmethod
    def filter_by_user(user_id: str) -> List[BookedGymSlot]:
        booked_gym_slots = []
        all_booked_gym_slots = list(BookedGymSlot.db.dict().values())
        for booked_slot in all_booked_gym_slots:
            if booked_slot.user_id == user_id:
                booked_gym_slots.append(booked_slot)
        return booked_gym_slots

    @staticmethod
    def filter_by_time_slot(time_slot_id: str) -> List[BookedGymSlot]:
        booked_slots = []
        for booked_slot in BookedGymSlot.db.dict().values():
            if booked_slot.time_slot_id == time_slot_id:
                booked_slots.append(booked_slot)
        return booked_slots

    def __init__(self, user_id, gym_id, time_slot_id, paid=True):
        self.id = str(uuid4())
        self.user_id = user_id
        self.gym_id = gym_id
        self.time_slot_id = time_slot_id
        self.date_submitted = datetime.now()

        # store amount paid as time slot price can change
        time_slot = TimeSlot.db.get(time_slot_id)
        if paid:
            self.amount_paid = time_slot.price
        else:
            self.amount_paid = 0

        self.booked_date = get_nearest_date_from_day(time_slot.day)

        BookedGymSlot.db.set(self.id, self)

    def get_gym_location(self):
        return GymLocation.db.get(self.gym_id)

    def get_time_slot(self):
        return TimeSlot.db.get(self.time_slot_id)

    def get_user(self):
        return User.db.get(self.user_id)
