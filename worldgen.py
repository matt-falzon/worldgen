#!/usr/bin/env python3
"""
Procedural World Generator
A cellular automaton that grows organic worlds with terrain, cities, and biomes.
Includes seasonal rendering and weather simulation.
"""

import random
import math
import sys
import time
import os
from typing import List, Tuple

# --- Perlin-ish noise (simplified value noise) ---

class SimplexNoise:
    """Simplified noise generator for terrain height maps."""

    def __init__(self, seed: int = None):
        self.seed = seed or random.randint(0, 2**31)
        random.seed(self.seed)
        size = 256
        self.perm = list(range(size))
        random.shuffle(self.perm)
        self.perm = self.perm + self.perm

    def _fade(self, t: float) -> float:
        return t * t * t * (t * (t * 6 - 15) + 10)

    def _lerp(self, a: float, b: float, t: float) -> float:
        return a + t * (b - a)

    def _grad(self, hash_val: int, x: float, y: float) -> float:
        h = hash_val & 3
        if h == 0:
            return x + y
        elif h == 1:
            return -x + y
        elif h == 2:
            return x - y
        else:
            return -x - y

    def noise2d(self, x: float, y: float) -> float:
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        x -= math.floor(x)
        y -= math.floor(y)
        u = self._fade(x)
        v = self._fade(y)
        a = self.perm[X] + Y
        aa = self.perm[a]
        ab = self.perm[a + 1]
        b = self.perm[X + 1] + Y
        ba = self.perm[b]
        bb = self.perm[b + 1]
        return self._lerp(
            self._lerp(self._grad(self.perm[aa], x, y),
                        self._grad(self.perm[ba], x - 1, y), u),
            self._lerp(self._grad(self.perm[ab], x, y - 1),
                        self._grad(self.perm[bb], x - 1, y - 1), u),
            v
        )

    def octave(self, x: float, y: float, octaves: int = 4, persistence: float = 0.5) -> float:
        total = 0.0
        frequency = 1.0
        amplitude = 1.0
        max_val = 0.0
        for _ in range(octaves):
            total += self.noise2d(x * frequency, y * frequency) * amplitude
            max_val += amplitude
            amplitude *= persistence
            frequency *= 2.0
        return total / max_val


# --- Terrain types ---

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

# River flow direction chars - chosen based on direction of flow
RIVER_CHARS = {
    (0, 1): "│",    # down
    (0, -1): "│",   # up
    (1, 0): "─",    # right
    (-1, 0): "─",   # left
    (1, 1): "/",    # down-right
    (-1, -1): "/",  # up-left
    (1, -1): "ˋ",   # up-right
    (-1, 1): "ˋ",   # down-left
}

TERRAIN_CHARS = {
    WATER_DEEP: "≈",
    WATER_SHALLOW: "~",
    SAND: "·",
    GRASS: "·",
    FOREST: "♣",
    MOUNTAIN: "▲",
    SNOW: "❄",
    CITY: "■",
    ROAD: "─",
    PARK: "☘",
    INDUSTRIAL: "▓",
    PORT: "⚓",
    SEASIDE: "░",
    SWAMP: "☼",
    JUNGLE: "♠",
    RIVER: "│",
    DELTA: "⊗",
}

# Terminal colors (ANSI)
COLORS = {
    WATER_DEEP: "\033[34m",
    WATER_SHALLOW: "\033[96m",
    SAND: "\033[33m",
    GRASS: "\033[32m",
    FOREST: "\033[92m",
    MOUNTAIN: "\033[37m",
    SNOW: "\033[97m",
    CITY: "\033[93m",
    ROAD: "\033[36m",
    PARK: "\033[92m",
    INDUSTRIAL: "\033[35m",
    PORT: "\033[91m",
    SEASIDE: "\033[33m",
    SWAMP: "\033[33m",
    JUNGLE: "\033[32m",
    RIVER: "\033[96m",
    DELTA: "\033[34m",
}

