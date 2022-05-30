from typing import Generic, TypeVar, Optional, Callable, List, Dict
import shelve

T = TypeVar("T")


# to do: generic type
class Database(Generic[T]):
    def __init__(self, name: str):
        self.name = name

    def open(self):
        return shelve.open(f"databases/{self.name}")

    def get(self, key: str) -> Optional[T]:
        with self.open() as db:
            return db.get(key)

    def set(self, key: str, value: T):
        with self.open() as db:
            db[key] = value

    def pop(self, key: str):
        with self.open() as db:
            return db.pop(key)

    def dict(self) -> Dict[str, T]:
        with self.open() as db:
            return dict(db)

    def sorted_filter(self, weight_func: Callable[[T], float]) -> List[T]:
        results = []
        with self.open() as db:
            for value in db.values():
                weight = weight_func(value)
                if weight > 0:
                    results.append(value)
        return sorted(results, key=lambda _value: weight_func(_value), reverse=True)
