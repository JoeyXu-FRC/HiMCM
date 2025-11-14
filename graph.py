from typing import Dict, Iterable, List, Optional, Tuple, Union
from location import Location

Index = int
Edge = Tuple[Index, Index, int]

class Graph:
    """
    An undirected graph implemented with an adjacency list.
    Vertices are Location objects, internally represented by integer indices.
    Initialization:
      - locations: Can be an int (to create that many default Location instances) or an iterable of Location instances.
      - E: A set of edges, where elements are (u, v) or (u, v, w). u/v can be indices (int) or Location instances.
    Storage:
      - self.locations: List[Location]     - List of vertices, where the index is the vertex ID.
      - self._adj: Dict[int, Dict[int, int]]  - Adjacency list, storing integer weights.
    """
    def __init__(self, locations: Optional[Union[int, Iterable[Location]]] = None, E: Optional[Iterable[Tuple]] = None):
        self.locations: List[Location] = []
        self._adj: Dict[Index, Dict[Index, int]] = {}

        if locations is None:
            pass
        elif isinstance(locations, int):
            for _ in range(locations):
                self.add_location(Location())
        else:
            for r in locations:
                if not isinstance(r, Location):
                    raise TypeError("locations iterable must contain Location instances")
                self.add_location(r)

        if E:
            for e in E:
                if len(e) == 2:
                    u, v = e
                    self.add_edge(u, v)
                elif len(e) == 3:
                    u, v, w = e
                    self.add_edge(u, v, weight=w)
                else:
                    raise ValueError("Edges should be in the format (u, v) or (u, v, w)")

    # --- Vertex-related methods ---
    def add_location(self, location: Optional[Location] = None) -> Index:
        """Adds a location (or creates a default one if not provided) and returns its index."""
        if location is None:
            location = Location()
        self.locations.append(location)
        idx = len(self.locations) - 1
        self._adj.setdefault(idx, {})
        return idx

    def get_location(self, idx: Index) -> Location:
        return self.locations[idx]

    def location_index(self, item: Union[Index, Location]) -> Index:
        """Returns the index if an index is passed; returns the index of a Location instance if a Location is passed (matched by object identity)."""
        if isinstance(item, int):
            return item
        for i, r in enumerate(self.locations):
            if r is item:
                return i
        raise ValueError("Location instance not found in graph")

    # --- Edge-related methods ---
    def add_edge(self, u: Union[Index, Location], v: Union[Index, Location], weight: int = 1) -> None:
        """Adds an undirected edge u--v. u/v can be an index or a Location instance. Weight is an integer."""
        ui = self.location_index(u) if not isinstance(u, int) else u
        vi = self.location_index(v) if not isinstance(v, int) else v
        # Automatically ensure indices exist
        max_idx = max(ui, vi)
        while len(self.locations) <= max_idx:
            self.add_location(Location())
        self._adj.setdefault(ui, {})
        self._adj.setdefault(vi, {})
        self._adj[ui][vi] = int(weight)
        self._adj[vi][ui] = int(weight)

    def remove_edge(self, u: Union[Index, Location], v: Union[Index, Location]) -> None:
        ui = self.location_index(u) if not isinstance(u, int) else u
        vi = self.location_index(v) if not isinstance(v, int) else v
        if ui in self._adj and vi in self._adj[ui]:
            del self._adj[ui][vi]
        if vi in self._adj and ui in self._adj[vi]:
            del self._adj[vi][ui]

    def has_edge(self, u: Union[Index, Location], v: Union[Index, Location]) -> bool:
        ui = self.location_index(u) if not isinstance(u, int) else u
        vi = self.location_index(v) if not isinstance(v, int) else v
        return ui in self._adj and vi in self._adj[ui]

    def neighbors(self, v: Union[Index, Location]) -> List[Index]:
        vi = self.location_index(v) if not isinstance(v, int) else v
        return list(self._adj.get(vi, {}).keys())

    def weight(self, u: Union[Index, Location], v: Union[Index, Location]) -> Optional[int]:
        ui = self.location_index(u) if not isinstance(u, int) else u
        vi = self.location_index(v) if not isinstance(v, int) else v
        w = self._adj.get(ui, {}).get(vi)
        return int(w) if w is not None else None

    # --- Queries ---
    def vertices(self) -> List[Index]:
        return list(range(len(self.locations)))

    def locations_list(self) -> List[Location]:
        return list(self.locations)

    def edges(self) -> List[Edge]:
        out: List[Edge] = []
        seen = set()
        for u, nbrs in self._adj.items():
            for v, w in nbrs.items():
                key = (u, v) if u <= v else (v, u)
                if key in seen:
                    continue
                seen.add(key)
                out.append((key[0], key[1], int(w)))
        return out

    def degree(self, v: Union[Index, Location]) -> int:
        vi = self.location_index(v) if not isinstance(v, int) else v
        return len(self._adj.get(vi, {}))

    def __len__(self) -> int:
        return len(self.locations)

    def __contains__(self, item: Union[Index, Location]) -> bool:
        if isinstance(item, int):
            return 0 <= item < len(self.locations)
        try:
            self.location_index(item)
            return True
        except ValueError:
            return False

    def __repr__(self) -> str:
        return f"<Undirected Graph | locations={len(self.locations)} | E={len(self.edges())}>"

    def get_neighbour(self, location: Union[Index, Location]) -> List[Location]:
        """Return the neighboring Location objects for the given vertex.

        `location` may be an integer index or a Location instance. The result
        is a list of Location instances corresponding to adjacent vertices.
        """
        vi = self.location_index(location) if not isinstance(location, int) else location
        return [self.get_location(i) for i in self.neighbors(vi)]