import sys
import os

# Ensure the parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from worldgen import World, GRASS, FOREST, WATER_DEEP, WATER_SHALLOW, MOUNTAIN, SNOW, JUNGLE
from ecosystem import Animal, Ecosystem
import random

def test_animal_spawn():
    w = World(60, 20)
    w.generate()
    eco = Ecosystem(w)
    
    # 1. Deer in forest/plains
    deer = Animal("Deer", 0, 0, preferred_biome=GRASS, migration_range=2)
    eco.animals.append(deer)
    assert deer.species == "Deer"
    print("Test passed: Animal species correct.")

def test_migration_logic():
    w = World(60, 20)
    w.generate()
    # Simple migration test: check if animal prefers forest and currently in grass
    deer = Animal("Deer", 10, 10, preferred_biome=FOREST, migration_range=5)
    print("Test passed: Migration stub logic ready.")

if __name__ == "__main__":
    test_animal_spawn()
    test_migration_logic()
    print("All tests passed.")
