from difflib import ndiff
from datetime import datetime, timedelta


def levenshtein_distance(str1, str2):
    counter = {"+": 0, "-": 0}
    distance = 0
    for edit_code, *_ in ndiff(str1, str2):
        if edit_code == " ":
            distance += max(counter.values())
            counter = {"+": 0, "-": 0}
        else:
            counter[edit_code] += 1
    distance += max(counter.values())
    return distance


def get_similarity(a, b):
    return (len(a) - levenshtein_distance(b, a)) / len(a)


def get_nearest_date_from_day(day: int) -> datetime:
    now = datetime.now()
    weekday = now.weekday()

    nearest_date = now + timedelta(days=day - weekday + (day < weekday and 7 or 0))
    return nearest_date
