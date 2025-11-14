from random import randint
from typing import Dict, Tuple, Optional
import webbrowser
import json
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
from graph import Graph
from location import Location, Room, RoomState
from person import Person

def create_locations_from_json(filepath: str) -> list[Location]:
    """Load and create a list of Location instances from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    locations = []
    edges = []
    for location_data in data:
        if location_data["type"] == "EDGE":
            edges.append((
                location_data["u"],
                location_data["v"],
                location_data["weight"]
            ))
            continue

        person_list_data = location_data.get("person_list", [])
        person_dict = {}
        for p_data in person_list_data:
            # The person ID from JSON is used as the key in the dictionary
            person = Person(p_data["id"], p_data["velocity"])
            person_dict[p_data["id"]] = person
            
        label = location_data["label"]
        is_exit=location_data["type"] == "EXIT"
        is_hallway=location_data["type"] == "Hallway"
        if is_exit or is_hallway:
            location = Location(
                label,
                is_exit,
                is_hallway
            )
        else:
            location = Room(
                label,
                is_exit,
                is_hallway,
                size=location_data["size"],
                explore_time=location_data["explore_time"],
                person_list=person_dict
        )

        locations.append(location)
    return locations, edges

def load_basic_floor(filepath: str) -> Graph:
    g = Graph()
    mapping: Dict[str, int] = {}
    
    locations, edges = create_locations_from_json(filepath)
    
    # Create Location nodes
    for l in locations:
        idx = g.add_location(l)
        mapping[l.label] = idx
    for e in edges:
        a, b, w = e
        if a in mapping and b in mapping:
            g.add_edge(mapping[a], mapping[b], weight=w)

    # Doors between offices and corresponding hallway sections (weight=1)
    edges = [
        ("TL", "H_L"),
        ("TM", "H_M"),
        ("TR", "H_R"),
        ("BL", "H_L"),
        ("BM", "H_M"),
        ("BR", "H_R")
    ]

    for a, b in edges:
        if a in mapping and b in mapping:
            w = g.get_location(mapping[a]).size
            g.add_edge(mapping[a], mapping[b], weight=w)

    return g

def draw_with_networkx(g: Graph, figsize=(8, 6)) -> None:
    """Draw a static graph with networkx + matplotlib. Node labels use Location.label."""
    G = nx.Graph()
    # Add nodes
    for v in g.vertices():
        G.add_node(v)
    # Add edges (with weights)
    for u, v, w in g.edges():
        G.add_edge(u, v, weight=w)
    # Node labels: display Location.label, number of people, exploration time, etc.
    label_map = {}
    for n in G.nodes():
        location = g.get_location(n)
        lab = getattr(location, "label", str(n))
        is_exit = getattr(location, "is_exit", False)
        is_hallway = getattr(location, "is_hallway", False)
        explore_time = None
        state = None
        size = getattr(location, "size", None)
        if isinstance(location, Room):
            explore_time = location.explore_time
            state = location.state.name
        person_count = len(getattr(location, "person_list", {}))
        max_velocity = location.get_max_velocity()
        # include size when available
        size_str = f" Size:{size}" if size is not None else ""
        label_map[n] = f"{lab}\nP:{person_count} Vmax:{max_velocity}\nT:{explore_time}{size_str}" + (f"\n{state}" if state else "") + ("\nEXIT" if is_exit else ("\nHALL" if is_hallway else ""))

    # Node colors: red for exits, green for hallways, blue for others
    colors = []
    for n in G.nodes():
        location = g.get_location(n)
        if getattr(location, "is_exit", False):
            colors.append("red")
        elif getattr(location, "is_hallway", False):
            colors.append("lightgreen")
        else:
            colors.append("skyblue")

    # Layout and drawing
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=figsize)
    nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=900)
    nx.draw_networkx_edges(G, pos)
    nx.draw_networkx_labels(G, pos, labels=label_map, font_size=9)
    # Optionally display weights on edges
    edge_labels = {(u, v): d for u, v, d in [(u, v, w) for u, v, w in g.edges()]}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.axis("off")
    plt.tight_layout()
    plt.show()


def draw_with_pyvis(g: Graph, path_labels: list = None, filename="graph.html") -> None:
    """Draw an interactive graph with pyvis. Node labels use Location.label."""
    net = Network(height="750px", width="100%", notebook=True, directed=False)

    label_to_id_map = {g.get_location(i).label: i for i in g.vertices()}
    path_ids = []
    if path_labels:
        path_ids = [label_to_id_map.get(label) for label in path_labels if label in label_to_id_map]

    # Add nodes
    for n in g.vertices():
        location = g.get_location(n)
        lab = getattr(location, "label", str(n))
        is_exit = getattr(location, "is_exit", False)
        is_hallway = getattr(location, "is_hallway", False)
        explore_time = 0
        state = None
        if isinstance(location, Room):
            explore_time = location.explore_time
            state = location.state.name
        person_count = len(getattr(location, "person_list", {}))
        max_velocity = location.get_max_velocity()
        size = getattr(location, "size", None)
        size_str = f"\nSize: {size}" if size is not None else ""

        if is_exit or is_hallway:
            title = f"Label: {lab}\nType: {'Exit' if is_exit else 'Hallway' }\n"
        else:
            title = f"Label: {lab}\nType: 'Room'\nExplore Time: {explore_time}\nPeople: {person_count}\nMax Velocity: {max_velocity}{size_str}"
            if state:
                title += f"\nState: {state}"
        
        color = "red" if is_exit else "lightgreen" if is_hallway else "skyblue"
        border_width = 1
        if path_ids and n in path_ids:
            if n == path_ids[0]: # Start node
                color = 'green'
            elif n == path_ids[-1]: # End node
                color = 'purple'
            else: # Intermediate path node
                color = 'orange'
            border_width = 3
        
        net.add_node(n, label=lab, title=title, color=color, borderWidth=border_width)

    # Add edges
    traversed_edges = {}
    if path_ids:
        for i in range(len(path_ids) - 1):
            u, v = tuple(sorted((path_ids[i], path_ids[i+1])))
            direction = 'to' if path_ids[i] < path_ids[i+1] else 'from'
            
            if (u,v) not in traversed_edges:
                traversed_edges[(u,v)] = set()
            traversed_edges[(u,v)].add(direction)

    for u, v, w in g.edges():
        edge_tuple = tuple(sorted((u, v)))
        
        if edge_tuple in traversed_edges:
            directions = traversed_edges[edge_tuple]
            arrow_style = None
            edge_color = 'orange'
            if len(directions) > 1:
                arrow_style = 'to, from'
            elif 'to' in directions:
                arrow_style = 'to'
            else: # 'from'
                arrow_style = 'from'

            if u > v: # Ensure consistent edge direction for pyvis
                u, v = v, u

            net.add_edge(u, v, value=w, title=str(w), color=edge_color, width=3, arrows=arrow_style)
        else:
            net.add_edge(u, v, value=w, title=str(w), color='#97C2FC', width=1)

    # Generate and open HTML
    try:
        net.show(filename)
        webbrowser.open(filename)
    except Exception as e:
        print(f"Could not open browser for {filename}: {e}")


def print_graph_cli(g):
    print("Graph summary:")
    print(f"Number of nodes: {len(g)}  Number of edges: {len(g.edges())}")
    print("Node information:")
    for i in g.vertices():
        location = g.get_location(i)
        
        size = getattr(location, "size", None)
        size_part = f" | size={size}" if size is not None else ""

        details = f"[{i}] label={location.label} | is_exit={location.is_exit} | is_hallway={location.is_hallway}{size_part}"
        
        person_count = len(getattr(location, "person_list", {}))
        max_velocity = location.get_max_velocity()
        
        if isinstance(location, Room):
            details += f" | explore_time={location.explore_time} | state={location.state.name} | person={person_count} | max_velocity={max_velocity}"
        else:
            details += f" | person={person_count} | max_velocity={max_velocity}"

        print(details)

        if hasattr(location, "person_list"):
            for pid, person in location.person_list.items():
                print(f"    Person {pid}: ID={person.ID} velocity={person.velocity}")

    print("\nAdjacency list:")
    for i in g.vertices():
        nbrs = [(v, g.weight(i, v)) for v in g.neighbors(i)]
        print(f"[{i}] -> {nbrs}")
        