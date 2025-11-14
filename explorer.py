from typing import List, Optional, Tuple
from graph import Graph
from location import Location  # Added import

INF = 10**9  # A large integer to represent infinity

class Explorer:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.dist, self.nxt, self.labels = self._get_distance_matrix()
        self.label_to_idx: dict = {label: i for i, label in enumerate(self.labels)}

    def _floyd_warshall(self) -> Tuple[List[List[int]], List[List[Optional[int]]]]:
        """
        Computes all-pairs shortest paths for the input undirected graph g (with integer-indexed nodes).
        Returns (dist, next):
          - dist[i][j] is the shortest distance (INF if not reachable)
          - next[i][j] is the index of the next hop for reconstructing the path from i to j (None if not reachable)
        """
        n = len(self.graph)
        dist: List[List[int]] = [[INF] * n for _ in range(n)]
        nxt: List[List[Optional[int]]] = [[None] * n for _ in range(n)]

        for i in range(n):
            dist[i][i] = 0
            nxt[i][i] = i

        for u, v, w in self.graph.edges():
            # If multiple edges exist, keep the one with the minimum weight
            if w < dist[u][v]:
                dist[u][v] = w
                dist[v][u] = w
                nxt[u][v] = v
                nxt[v][u] = u

        for k in range(n):
            for i in range(n):
                if dist[i][k] == INF:
                    continue
                for j in range(n):
                    nk = dist[i][k] + dist[k][j]
                    if nk < dist[i][j]:
                        dist[i][j] = nk
                        nxt[i][j] = nxt[i][k]

        return dist, nxt

    def _get_distance_matrix(self) -> Tuple[List[List[int]], List[List[Optional[int]]], List[str]]:
        """
        Calculates the shortest path matrix for the graph.
        Returns (dist, next, labels):
          - dist[i][j] is the shortest distance
          - next[i][j] is the next hop for reconstructing the path
          - labels[i] is the label of node i
        """
        dist, nxt = self._floyd_warshall()
        labels: List[str] = []
        for i in range(len(self.graph)):
            location = self.graph.get_location(i)
            lab = getattr(location, "label", "") or str(i)
            labels.append(lab)
        return dist, nxt, labels

    def reconstruct_path(self, u: int, v: int) -> List[int]:
        """
        Reconstructs the path from u to v (as a list of node indices) using the 'next' matrix from floyd_warshall.
        Returns an empty list if not reachable; returns [u] if u==v.
        """
        if self.nxt[u][v] is None:
            return []
        path = [u]
        while u != v:
            u = self.nxt[u][v]
            if u is None:
                return []
            path.append(u)
            # safety: prevent accidental infinite loops (should not happen in theory)
            if len(path) > len(self.nxt) + 5:
                break
        return path

    def get_path(self, label_start: str, label_end: str) -> Tuple[Optional[int], List[str]]:
        """
        Calculates the shortest distance and path between two nodes given their labels.
        Returns (distance, path_labels).
        If a label is not found or path does not exist, distance is None and path is empty.
        """
        if label_start not in self.label_to_idx or label_end not in self.label_to_idx:
            return None, []

        u = self.label_to_idx[label_start]
        v = self.label_to_idx[label_end]

        distance = self.dist[u][v]
        
        if distance == INF:
            return None, []

        path_indices = self.reconstruct_path(u, v)
        path_labels = [self.labels[i] for i in path_indices]

        return distance, path_labels

    def find_nearest_exit(self, start_label: str) -> Tuple[Optional[int], Optional[str], List[str]]:
        """
        Finds the nearest exit from a given starting label.
        Returns (distance, exit_label, path_labels).
        If the start label is not found or no path to an exit exists, returns (None, None, []).
        """
        if start_label not in self.label_to_idx:
            return None, None, []

        start_idx = self.label_to_idx[start_label]
        
        # Find all exit nodes
        exits = [i for i in range(len(self.graph)) if getattr(self.graph.get_location(i), "is_exit", False)]
        
        if not exits:
            return None, None, []

        min_dist = INF
        best_exit = -1
        for exit_node in exits:
            if self.dist[start_idx][exit_node] < min_dist:
                min_dist = self.dist[start_idx][exit_node]
                best_exit = exit_node
        
        if best_exit != -1 and min_dist != INF:
            path_idx = self.reconstruct_path(start_idx, best_exit)
            path_labels = [self.labels[i] for i in path_idx]
            return min_dist, self.labels[best_exit], path_labels
        
        return None, None, []

    def print_distance_matrix(self) -> None:
        """Prints the shortest path distance matrix and an example path."""
        print("labels:", self.labels)
        for i, row in enumerate(self.dist):
            row_str = ["INF" if x == INF else str(int(x)) for x in row]
            print(f"{self.labels[i]:>4}:", row_str)

        # Example: Find a path from TL to any exit
        if "TL" in self.label_to_idx:
            a = self.label_to_idx["TL"]
            # All nodes marked as exits
            exits = [i for i in range(len(self.graph)) if getattr(self.graph.get_location(i), "is_exit", False)]
            if exits:
                # Find the nearest exit
                min_dist = INF
                best_exit = -1
                for exit_node in exits:
                    if self.dist[a][exit_node] < min_dist:
                        min_dist = self.dist[a][exit_node]
                        best_exit = exit_node
                
                if best_exit != -1:
                    path_idx = self.reconstruct_path(a, best_exit)
                    if path_idx:
                        print(f"Path TL -> {self.labels[best_exit]} (nearest exit) indices:", path_idx)
                        print(f"Path TL -> {self.labels[best_exit]} labels:", [self.labels[i] for i in path_idx])
                    else:
                        print("Path from TL to the nearest exit is not reachable")
                else:
                    print("All exits are unreachable from TL")
            else:
                print("No rooms marked as exits in the graph")
        else:
            print("No room with label 'TL' in the graph to show a path example")

    def get_location_by_label(self, label: str) -> Optional[Location]:
        """
        Translates a location label to its corresponding Location object.
        Returns the Location object or None if the label is not found.
        """
        if label in self.label_to_idx:
            idx = self.label_to_idx[label]
            return self.graph.get_location(idx)
        return None