# Seasonal color overlays
SEASON_COLORS = {
    "Spring": {
        GRASS: "\033[92m",
        FOREST: "\033[32m",
        PARK: "\033[92m",
        SAND: "\033[33m",
    },
    "Summer": {
        GRASS: "\033[33m",
        FOREST: "\033[32m",
        PARK: "\033[33m",
        SAND: "\033[93m",
    },
    "Autumn": {
        GRASS: "\033[33m",
        FOREST: "\033[31m",
        PARK: "\033[33m",
        SAND: "\033[33m",
    },
    "Winter": {
        GRASS: "\033[37m",
        FOREST: "\033[36m",
        PARK: "\033[37m",
        SAND: "\033[37m",
    },
}

# Seasonal terrain chars
SEASON_CHARS = {
    "Spring": {
        GRASS: "·",
        FOREST: "♣",
        PARK: "☘",
    },
    "Summer": {
        GRASS: "·",
        FOREST: "♣",
        PARK: "☘",
    },
    "Autumn": {
        GRASS: "·",
        FOREST: "✾",
        PARK: "✾",
    },
    "Winter": {
        GRASS: "·",
        FOREST: "✧",
        PARK: "✧",
    },
}

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


class World:
    def __init__(self, width: int = 120, height: int = 40, seed: int = None):
        self.width = width
        self.height = height
        self.seed = seed or random.randint(0, 2**31)
        self.noise = SimplexNoise(self.seed)
        self.noise2 = SimplexNoise(self.seed + 1000)
        self.noise3 = SimplexNoise(self.seed + 2000)
        self.grid: List[List[str]] = []
        self.moisture: List[List[float]] = []
        self.temperature: List[List[float]] = []
        self.heightmap: List[List[float]] = []
        self.cities: List[Tuple[int, int, str]] = []
        self.population: int = 0

    def generate_heightmap(self):
        scale = 0.03
        self.heightmap = [
            [
                (self.noise.octave(x * scale, y * scale, octaves=5, persistence=0.5) + 1.0) / 2.0
                for x in range(self.width)
            ]
            for y in range(self.height)
        ]

    def generate_moisture(self):
        scale = 0.04
        self.moisture = [
            [
                (self.noise2.octave(x * scale, y * scale, octaves=4, persistence=0.5) + 1.0) / 2.0
                for x in range(self.width)
            ]
            for y in range(self.height)
        ]

    def generate_temperature(self):
        scale = 0.02
        self.temperature = [
            [
                (self.noise3.octave(x * scale, y * scale, octaves=3, persistence=0.5) + 1.0) / 2.0
                for x in range(self.width)
            ]
            for y in range(self.height)
        ]

    def classify_terrain(self):
        self.grid = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                h = self.heightmap[y][x]
                m = self.moisture[y][x]
                t = self.temperature[y][x]

                if h < 0.25:
                    row.append(WATER_DEEP)
                elif h < 0.33:
                    row.append(WATER_SHALLOW)
                elif h < 0.35 and m > 0.55:
                    row.append(SWAMP)
                elif h < 0.38:
                    row.append(SAND)
                elif h > 0.72:
                    if t < 0.35:
                        row.append(SNOW)
                    else:
                        row.append(MOUNTAIN)
                elif h > 0.55 and t < 0.35:
                    row.append(SNOW)
                elif m > 0.60 and t > 0.55:
                    row.append(JUNGLE)
                elif m > 0.50 and t > 0.40:
                    row.append(FOREST)
                elif m < 0.28 and t > 0.50:
                    row.append(SAND)
                else:
                    row.append(GRASS)
            self.grid.append(row)

    def find_flat_grass_regions(self, min_size: int = 8) -> List[List[Tuple[int, int]]]:
        """Find contiguous flat grass regions suitable for city placement."""
        visited = [[False] * self.width for _ in range(self.height)]
        regions = []

        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] != GRASS:
                    continue
                if visited[y][x]:
                    continue

                # BFS
                region = []
                queue = [(x, y)]
                visited[y][x] = True

                while queue:
                    cx, cy = queue.pop(0)
                    region.append((cx, cy))
                    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if not visited[ny][nx] and self.grid[ny][nx] == GRASS:
                                visited[ny][nx] = True
                                queue.append((nx, ny))

                if len(region) >= min_size:
                    regions.append(region)

        return regions

    def place_cities(self, max_cities: int = 12):
        regions = self.find_flat_grass_regions(min_size=10)
        random.shuffle(regions)
        regions.sort(key=len, reverse=True)

        city_names = [
            "Novara", "Kestrel", "Aethel", "Vostok", "Zephyr",
            "Meridian", "Sunder", "Luminar", "Oakhaven", "Briarwood",
            "Emberfall", "Tarnish", "Verdant", "Cinder", "Holloway",
            "Ironforge", "Ashvale", "Goldfield", "Stonehaven", "Ravenloft"
        ]
        random.shuffle(city_names)

        placed = []
        used_cells = set()

        for region in regions[:max_cities * 2]:
            if len(placed) >= max_cities:
                break

            # Check distance from already placed cities
            cx, cy = region[len(region) // 2]
            too_close = False
            for px, py, _ in placed:
                dist = math.hypot(cx - px, cy - py)
                if dist < 15:
                    too_close = True
                    break

            if too_close:
                continue

            # Check no overlap
            overlap = False
            for cell in region[:6]:
                if cell in used_cells:
                    overlap = True
                    break
            if overlap:
                continue

            # Place city
            city_size = min(6, len(region))
            for cell in region[:city_size]:
                self.grid[cell[1]][cell[0]] = CITY
                used_cells.add(cell)

            # Place parks adjacent to city
            for cell in region[city_size:city_size + 3]:
                if cell not in used_cells:
                    self.grid[cell[1]][cell[0]] = PARK
                    used_cells.add(cell)

            name = city_names[len(placed)]
            pop = random.randint(5000, 500000)
            self.population += pop
            placed.append((cx, cy, name))

        # Place some industrial zones near cities
        for cx, cy, _ in placed:
            for _ in range(3):
                dx = random.randint(-5, 5)
                dy = random.randint(-3, 3)
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.grid[ny][nx] in (GRASS, SAND):
                        self.grid[ny][nx] = INDUSTRIAL
                        break

        # Place ports near water
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == SAND:
                    # Check if adjacent to water
                    adjacent_water = False
                    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if self.grid[ny][nx] in (WATER_DEEP, WATER_SHALLOW):
                                adjacent_water = True
                                break
                    if adjacent_water:
                        # Check if near a city
                        near_city = False
                        for px, py, _ in placed:
                            if math.hypot(x - px, y - py) < 10:
                                near_city = True
                                break
                        if near_city and random.random() < 0.4:
                            self.grid[y][x] = PORT

        # Place some roads between nearby cities
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                x1, y1, _ = placed[i]
                x2, y2, _ = placed[j]
                dist = math.hypot(x2 - x1, y2 - y1)
                if dist < 35:
                    # Bresenham's line
                    dx = abs(x2 - x1)
                    dy = abs(y2 - y1)
                    sx = 1 if x1 < x2 else -1
                    sy = 1 if y1 < y2 else -1
                    err = dx - dy
                    cx, cy = x1, y1
                    while True:
                        if 0 <= cx < self.width and 0 <= cy < self.height:
                            if self.grid[cy][cx] in (GRASS, SAND, FOREST):
                                self.grid[cy][cx] = ROAD
                        if cx == x2 and cy == y2:
                            break
                        e2 = 2 * err
                        if e2 > -dy:
                            err -= dy
                            cx += sx
                        if e2 < dx:
                            err += dx
                            cy += sy

        self.cities = placed

    def generate_rivers(self, num_rivers: int = 5):
        # 1. Find potential sources
        sources = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] in (MOUNTAIN, SNOW):
                    sources.append((x, y, self.heightmap[y][x]))
        
        sources.sort(key=lambda s: s[2], reverse=True)
        sources = sources[:num_rivers * 3] # More than we strictly need
        
        rivers = []
        
        # 2. Trace rivers
        for sx, sy, _ in sources:
            if len(rivers) >= num_rivers: break
            
            path = [(sx, sy)]
            curr_x, curr_y = sx, sy
            visited = set([(sx, sy)])
            
            while True:
                # Find downhill
                best_neighbor = None
                lowest_h = self.heightmap[curr_y][curr_x]
                
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                    nx, ny = curr_x + dx, curr_y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if (nx, ny) not in visited:
                            h = self.heightmap[ny][nx]
                            if h < lowest_h:
                                lowest_h = h
                                best_neighbor = (nx, ny, dx, dy)
                
                if not best_neighbor: # Reached local minimum / coast
                    break
                    
                nx, ny, dx, dy = best_neighbor
                
                # Check termination
                if self.grid[ny][nx] in (WATER_DEEP, WATER_SHALLOW):
                    # Finalize river and delta
                    path.append((nx, ny))
                    rivers.append(path)
                    break
                
                if self.grid[ny][nx] == RIVER: # Merge
                    path.append((nx, ny))
                    rivers.append(path)
                    break

                # Continue
                path.append((nx, ny))
                visited.add((nx, ny))
                curr_x, curr_y = nx, ny
                if len(path) > 100: break # Max length
        
        # 3. Apply to grid
        for path in rivers:
            if len(path) < 5: continue
            for i in range(len(path) - 1):
                x, y = path[i]
                if self.grid[y][x] not in (WATER_DEEP, WATER_SHALLOW, CITY, PORT, RIVER):
                    self.grid[y][x] = RIVER
            # Delta at the end
            x, y = path[-1]
            if self.grid[y][x] in (SAND, GRASS):
                self.grid[y][x] = DELTA

    def generate(self):
        """Full world generation pipeline."""
        self.generate_heightmap()
        self.generate_moisture()
        self.generate_temperature()
        self.classify_terrain()
        self.place_cities()
        self.generate_rivers()

    def get_sun_angle(self, hour: float) -> float:
        """Returns the angle of the sun in radians: 0 at noon."""
        return (hour - 12.0) / 12.0 * math.pi

    def get_lighting_multiplier(self, hour: float) -> float:
        """Returns a multiplier (0.0–1.0) for brightness based on hour."""
        # Noon (12) = 1.0, Midnight (0/24) = 0.1
        # Use cosine for smooth transition
        angle = (hour - 12.0) / 12.0 * math.pi
        return (math.cos(angle) + 1.1) / 2.1

    def render(self, colored: bool = True) -> str:
        """Render the world to a string."""
        lines = []
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                terrain = self.grid[y][x]
                char = TERRAIN_CHARS.get(terrain, "?")
                if colored:
                    color = COLORS.get(terrain, "")
                    line += f"{color}{char}{RESET}"
                else:
                    line += char
            lines.append(line)
        return "\n".join(lines)

    def render_with_time(self, hour: float, moon_phase: float = 0.5, colored: bool = True) -> str:
        """Render the world with day/night lighting, stars, city lights, and shadows."""
        is_night = hour < 6.0 or hour > 18.0
        
        # Calculate shadow map for mountains (simple gradient)
        shadows = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        if not is_night:
            sun_dir = -self.get_sun_angle(hour) # Opposite: if sun is in East, shadow falls West
            for y in range(self.height):
                for x in range(self.width):
                    if self.grid[y][x] == MOUNTAIN:
                        shadow_len = int(self.heightmap[y][x] * 5)
                        for i in range(1, shadow_len + 1):
                            nx, ny = x + i * int(math.cos(sun_dir)), y + i * int(math.sin(sun_dir))
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                shadows[ny][nx] = max(shadows[ny][nx], 0.3)
        
        lines = []
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                terrain = self.grid[y][x]
                char = TERRAIN_CHARS.get(terrain, "?")
                is_water = terrain in (WATER_DEEP, WATER_SHALLOW, SWAMP)
                is_mountain = terrain == MOUNTAIN
                
                # Apply night lighting
                if is_night:
                    char = "·" if terrain == GRASS else char # Simplify terrain at night
                    color = "\033[90m" # Dim
                    
                    # City lights
                    if terrain == CITY or terrain == INDUSTRIAL:
                        color = "\033[93m"
                    elif terrain == ROAD:
                        char = "."
                        color = "\033[90m"
                        
                    # Moon brightness
                    moon_mult = moon_phase * 0.5
                    color = color if moon_mult > 0.2 else "\033[30m"
                        
                    # Stars in the sky (water/mountains area)
                    # Simple noise check for star placement
                    if not is_water and terrain != MOUNTAIN and random.random() < 0.05:
                        char = "."
                        color = "\033[97m"
                else:
                    color = COLORS.get(terrain, "\033[0m")
                    # Apply shadow overlay
                    if shadows[y][x] > 0:
                        color = "\033[30m"
                        char = "/" if is_mountain else "."
                    
                if colored:
                    line += f"{color}{char}{RESET}"
                else:
                    line += char
            lines.append(line)
        return "\n".join(lines)

    def render_seasonal(self, season: str, colored: bool = True) -> str:
        """Render the world with seasonal colors and characters."""
        lines = []
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                terrain = self.grid[y][x]
                char = TERRAIN_CHARS.get(terrain, "?")
                color = COLORS.get(terrain, "")

                # Apply seasonal overrides
                if season in SEASON_CHARS and terrain in SEASON_CHARS[season]:
                    char = SEASON_CHARS[season][terrain]
                if season in SEASON_COLORS and terrain in SEASON_COLORS[season]:
                    color = SEASON_COLORS[season][terrain]

                # Winter snow overlay on grass
                if season == "Winter" and terrain == GRASS:
                    if random.random() < 0.15:
                        char = "❄"
                        color = "\033[97m"

                # Autumn leaf particles
                if season == "Autumn" and terrain == GRASS:
                    if random.random() < 0.08:
                        char = "✾"
                        color = "\033[31m"

                # Spring flowers
                if season == "Spring" and terrain == GRASS:
                    if random.random() < 0.1:
                        char = "❀"
                        color = "\033[95m"

                if colored:
                    line += f"{color}{char}{RESET}"
                else:
                    line += char
            lines.append(line)
        return "\n".join(lines)

    def render_weather(self, season: str, weather_type: str, colored: bool = True) -> str:
        """Render the world with weather effects overlaid."""
        weather_noise = SimplexNoise(self.seed + 9999)
        lines = []
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                terrain = self.grid[y][x]
                char = TERRAIN_CHARS.get(terrain, "?")
                color = COLORS.get(terrain, "")

                # Seasonal base
                if season in SEASON_CHARS and terrain in SEASON_CHARS[season]:
                    char = SEASON_CHARS[season][terrain]
                if season in SEASON_COLORS and terrain in SEASON_COLORS[season]:
                    color = SEASON_COLORS[season][terrain]

                # Weather overlay
                noise_val = weather_noise.noise2d(x * 0.1, y * 0.1)
                is_water = terrain in (WATER_DEEP, WATER_SHALLOW, SWAMP)

                if weather_type == "Rain":
                    if noise_val > 0.3 and not is_water:
                        char = "│"
                        color = "\033[36m"
                    elif is_water and noise_val > 0.2:
                        char = "◆"
                        color = "\033[96m"

                elif weather_type == "Storm":
                    if noise_val > 0.4:
                        char = "│"
                        color = "\033[36m"
                    elif noise_val > 0.6:
                        char = "⚡"
                        color = "\033[93m"
                    elif noise_val < -0.6 and random.random() < 0.3:
                        char = "⚡"
                        color = "\033[93m"
                    if is_water and noise_val > 0.1:
                        char = "◆"
                        color = "\033[96m"

                elif weather_type == "Snow":
                    if noise_val > 0.2 and not is_water:
                        char = "❄"
                        color = "\033[97m"
                    elif terrain == GRASS and noise_val > 0.4:
                        char = "❅"
                        color = "\033[97m"

                elif weather_type == "Fog":
                    fog_density = (noise_val + 1.0) / 2.0
                    if fog_density > 0.6:
                        char = "░"
                        color = "\033[90m"
                    elif fog_density > 0.45:
                        char = "▒"
                        color = "\033[90m"
                    elif fog_density > 0.35:
                        char = "▓"
                        color = "\033[30m"

                elif weather_type == "Clear":
                    if season == "Summer" and terrain == GRASS and random.random() < 0.02:
                        char = "✦"
                        color = "\033[93m"

                if colored:
                    line += f"{color}{char}{RESET}"
                else:
                    line += char
            lines.append(line)
        return "\n".join(lines)

    def render_legend(self) -> str:
        """Render a legend below the map."""
        items = [
            (WATER_DEEP, "Deep Water"),
            (WATER_SHALLOW, "Shallow"),
            (SAND, "Beach"),
            (GRASS, "Plains"),
            (FOREST, "Forest"),
            (MOUNTAIN, "Mountain"),
            (SNOW, "Snow"),
            (CITY, "City"),
            (ROAD, "Road"),
            (PARK, "Park"),
            (INDUSTRIAL, "Industry"),
            (PORT, "Port"),
            (RIVER, "River"),
            (DELTA, "Delta"),
        ]
        legend_lines = []
        for terrain, name in items:
            char = TERRAIN_CHARS[terrain]
            legend_lines.append(f"  {COLORS[terrain]}{char}{RESET} {name}")
        return "\n".join(legend_lines)

    def render_stats(self) -> str:
        """Render world statistics."""
        terrain_counts = {}
        for row in self.grid:
            for cell in row:
                terrain_counts[cell] = terrain_counts.get(cell, 0) + 1

        lines = []
        total_cells = self.width * self.height
        for terrain in [WATER_DEEP, WATER_SHALLOW, SAND, GRASS, FOREST, MOUNTAIN, SNOW, CITY, ROAD, PARK, INDUSTRIAL, PORT, RIVER, DELTA]:
            count = terrain_counts.get(terrain, 0)
            pct = count / total_cells * 100
            name = {
                WATER_DEEP: "Deep Water",
                WATER_SHALLOW: "Shallow Water",
                SAND: "Beach/Sand",
                GRASS: "Plains",
                FOREST: "Forest",
                MOUNTAIN: "Mountain",
                SNOW: "Snow Peak",
                CITY: "City Blocks",
                ROAD: "Roads",
                PARK: "Parks",
                INDUSTRIAL: "Industrial",
                PORT: "Ports",
                RIVER: "River",
                DELTA: "Delta",
            }.get(terrain, terrain)
            bar = "█" * int(pct / 2)
            lines.append(f"  {bar:<30} {name:>14}: {pct:5.1f}%")

        lines.append("")
        lines.append(f"  Total Population: {BOLD}{self.population:,}{RESET}")
        lines.append(f"  Cities: {BOLD}{len(self.cities)}{RESET}")
        lines.append(f"  World Seed: {BOLD}{self.seed}{RESET}")
        lines.append(f"  Dimensions: {self.width} × {self.height}")
        return "\n".join(lines)

    def render_city_list(self) -> str:
        """Render the list of cities."""
        if not self.cities:
            return "  No cities found."
        lines = ["  Cities:", "  " + "─" * 40]
        # Sort by proximity to center
        cx, cy = self.width / 2, self.height / 2
        for x, y, name in sorted(self.cities, key=lambda c: math.hypot(c[0] - cx, c[1] - cy)):
            pop = random.randint(10000, 300000)
            lines.append(f"    {COLORS[CITY]}■{RESET} {BOLD}{name:<15}{RESET} pop: {pop:>8,}")
        return "\n".join(lines)


