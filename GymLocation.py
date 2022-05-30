from __future__ import annotations
from typing import TypedDict, Type
from enum import Enum
from uuid import uuid4
import random
from datetime import time

from Database import Database
from TimeSlot import TimeSlot
from util import get_similarity

from wtforms import (
    Form,
    StringField,
    SelectField,
    FloatField,
    TextAreaField,
    Field,
    validators,
)
from wtforms.widgets import HiddenInput


class Coordinates(TypedDict):
    lng: float
    lat: float


class CapacityLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class GymLocation:
    db: Database[GymLocation] = Database("gym_locations")

    @staticmethod
    def get(_id: str):
        return GymLocation.db.get(_id)

    @staticmethod
    def set(_id: str, gym_location: GymLocation):
        return GymLocation.db.set(_id, gym_location)

    @staticmethod
    def get_all():
        return list(GymLocation.db.dict().values())

    @staticmethod
    def filter_by_name(query: str):
        def weight_func(value: GymLocation):
            similarity = get_similarity(value.name, query)
            print(value.name, query, similarity)
            return similarity
        return GymLocation.db.sorted_filter(weight_func)

    def __init__(
            self,
            name: str,
            address: str,
            description: str,
            coordinates: Coordinates,
            capacity_level: CapacityLevel
    ):
        self.id = str(uuid4())
        self.name = name
        self.address = address
        self.description = description
        self.coordinates = coordinates
        self.capacity_level = capacity_level

        GymLocation.db.set(self.id, self)

        # Create default time slots
        start_hour = 10
        weekday_duration = 5
        weekend_duration = 3
        for day in range(7):
            for i in range((day < 5 and weekday_duration or weekend_duration) + 1):
                time_slot_time = time(start_hour + i)
                time_slot = TimeSlot(self.id, day, time_slot_time, random.random() < 0.8, day < 5 and 5 or 10)

    def __str__(self):
        return self.name


def generate_random_locations():
    # only generate locations if there are none
    if len(GymLocation.db.dict()) > 0:
        return

    # generate random locations
    random_addresses = [
        "Alexandra Hill",
        "Bukit Merah",
        "City Terminals",
        "Henderson Hill",
        "Kampong Tiong Bahru",
        "Loyang East",
        "Paya Lebar",
        "Simei",
        "Tampines East"
    ]

    for i in range(len(random_addresses)):
        lng = random.uniform(103.69599334671034, 103.9026049920435)
        lat = random.uniform(1.3278364433159737, 1.3987125240902714)
        address = random_addresses[i]
        gym_location = GymLocation(
            f"{address.split(' ')[0]} {random.choice(['Fitness', 'Center', 'Complex'])}",
            address,
            f"This gym is from {address}, it has good equipment!",
            Coordinates(lng=lng, lat=lat),
            random.choice([CapacityLevel.LOW, CapacityLevel.MEDIUM, CapacityLevel.HIGH])
        )


def text_field(field: Type[Field], label, min_length, max_length):
    kwargs = {
        "label": label,
        "validators": [validators.Length(min=min_length, max=max_length), validators.DataRequired()],
        "render_kw": {
            "minlength": min_length,
            "maxlength": max_length,
        }
    }

    return field(**kwargs)


class CreateGymLocationForm(Form):
    id = StringField(widget=HiddenInput())
    name = text_field(StringField, "Name", 3, 50)
    address = text_field(StringField, "Address", 3, 50)
    description = text_field(TextAreaField, "Description", 3, 200)
    lng = FloatField(widget=HiddenInput())
    lat = FloatField(widget=HiddenInput())
    capacity_level = SelectField("Capacity Level", choices=[
        (capacity_level.value, capacity_level.name) for capacity_level in CapacityLevel
    ], validators=[validators.DataRequired()])
