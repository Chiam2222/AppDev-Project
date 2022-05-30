from __future__ import annotations
from typing import List, Dict, TYPE_CHECKING

from uuid import uuid4
from datetime import time, timedelta, datetime

from Database import Database

from flask import request
from wtforms import (
    Form,
    RadioField,
    SelectField,
    FloatField,
    validators
)
from wtforms.widgets.html5 import NumberInput


class TimeSlot:
    db: Database[TimeSlot] = Database("time_slots")

    @staticmethod
    def filter_by_gym(gym_id: str) -> Dict[str, TimeSlot]:
        time_slots = {}
        for time_slot in TimeSlot.db.dict().values():
            if time_slot.gym_id == gym_id:
                time_slots[time_slot.id] = time_slot
        return time_slots

    @staticmethod
    def sort_by_day(time_slots: List[TimeSlot]) -> Dict[int, List[TimeSlot]]:
        time_slots_by_day = {}
        for day in range(7):
            day_time_slots = []
            for time_slot in time_slots:
                if time_slot.day == day:
                    day_time_slots.append(time_slot)
            time_slots_by_day[day] = sorted(
                day_time_slots,
                key=lambda slot: (slot.time.hour * 60 + slot.time.minute) * 60 + slot.time.second
            )
        return time_slots_by_day

    def __init__(
            self,
            gym_id: str,
            day: int,
            _time: time,
            available: bool,
            price: float,
            duration: timedelta = timedelta(hours=1),
    ):
        self.id = str(uuid4())
        self.gym_id = gym_id
        self.day = day
        self.time = _time
        self.duration = duration
        self.available = available
        self.price = price

        TimeSlot.db.set(self.id, self)

    def get_end_time(self):
        return (datetime.combine(datetime.today(), self.time) + self.duration).time()

    def __str__(self):
        return f"{self.time.strftime('%H%M')}-{self.get_end_time().strftime('%H%M')}"


def available_field():
    return RadioField(
        "Status",
        choices=[("true", "Available"), ("false", "Unavailable")],
        validators=[validators.InputRequired()],
        coerce=lambda x: x == "true",
        default="true"
    )


def price_field():
    return FloatField(
        "Price ($)",
        widget=NumberInput(),
        validators=[
            validators.InputRequired(),
            validators.NumberRange(min=0, message="Please enter a number greater than 0.")
        ],
        default=5,
        render_kw={"min": 0, "step": 0.01}
    )


class UpdateTimeSlotForm(Form):
    price = price_field()
    available = available_field()


class CreateTimeSlotForm(Form):
    time = SelectField(
        "Time",
        validators=[validators.InputRequired()],
        coerce=int,
        description="You can only add time slots that haven't been added")
    price = price_field()
    available = available_field()