def clear_screen():
    os.write(2, b"\033[2J\033[H")


def print_title():
    """Print an ASCII art title."""
    title = f"""
{BOLD}
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║   ███╗   ██╗███████╗██╗██████╗  █████╗  ██████╗███╗   ██╗║
    ║   ████╗  ██║██╔════╝██║██╔══██╗██╔══██╗██╔════╝ ████╗  ██║║
    ║   ██╔██╗ ██║█████╗  ██║██████╔╝███████║██║  ███╗██╔██╗ ██║║
    ║   ██║╚██╗██║██╔══╝  ██║██╔══██╗██╔══██║██║   ██║██║╚██╗██║║
    ║   ██║ ╚████║███████╗██║██║  ██║██║  ██║╚██████╔╝██║ ╚████║║
    ║   ╚═╝  ╚═══╝╚══════╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝║
    ║                                                          ║
    ║           P R O C E D U R A L   W O R L D               ║
    ║               G E N E R A T O R                         ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    {RESET}"""
    print(title)


def print_loading(steps: int = 5, duration: float = 0.3):
    """Animated loading bar."""
    for i in range(steps + 1):
        filled = "█" * i
        empty = "░" * (steps - i)
        pct = i / steps * 100
        line = f"\r  Generating world... [{filled}{empty}] {pct:3.0f}%"
        os.write(2, line.encode())
        os.write(2, b"\033[0G")
        time.sleep(duration)
    os.write(2, b"\n")


