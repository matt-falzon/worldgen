#!/usr/bin/env python3
"""
Trade Routes Module
Cities trade goods based on local resources. Optimal paths are calculated
using Dijkstra's algorithm with terrain-based movement costs.

Terrain costs reflect how difficult it is to travel across each terrain type.
Mountains and water are expensive/impassable, while roads and plains are cheap.
"""

import heapq
import math
import random
from typing import Dict, List, Tuple, Optional, Set

# --- Terrain types (mirrored from worldgen.py for standalone use) ---
WATER_DEEP = "D"
WATER_SHALLOW = "S"
SAND = "A"
GRASS = "G"
FOREST = "F"
MOUNTAIN = "M"
SNOW = "N"
CITY = "C"
ROAD = "R"
PARK = "P"
INDUSTRIAL = "I"
PORT = "O"
SEASIDE = "B"
SWAMP = "W"
JUNGLE = "J"
RIVER = "U"
DELTA = "L"

# --- Terrain movement costs for trade caravans ---
# Higher cost = harder/slower to traverse
TERRAIN_COST = {
    WATER_DEEP: None,       # impassable
    WATER_SHALLOW: 20,      # very hard (shallow wading)
    SAND: 3,                # slow but passable
    GRASS: 1,               # ideal terrain
    FOREST: 4,              # dense, slow
    MOUNTAIN: 10,           # steep, dangerous
    SNOW: 8,                # cold, slow
    CITY: 1,                # through a city
    ROAD: 1,               # built for travel — cheapest
    PARK: 1,                # maintained land
    INDUSTRIAL: 2,          # somewhat passable
    PORT: 1,                # port area
    SEASIDE: 2,             # beach
    SWAMP: 7,               # boggy, very slow
    JUNGLE: 6,              # thick vegetation
    RIVER: 5,               # must ford or find crossing
    DELTA: 4,               # marshy
}

# --- Trade goods and which terrains produce them ---
GOODS_PRODUCTION = {
    "grain": {GRASS, PARK},          # Plains and parks grow grain
    "wood": {FOREST, JUNGLE},        # Forests provide timber
    "iron": {MOUNTAIN},              # Mountains have mines
    "fish": {WATER_SHALLOW, SAND, PORT, DELTA, SEASIDE},  # Coastal/water goods
    "herbs": {FOREST, SWAMP},        # Forests and swamps have medicinal herbs
    "salt": {SAND, SEASIDE},         # Salt flats and coastal evaporation
    "stone": {MOUNTAIN, SNOW},       # Quarrying stone
    "spices": {JUNGLE, SWAMP},       # Exotic jungle/swamp produce
    "furs": {SNOW, MOUNTAIN},        # Cold climate animal furs
    "gems": {MOUNTAIN},              # Rare mountain gems
}

# Reverse map: terrain -> list of goods produced
TERRAIN_GOODS: Dict[str, List[str]] = {}
for good, terrains in GOODS_PRODUCTION.items():
    for terrain in terrains:
        TERRAIN_GOODS.setdefault(terrain, []).append(good)

# Goods that cities always want (base demand)
BASE_DEMAND = {"grain", "iron", "salt", "wood"}

TRADE_ROUTE_CHAR = "╳"
TRADE_ROUTE_COLOR = "\033[95m"  # Bright magenta


class CityResources:
    """Tracks what a city produces and needs based on surrounding terrain."""

    def __init__(self, name: str, x: int, y: int, grid, radius: int = 8):
        self.name = name
        self.x = x
        self.y = y
        self.radius = radius
        self.production: Dict[str, int] = {}  # good -> amount produced
        self.demand: Dict[str, int] = {}       # good -> amount needed
        self._analyze_surroundings(grid)

    def _analyze_surroundings(self, grid):
        """Scan terrain around the city to determine resource production."""
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0

        terrain_counts: Dict[str, int] = {}
        for dy in range(-self.radius, self.radius + 1):
            for dx in range(-self.radius, self.radius + 1):
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    dist = math.hypot(dx, dy)
                    if dist <= self.radius:
                        terrain = grid[ny][nx]
                        terrain_counts[terrain] = terrain_counts.get(terrain, 0) + 1

        # Production based on terrain counts
        for good, producing_terrains in GOODS_PRODUCTION.items():
            total = sum(terrain_counts.get(t, 0) for t in producing_terrains)
            self.production[good] = max(1, total)  # At least 1 of anything found

        # Demand: cities need base goods, more if they lack local production
        for good in BASE_DEMAND:
            local = self.production.get(good, 0)
            if local < 5:
                self.demand[good] = 10 - local  # High demand if low production
            else:
                self.demand[good] = max(1, 10 - local)

        # Luxury goods demand (randomized based on city wealth)
        luxury_goods = {"spices", "gems", "furs"}
        for good in luxury_goods:
            if random.random() < 0.6:
                self.demand.setdefault(good, random.randint(1, 5))

    def surplus(self) -> Dict[str, int]:
        """Return goods this city has in excess."""
        return {
            good: amt - self.demand.get(good, 0)
            for good, amt in self.production.items()
            if amt > self.demand.get(good, 0)
        }

    def needs(self) -> Dict[str, int]:
        """Return goods this city needs (demand not met by production)."""
        return {
            good: need - self.production.get(good, 0)
            for good, need in self.demand.items()
            if need > self.production.get(good, 0)
        }


