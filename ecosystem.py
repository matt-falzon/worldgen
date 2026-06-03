import dataclasses
from typing import List
import random

@dataclasses.dataclass
class Animal:
    species: str
    x: int
    y: int
    preferred_biome: str
    migration_range: int
    food: int = 10

class Ecosystem:
    def __init__(self, world):
        self.world = world
        self.animals: List[Animal] = []

    def spawn_animals(self):
        for y in range(self.world.height):
            for x in range(self.world.width):
                terrain = self.world.grid[y][x]
                if terrain == 'F': # Forest
                    if random.random() < 0.05:
                        self.animals.append(Animal('Deer', x, y, 'F', 2))
                elif terrain == 'M': # Mountain
                    if random.random() < 0.02:
                        self.animals.append(Animal('Bear', x, y, 'F', 1))
                elif terrain == 'S': # Water
                    if random.random() < 0.03:
                        self.animals.append(Animal('Fish', x, y, 'S', 0))
                elif terrain == 'G': # Grass
                    if random.random() < 0.02:
                        self.animals.append(Animal('Bird', x, y, 'G', 5))

    def simulate_season(self, season: str):
        for animal in self.animals:
            # Hibernation
            if animal.species == 'Bear' and season == 'Winter':
                continue

            # Migration
            target_biome = animal.preferred_biome
            if animal.species == 'Deer' and season == 'Winter':
                target_biome = 'F'
            
            # Simple move
            dx = random.randint(-animal.migration_range, animal.migration_range)
            dy = random.randint(-animal.migration_range, animal.migration_range)
            new_x = max(0, min(self.world.width - 1, animal.x + dx))
            new_y = max(0, min(self.world.height - 1, animal.y + dy))
            
            # Check if better
            if self.world.grid[new_y][new_x] == target_biome:
                animal.x, animal.y = new_x, new_y

    def render_overlay(self, world_render: str) -> str:
        render_lines = world_render.split('\n')
        for animal in self.animals:
            if 0 <= animal.y < len(render_lines):
                emoji = {
                    'Deer': '🦌',
                    'Bear': '🐻',
                    'Fish': '🐟',
                    'Bird': '🐦',
                }.get(animal.species, '?')
                
                line = render_lines[animal.y]
                # Try to replace 1 character with the emoji
                if animal.x < len(line):
                    render_lines[animal.y] = line[:animal.x] + emoji + line[animal.x+1:]
        return '\n'.join(render_lines)