def generate_animated(world: World, steps: int = 5):
    """Show world generation step by step."""
    messages = [
        ("Carving terrain heightmap...", lambda: world.generate_heightmap()),
        ("Distributing moisture patterns...", lambda: world.generate_moisture()),
        ("Simulating temperature zones...", lambda: world.generate_temperature()),
        ("Classifying biomes...", lambda: world.classify_terrain()),
        ("Growing cities and roads...", lambda: world.place_cities()),
        ("Tracing rivers and deltas...", lambda: world.generate_rivers()),
    ]
    for i, (msg, fn) in enumerate(messages):
        bar_len = 40
        for j in range(bar_len + 1):
            filled = "▓" * j
            empty = "░" * (bar_len - j)
            pct = j / bar_len * 100
            line = f"\r  {msg:<40} [{filled}{empty}] {pct:3.0f}%"
            os.write(2, line.encode())
            os.write(2, b"\033[0G")
            time.sleep(0.02)
        fn()
        os.write(2, b"\n")


def show_world(world: World):
    """Display a fully generated world."""
    clear_screen()
    print_title()
    print()

    # Animated generation
    # Reset world for re-generation display
    world2 = World(world.width, world.height, world.seed)
    generate_animated(world2, steps=5)
    print()

    # Render map
    print(world2.render())
    print()

    # Render legend
    print(world2.render_legend())
    print()

    # Render stats
    print(world2.render_stats())
    print()

    # Render city list
    print(world2.render_city_list())
    print()
    print(f"\n  Tip: Use the seed {BOLD}{world2.seed}{RESET} to regenerate this exact world.")
    print(f"  {DIM}Press Ctrl+C to exit, or wait for the next generation...{RESET}")


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Procedural World Generator")
    parser.add_argument("--once", action="store_true", help="Generate a single world and exit")
    parser.add_argument("--seed", type=int, default=None, help="Use a specific seed")
    parser.add_argument("--width", type=int, default=120, help="World width (default: 120)")
    parser.add_argument("--height", type=int, default=40, help="World height (default: 40)")
    parser.add_argument("--plain", action="store_true", help="No color output")
    parser.add_argument("--noload", action="store_true", help="Skip animated loading bars")
    parser.add_argument("--seasons", action="store_true", help="Animate through seasons")
    return parser.parse_args()


