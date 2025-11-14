from location import Location, Room, RoomState
from explorer import Explorer
from person import Person
import math
from typing import Optional

class Firefighter(Person):
    location : Location = None
    expolorer_helper: Explorer = None

    def __init__(self, ID, velocity, explore_helper):
        super().__init__(ID, velocity)
        self.explorer_helper = explore_helper
        self.person_list = {}

    def setPos(self, label):
        location = self.explorer_helper.get_location_by_label(label)
        if not location or not isinstance(location, Location):
            return 0, self.location.label
        self.location  = location

    def max_velocity(self):        
        if len(self.person_list) == 0:
            return self.velocity
        return min(self.velocity, min(p.velocity for p in self.person_list.values()) or self.velocity)
    
    def moveTo(self, label):
        t = 0
        path_labels = [self.location.label]
        
        destination = self.explorer_helper.get_location_by_label(label)
        if not destination or not isinstance(destination, Location):
            return t, path_labels

        if self.location == destination:
            return t, path_labels

        distance, path_labels = self.explorer_helper.get_path(self.location.label, label)
        if distance is None:
            return 0, [self.location.label]

        t += math.ceil(distance / self.max_velocity()) 

        self.location = destination
        
        return t, path_labels

    def exploreRoom(self, room_label: str) -> int:
        t = 0

        path_labels = [self.location.label]
        room = self.explorer_helper.get_location_by_label(room_label)
        if not room or not isinstance(room, Room):
            return 0, path_labels

        if self.location == room:
            return 0, self.location.label
        if room.state != RoomState.unknown:
            return 0,  path_labels
        
        # Move firefighter to the room if not already there
        distance, path_labels = self.explorer_helper.get_path(self.location.label, room.label)
        if distance is None:
            return 0,  path_labels
        
        t = math.ceil(distance / self.max_velocity())
        self.location = room        
            
        # Update room state after exploration
        if len(room.person_list) == 0:
            room.state = RoomState.safe
        else:
            room.state = RoomState.waiting
        
        return  t + room.explore_time, path_labels

    def rescueRoomToLocation(self, room_label: str, location_label: str) -> int:
        path_labels = [self.location.label]
        t = 0
        room = self.explorer_helper.get_location_by_label(room_label)
        if not room or not isinstance(room, Room) or room.state != RoomState.waiting:
            print("Room isn't in waiting for reseue.")
            return t, path_labels
        
        location =  self.explorer_helper.get_location_by_label(location_label)
        if not location or not isinstance(location, Location):
            return t, path_labels
        
        # Move firefighter to the room if not already there
        if self.location != room:
            # explorer.get_path expects labels; accept Location or label
            start_label = self.location.label if isinstance(self.location, Location) else self.location
            room_label = room.label if isinstance(room, Location) else room
            distance, path_labels = self.explorer_helper.get_path(start_label, room_label)
            if distance is None:
                return t, path_labels
            t = math.ceil(distance / self.max_velocity())
            self.location = room     
        
        if self.location == location:
            return t, path_labels
        
        start_label = self.location.label if isinstance(self.location, Location) else self.location
        location_label = location.label if isinstance(location, Location) else location
        distance, path_labels_2 = self.explorer_helper.get_path(start_label, location_label)
        path_labels = path_labels + path_labels_2[1:]
        t += math.ceil(distance / self.max_velocity())
        self.person_list.update(room.person_list)
        self.location = location
        room.person_list = {}
        room.state = RoomState.safe

        return t, path_labels

    def resecueRoomToNearestExit(self, room_label: str) -> int:
        path_labels = [self.location.label]
        t = 0
        room = self.explorer_helper.get_location_by_label(room_label)
        if not room or not isinstance(room, Room) or room.state != RoomState.waiting:
            print("Room isn't in waiting for reseue.")
            return t, path_labels
                
        # Move firefighter to the room if not already there
        if self.location != room:
            # explorer.get_path expects labels; accept Location or label
            start_label = self.location.label if isinstance(self.location, Location) else self.location
            room_label = room.label if isinstance(room, Location) else room
            distance, path_labels = self.explorer_helper.get_path(start_label, room_label)
            if distance is None:
                return t, path_labels
            
            t = math.ceil(distance / self.max_velocity())
            self.location = room     
        
        min_dist, exit_label, path_labels_2 = self.explorer_helper.find_nearest_exit(room.label)
        if min_dist is None:
            return t, path_labels
        t += math.ceil(min_dist / self.max_velocity()) 
        path_labels =  path_labels + path_labels_2[1:]
        self.person_list.update(room.person_list)
        self.location = self.explorer_helper.get_location_by_label(exit_label)
        room.person_list = {}
        room.state = RoomState.safe

        return t, path_labels
    
    def unload(self):
        if self.location and self.location.is_exit:
            self.person_list.clear()
        return 0, [self.location.label]