from drawer import *
from explorer import *
from firefighter import Firefighter
from collections import deque
from heapq import heappush, heappop

def test():
    graph = load_basic_floor('Figure1_building_structure.json')
    print_graph_cli(graph)

    explore_helper = Explorer(graph)
    explore_helper.print_distance_matrix()
    firefighter = Firefighter(100, 3, explore_helper)

    #Set fire fighter start point
    firefighter.setPos("EXIT_R") 

    #Explore room TR
    t, path_labels = firefighter.exploreRoom("TR")
    print("explore room TR")
    print("explore time:", t)
    print(f"Path: {' -> '.join(path_labels)}")     

    #Explort room TM
    t, path_labels = firefighter.exploreRoom("TM")    
    print("explore room TM")
    print("explore time:", t)    
    print(f"Path: {' -> '.join(path_labels)}")    

    #Explort room BM
    t, path_labels = firefighter.exploreRoom("BM")
    print("explore room BM")
    print("explore time:", t)
    print(f"Path: {' -> '.join(path_labels)}")  

    #Set fire fighter EXIT_L
    #Rescue room TM to H_M
    firefighter.setPos("EXIT_L")
    t, path_labels = firefighter.rescueRoomToLocation("TM", "H_M")    
    print("Rescue room TM to H_M")
    print("rescue time:", t)
    print(f"Path: {' -> '.join(path_labels)}")     

    #Move to EXIT_R
    t, path_labels = firefighter.moveTo("EXIT_R")
    print("Move to EXIT_R")
    print("Move time:", t)
    print(f"Path: {' -> '.join(path_labels)}")  
    
    #Set fire fighter EXIT_L
    #Rescue room TM to H_M
    firefighter.setPos("EXIT_R")
    t, path_labels = firefighter.resecueRoomToNearestExit("BM")
    print("Rescue room TM to nearest Exit")
    print("rescue time:", t)
    print(f"Path: {' -> '.join(path_labels)}")     

    firefighter.unload()

    draw_with_pyvis(graph, path_labels)
    
def rescue_building_1FF() -> int:
    total_time = 0
    graph = load_basic_floor('Figure1_building_structure.json')
    #print_graph_cli(graph)

    explore_helper = Explorer(graph)    
    firefighter = Firefighter(100, 5, explore_helper)
    firefighter.setPos("EXIT_R")

    # Phase 1: BFS exploration (discover rooms). Collect rooms that need rescue.
    start_label = "EXIT_R"
    start_idx = explore_helper.label_to_idx.get(start_label)
    path = [start_label]

    if start_idx is None:
        # fallback: traverse all locations if start not found
        queue = deque(range(len(graph)))
        visited = set()
    else:
        queue = deque([start_idx])
        visited = {start_idx}

    waiting_rooms = []

    print("Exploration Phase:")
    print("BFS exploration (discover rooms). Collect rooms that need rescue.")
    while queue:
        idx = queue.popleft()
        loc = graph.get_location(idx)

        # If it's a room and unknown, explore it
        if isinstance(loc, Room) and loc.state == RoomState.unknown:
            t, path_labels = firefighter.exploreRoom(loc.label)
            total_time += t
            if path_labels:
                print(f"\tExplored room {loc.label} in time {t}. Path: {' -> '.join(path_labels)}")

        # collect rooms that require rescue after exploration
        if isinstance(loc, Room) and loc.state == RoomState.waiting:
            waiting_rooms.append(loc.label)

        # Enqueue neighbors for BFS
        for nbr in graph.neighbors(idx):
            if nbr not in visited:
                visited.add(nbr)
                queue.append(nbr)

    # Phase 2: Perform rescues for all waiting rooms discovered in phase 1
    print("Perform rescues for all waiting rooms discovered in phase 1")
    for room_label in waiting_rooms:
        t, path_labels = firefighter.resecueRoomToNearestExit(room_label)
        firefighter.unload()
        total_time += t
        if path_labels:
            print(f"\tRescue room {room_label} in time {t}. Path: {' -> '.join(path_labels)}")
    
    # draw_with_pyvis(graph, path)

    return total_time

