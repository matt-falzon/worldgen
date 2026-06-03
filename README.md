# Procedural World Generator

Generates organic, colorful worlds in your terminal using noise-based terrain, city placement, seasonal rendering, and weather simulation.

## Requirements

Python 3.6+

## Usage

```bash
# Single world generation
python3 worldgen.py --once

# With a specific seed (reproducible)
python3 worldgen.py --once --seed 42

# Animated season + weather cycle
python3 worldgen.py --seasons --seed 42

# Plain text (no ANSI colors)
python3 worldgen.py --once --plain
```

## Flags

| Flag | Description |
|------|-------------|
| `--once` | Generate a single world and exit |
| `--seed N` | Use a specific seed for reproducibility |
| `--seasons` | Animate through seasons with weather effects |
| `--plain` | No color output |
| `--noload` | Skip animated loading bars |
| `--width N` | World width (default: 120) |
| `--height N` | World height (default: 40) |

## What It Generates

- **Terrain**: Deep water, shallow water, beaches, plains, forests, jungles, swamps, mountains, snow peaks
- **Cities**: Randomly named cities placed on flat land with parks, industrial zones, and roads connecting nearby cities
- **Ports**: Placed on beaches adjacent to water near cities
- **Seasons**: Visual changes per season — spring flowers, autumn leaves, winter snow
- **Weather**: Rain, storms, snow, and fog overlays

## Examples

Generate a world and save to file:
```bash
python3 worldgen.py --once --seed 7 --plain > world.txt
```

Run continuously (auto-generates new worlds every 15s, Ctrl+C to stop):
```bash
python3 worldgen.py
```
