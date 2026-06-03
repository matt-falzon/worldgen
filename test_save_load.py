import json
import sys
import os
sys.path.insert(0, os.getcwd())
from worldgen import World
from ecosystem import Ecosystem

def test_persistence():
    w = World(60, 20, seed=12345)
    w.generate()
    eco = Ecosystem(w)
    eco.spawn_animals()
    
    w.save("test_world.json")
    with open("test_eco.json", "w") as f:
        json.dump(eco.to_dict(), f)
    
    w2 = World.load("test_world.json")
    with open("test_eco.json", "r") as f:
        eco_data = json.load(f)
    eco2 = Ecosystem.from_dict(eco_data, w2)
    
    assert w2.seed == w.seed
    assert len(eco2.animals) == len(eco.animals)
    print("Round-trip test passed!")

if __name__ == "__main__":
    test_persistence()
