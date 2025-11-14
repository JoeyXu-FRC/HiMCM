from dataclasses import dataclass
from enum import Enum
from typing import Optional

class RoomState(Enum):
    unknown = 1,
    waiting = 2,
    safe = 3,
    NA = 4

class Location:
    """Represents a Location with a number of people."""
    is_exit: bool = False
    is_hallway: bool = False    
    label: str = ""
    def __init__(self, label: str, is_exit: bool,  is_hallway: bool):
        self.is_exit = is_exit
        self.is_hallway = is_hallway
        self.label = label
        self.person_list = {}

    def get_max_velocity(self) -> Optional[int]:
        """Returns the minimum velocity of people in the location, or None if empty."""
        if not self.person_list:
            return None
        return min(p.velocity for p in self.person_list.values())

class Room(Location):
    """Represents a Room with a number of people and an exploration time (in seconds)."""
    explore_time: int = 1 # Default exploration time is 1 (time unit)
    state: RoomState = RoomState.unknown
    size: int = 1

    def __init__(self, label: str, is_exit: bool,  is_hallway: bool, size : int, explore_time : int, person_list: dict):
        super().__init__(label, is_exit,  is_hallway)
        self.size = size
        self.person_list = person_list
        self.explore_time = explore_time
       
        if is_exit or is_hallway:
            self.state = RoomState.NA
        else:
            self.state = RoomState.unknown

class Edge():
    u: Location
    v: Location
    weight: int

    def __init__(self, u: Location, v: Location, weight: int = 1):
        self.u = u
        self.v = v
        self.weight = weight