def animate_seasons(world: World, cycles: int = 1, delay: float = 2.5):
    """Animate the world through all four seasons with weather."""
    seasons = ["Spring", "Summer", "Autumn", "Winter"]
    season_emojis = {"Spring": "🌸", "Summer": "☀️", "Autumn": "🍂", "Winter": "❄️"}
    season_weathers = {
        "Spring": [("Showers", "🌧️"), ("Clear", "🌤️"), ("Light Rain", "🌦️")],
        "Summer": [("Clear", "☀️"), ("Thunderstorm", "⛈️"), ("Heat Wave", "🔥")],
        "Autumn": [("Overcast", "🌥️"), ("Rain", "🌧️"), ("Fog", "🌫️")],
        "Winter": [("Snowfall", "❄️"), ("Blizzard", "🌨️"), ("Fog", "🌫️")],
    }
    weather_map = {
        "Showers": "Rain", "Clear": "Clear", "Light Rain": "Rain",
        "Thunderstorm": "Storm", "Heat Wave": "Clear",
        "Overcast": "Fog", "Rain": "Rain", "Fog": "Fog",
        "Snowfall": "Snow", "Blizzard": "Snow",
    }
    season_descriptions = {
        "Spring": "Flowers bloom, forests turn fresh green",
        "Summer": "Warm winds dry the plains golden",
        "Autumn": "Leaves turn crimson and amber",
        "Winter": "Snow blankets the land in silence",
    }

    for cycle in range(cycles):
        for season in seasons:
            weathers = season_weathers[season]
            for weather_name, weather_emoji in weathers:
                clear_screen()
                print_title()
                print()
                world2 = World(world.width, world.height, world.seed)
                world2.generate()
                header = f"  {BOLD}Cycle {cycle + 1}/{cycles}  —  {season}  {season_emojis[season]}  {weather_name}  {weather_emoji}{RESET}"
                print(header)
                print(f"  {DIM}{season_descriptions[season]}{RESET}")
                print()
                wtype = weather_map.get(weather_name, "Clear")
                print(world2.render_weather(season, wtype))
                print()
                print(world2.render_city_list())
                print()
                time.sleep(delay)