def dijkstra(
    start: Tuple[int, int],
    goal: Tuple[int, int],
    grid: List[List[str]],
    impassable: Optional[Set[str]] = None,
) -> Optional[Tuple[List[Tuple[int, int]], int]]:
    """
    Find shortest path between two points using Dijkstra's algorithm
    with terrain-based movement costs.

    Returns:
        (path, cost) if a path exists, None otherwise.
        path is a list of (x, y) coordinates from start to goal inclusive.
    """
    if impassable is None:
        impassable = {WATER_DEEP}

    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    # Validate start and goal
    if not (0 <= start[0] < width and 0 <= start[1] < height):
        return None
    if not (0 <= goal[0] < width and 0 <= goal[1] < height):
        return None

    # Priority queue: (cost, counter, x, y)
    # counter breaks ties and avoids comparing tuples
    counter = 0
    pq = [(0, counter, start[0], start[1])]
    visited = set()
    came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
    cost_so_far: Dict[Tuple[int, int], int] = {start: 0}

    # 8-directional movement
    directions = [
        (1, 0), (-1, 0), (0, 1), (0, -1),
        (1, 1), (-1, -1), (1, -1), (-1, 1),
    ]

    while pq:
        current_cost, _, cx, cy = heapq.heappop(pq)
        pos = (cx, cy)

        if pos in visited:
            continue
        visited.add(pos)

        if pos == goal:
            # Reconstruct path
            path = [goal]
            while path[-1] != start:
                path.append(came_from[path[-1]])
            path.reverse()
            return path, current_cost

        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            neighbor = (nx, ny)

            if neighbor in visited:
                continue
            if not (0 <= nx < width and 0 <= ny < height):
                continue

            terrain = grid[ny][nx]
            move_cost = TERRAIN_COST.get(terrain)

            if move_cost is None:  # impassable
                continue
            if terrain in impassable:
                continue

            # Diagonal movement costs more
            if dx != 0 and dy != 0:
                move_cost = int(move_cost * 1.414)

            new_cost = current_cost + move_cost
            if new_cost < cost_so_far.get(neighbor, float("inf")):
                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = pos
                counter += 1
                heapq.heappush(pq, (new_cost, counter, nx, ny))

    return None  # No path found


def compute_trade_routes(
    world_grid: List[List[str]],
    cities: List[Tuple[int, int, str]],
    max_routes: int = 10,
) -> List[dict]:
    """
    Compute trade routes between cities based on complementary resources.

    For each pair of cities, check if one has surplus goods the other needs.
    Use Dijkstra to find optimal path through terrain.

    Returns list of trade route dicts:
    {
        "from": city_name,
        "to": city_name,
        "goods": [good_names],
        "path": [(x, y), ...],
        "cost": int,
        "value": int,  # estimated trade value
    }
    """
    # Build resource profiles for all cities
    resource_map: Dict[str, CityResources] = {}
    for x, y, name in cities:
        resource_map[name] = CityResources(name, x, y, world_grid)

    routes = []
    city_names = [name for _, _, name in cities]

    for i, name_a in enumerate(city_names):
        for j, name_b in enumerate(city_names):
            if i >= j:
                continue

            res_a = resource_map[name_a]
            res_b = resource_map[name_b]

            # What A can sell to B
            a_sells = []
            for good, amt in res_a.surplus().items():
                if good in res_b.needs():
                    a_sells.append(good)

            # What B can sell to A
            b_sells = []
            for good, amt in res_b.surplus().items():
                if good in res_a.needs():
                    b_sells.append(good)

            # Only create route if there's mutual trade benefit
            if not a_sells and not b_sells:
                continue

            # Find path
            xa, ya, _ = next(c for c in cities if c[2] == name_a)
            xb, yb, _ = next(c for c in cities if c[2] == name_b)

            result = dijkstra((xa, ya), (xb, yb), world_grid)
            if result is None:
                continue

            path, cost = result
            goods_traded = list(set(a_sells + b_sells))

            # Trade value: number of complementary goods * path quality
            value = len(goods_traded) * 100 // max(cost, 1)

            routes.append({
                "from": name_a,
                "to": name_b,
                "goods": goods_traded,
                "path": path,
                "cost": cost,
                "value": value,
            })

    # Sort by value (best trades first), limit to max_routes
    routes.sort(key=lambda r: r["value"], reverse=True)
    return routes[:max_routes]


def render_trade_route(
    grid: List[List[str]],
    path: List[Tuple[int, int]],
    route_char: str = TRADE_ROUTE_CHAR,
) -> List[List[str]]:
    """
    Render a trade route overlay on the grid.
    Returns a new grid with route markers placed.
    Does NOT modify the original grid.
    """
    # Deep copy grid
    overlay = [row[:] for row in grid]

    for x, y in path:
        # Don't overwrite cities or ports
        if overlay[y][x] not in (CITY, PORT):
            overlay[y][x] = route_char

    return overlay


def render_trade_stats(routes: List[dict]) -> str:
    """Generate a text summary of active trade routes."""
    if not routes:
        return "  No trade routes established."

    lines = ["\n  Trade Routes:"]
    for i, route in enumerate(routes, 1):
        goods_str = ", ".join(route["goods"][:3])
        if len(route["goods"]) > 3:
            goods_str += f" (+{len(route['goods']) - 3})"
        lines.append(
            f"    {i}. {route['from']} <-> {route['to']}: "
            f"[{goods_str}] (cost: {route['cost']}, value: {route['value']})"
        )
    return "\n".join(lines)
