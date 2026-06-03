import random
import math
from typing import List
from worldgen import World, GRASS, FOREST, CITY, INDUSTRIAL, PORT, SAND

class City:
    def __init__(self, name, x, y, population, radius):
        self.name = name
        self.x = x
        self.y = y
        self.population = population
        self.radius = radius
        self.founded = 0

class WorldSimulation(World):
    def __init__(self, width=120, height=40, seed=None):
        super().__init__(width, height, seed)
        self.simulation_cities: List[City] = []
        # Store as attribute directly to avoid type conflicts with base class

    def simulate_time_step(self, steps: int = 10):
        for step in range(steps):
            # 1. City expansion
            for city in self.simulation_cities:
                radius_int = int(city.radius)
                for r in range(radius_int + 1):
                    for dx in range(-r, r + 1):
                        for dy in range(-r, r + 1):
                            if dx**2 + dy**2 <= r**2:
                                nx, ny = city.x + dx, city.y + dy
                                if 0 <= nx < self.width and 0 <= ny < self.height:
                                    if self.grid[ny][nx] in (GRASS, FOREST):
                                        dist = math.hypot(dx, dy)
                                        chance = max(0, (city.radius - dist) / city.radius)
                                        if random.random() < chance:
                                            slum_char = 'L' 
                                            if dist < city.radius / 2:
                                                self.grid[ny][nx] = CITY
                                            elif dist < city.radius * 0.8:
                                                self.grid[ny][nx] = INDUSTRIAL
                                            else:
                                                self.grid[ny][nx] = slum_char
            # 2. Deforestation
            for y in range(self.height):
                for x in range(self.width):
                    if self.grid[y][x] == FOREST:
                        adjacent = False
                        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                if self.grid[ny][nx] in (CITY, INDUSTRIAL):
                                    adjacent = True
                                    break
                        if adjacent and random.random() < 0.05:
                            self.grid[y][x] = GRASS
            # 3. Population growth
            for city in self.simulation_cities:
                food = 0
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        nx, ny = city.x + dx, city.y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if self.grid[ny][nx] in (GRASS, FOREST):
                                food += 1
                city.population *= (1 + 0.01 * min(3, food / 5))

            # 2. Deforestation
            for y in range(self.height):
                for x in range(self.width):
                    if self.grid[y][x] == FOREST:
                        adjacent = False
                        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                if self.grid[ny][nx] in (CITY, INDUSTRIAL):
                                    adjacent = True
                                    break
                        if adjacent and random.random() < 0.05:
                            self.grid[y][x] = GRASS

            # 3. Population growth
            for city in self.cities:
                food = 0
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        nx, ny = city.x + dx, city.y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if self.grid[ny][nx] in (GRASS, FOREST):
                                food += 1
                city.population *= (1 + 0.01 * min(3, food / 5))

            # 4. Port expansion (simplified)
            # 5. Road building (simplified)

# Add city metadata storage as requested
# self.cities = [] -> list of dicts {name, x, y, population, radius, founded}
