import dataclasses
import re

with open('ecosystem.py', 'r') as f:
    content = f.read()

# Add to_dict/from_dict to Animal
animal_methods = """
    def to_dict(self):
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
"""
# Replace the dataclass body directly
content = re.sub(r'class Animal:.*?food: int = 10', r'class Animal:\n    species: str\n    x: int\n    y: int\n    preferred_biome: str\n    migration_range: int\n    food: int = 10' + animal_methods, content, flags=re.DOTALL)

# Add to_dict/from_dict to Ecosystem
eco_methods = """
    def to_dict(self):
        return {
            "animals": [a.to_dict() for a in self.animals]
        }

    @classmethod
    def from_dict(cls, data, world):
        eco = cls(world)
        eco.animals = [Animal.from_dict(a) for a in data["animals"]]
        return eco
"""
# Careful replacement for Ecosystem
content = content.replace("        self.animals: List[Animal] = []", "        self.animals: List[Animal] = []" + eco_methods)

with open('ecosystem.py', 'w') as f:
    f.write(content)