def main():
    args = parse_args()
    seed = args.seed or random.randint(0, 2**31)
    width = args.width
    height = args.height

    if args.seasons:
        world = World(width, height, seed)
        if args.noload:
            world.generate()
        else:
            generate_animated(world)
        print()
        animate_seasons(world, cycles=2, delay=3.0)
        print(f"\n  {BOLD}Seasons cycle complete.{RESET}")
        print()
        return

    if args.once:
        world = World(width, height, seed)
        if args.noload:
            world.generate()
        else:
            generate_animated(world)
        print()
        print(world.render(colored=not args.plain))
        print()
        print(world.render_legend())
        print()
        print(world.render_stats())
        print()
        print(world.render_city_list())
        print()
        return

    generation = 0
    while True:
        generation += 1
        current_seed = args.seed or random.randint(0, 2**31)
        world = World(width, height, current_seed)
        world.generate()
        show_world(world)

        try:
            for i in range(15, 0, -1):
                time.sleep(1)
                line = f"\r  Generating new world in {i}s... (Ctrl+C to stop)"
                os.write(2, line.encode())
                os.write(2, b"\033[0G")
            os.write(2, b"\n")
        except KeyboardInterrupt:
            print(f"\n  Generated {generation} world(s). Goodbye!")
            sys.exit(0)


def main():
    args = parse_args()
    seed = args.seed or random.randint(0, 2**31)
    width = args.width
    height = args.height

    if args.once:
        world = World(width, height, seed)
        if args.noload:
            world.generate()
        else:
            generate_animated(world)
        print()
        print(world.render(colored=not args.plain))
        print()
        print(world.render_legend())
        print()
        print(world.render_stats())
        print()
        print(world.render_city_list())
        print()
        return

    generation = 0
    while True:
        generation += 1
        current_seed = args.seed or random.randint(0, 2**31)
        world = World(width, height, current_seed)
        world.generate()
        show_world(world)

        try:
            for i in range(15, 0, -1):
                time.sleep(1)
                line = f"\r  Generating new world in {i}s... (Ctrl+C to stop)"
                os.write(2, line.encode())
                os.write(2, b"\033[0G")
            os.write(2, b"\n")
        except KeyboardInterrupt:
            print(f"\n  Generated {generation} world(s). Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()

def get_world():
    return World(120, 40)