# Simple example: run this file from the project root to see the results
if __name__ == "__main__":
    from drawer import load_basic_floor
    graph = load_basic_floor('Figure1_building_structure.json')
    explorer = Explorer(graph)
    explorer.print_distance_matrix()

    # Example for get_path
    print("\n--- Get Path Example ---")
    start_node = "TL"
    end_node = "EXIT_R"
    distance, path = explorer.get_path(start_node, end_node)
    if distance is not None:
        print(f"Shortest distance from {start_node} to {end_node}: {distance}")
        print(f"Path: {' -> '.join(path)}")
    else:
        print(f"No path found from {start_node} to {end_node}")

    # Example for find_nearest_exit
    print("\n--- Find Nearest Exit Example ---")
    start_node_exit_search = "TM"
    distance, exit_label, path = explorer.find_nearest_exit(start_node_exit_search)
    if distance is not None:
        print(f"Nearest exit from {start_node_exit_search} is {exit_label} with distance: {distance}")
        print(f"Path: {' -> '.join(path)}")
    else:
        print(f"No path to an exit found from {start_node_exit_search}")

    # Example for get_location_by_label
    print("\n--- Get Location by Label Example ---")
    label_to_find = "TR"
    location_obj = explorer.get_location_by_label(label_to_find)
    if location_obj:
        print(f"Found location for label '{label_to_find}': {location_obj}")
        print(f"  - Is exit: {location_obj.is_exit}")
        print(f"  - Is hallway: {location_obj.is_hallway}")
        if hasattr(location_obj, 'state'):
             print(f"  - State: {location_obj.state.name}")
    else:
        print(f"Could not find location for label '{label_to_find}'")