def rescue_building_2FF() -> int:
    total_time = 0
    graph = load_basic_floor('Figure1_building_structure.json')
    #print_graph_cli(graph)

    explore_helper = Explorer(graph)    
    # prepare two firefighters (indexes 0 and 1)
    firefighters = [Firefighter(1, 5, explore_helper), Firefighter(2, 5, explore_helper)]

    # find exit labels
    exit_labels = [graph.get_location(i).label for i in range(len(graph)) if getattr(graph.get_location(i), 'is_exit', False)]
    if not exit_labels:
        print("No exits found; aborting")
        return 0

    # assign starting exits (duplicate if only one)
    if len(exit_labels) == 1:
        start_labels = [exit_labels[0], exit_labels[0]]
    else:
        start_labels = [exit_labels[0], exit_labels[1]]

    firefighters[0].setPos(start_labels[0])
    firefighters[1].setPos(start_labels[1])

    # BFS queues for each firefighter (store indices)

    label_to_idx = explore_helper.label_to_idx
    queues = [deque(), deque()]
    visited = set()

    # initialize queues with starting indices
    for i, lbl in enumerate(start_labels):
        idx = label_to_idx.get(lbl)
        if idx is not None:
            queues[i].append(idx)
            visited.add(idx)

    # scheduler heap: (available_time, firefighter_index)
    heap = []
    heappush(heap, (0, 0))
    heappush(heap, (0, 1))
    last_time = [0, 0]

    def all_rooms_safe() -> bool:
        for loc in graph.locations:
            if isinstance(loc, Room) and loc.state != RoomState.safe:
                return False
        return True

    # run until all rooms safe or no more tasks
    while heap and not all_rooms_safe():
        cur_time, fi = heappop(heap)
        f = firefighters[fi]

        # get next target index from this firefighter's queue
        target_idx = None
        while queues[fi]:
            cand = queues[fi].popleft()
            if cand in visited:
                # already discovered by someone else
                continue
            target_idx = cand
            break

        if target_idx is None:
            # try to steal from the other queue: pick any undiscovered neighbor
            # If nothing, skip rescheduling
            # Enqueue any undiscovered neighbors of visited nodes to this queue
            for vi in range(len(graph)):
                if vi not in visited:
                    queues[fi].append(vi)
                    break
            if not queues[fi]:
                continue
            target_idx = queues[fi].popleft()

        # mark visited
        visited.add(target_idx)
        loc = graph.get_location(target_idx)

        # enqueue neighbors for this firefighter
        for nbr in graph.neighbors(target_idx):
            if nbr not in visited:
                queues[fi].append(nbr)

        # If it's a room and unknown -> explore
        if isinstance(loc, Room) and loc.state == RoomState.unknown:
            t, path_labels = f.exploreRoom(loc.label)
            if t is None:
                t = 0
            cur_time += t
            last_time[fi] = cur_time
            print(f"\tFirefighter {fi+1} explored room {loc.label} in time {t}. Path: {' -> '.join(path_labels)}")

        # If it's waiting -> rescue to nearest exit
        if isinstance(loc, Room) and loc.state == RoomState.waiting:
            t2, path_labels2 = f.resecueRoomToNearestExit(loc.label)
            if t2 is None:
                t2 = 0
            cur_time += t2
            last_time[fi] = cur_time
            # after rescue, unload if at exit
            f.unload()            
            print(f"\tFirefighter {fi+1} rescued room {loc.label} in time {t2}. Path: {' -> '.join(path_labels2)}")

        # schedule firefighter next available time
        heappush(heap, (cur_time, fi))

    total_time = max(last_time)
    # Optionally draw final graph (omitted path)
    # draw_with_pyvis(graph)

    return total_time

if __name__ == "__main__":
    test()

    print("Rescue building with 1 firefighter:")
    total_time_1FF = rescue_building_1FF()
    print(f"Total time with 1 firefighter: {total_time_1FF}\n")

    print("Rescue building with 2 firefighters:")
    total_time_2FF = rescue_building_2FF()
    print(f"Total time with 2 firefighters: {total_time_2FF}\n")
