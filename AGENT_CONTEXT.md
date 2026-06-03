# Worldgen — Project Context

## What It Is

A terminal-based procedural world generator built in Python. Uses noise-based heightmaps, moisture, and temperature maps to generate organic-looking worlds with terrain biomes, cities, roads, ports, and seasonal/weather rendering.

Location: `~/dev/worldgen/worldgen.py` (single file, ~790 lines)

## Architecture

- `SimplexNoise` — value noise generator with octave support for terrain heightmaps, moisture, and temperature layers
- `World` class — core generator
  - `generate_heightmap()`, `generate_moisture()`, `generate_temperature()` — noise layers
  - `classify_terrain()` — maps noise values to terrain types (water, sand, grass, forest, jungle, swamp, mountain, snow)
  - `place_cities()` — finds flat grass regions via BFS, places cities with parks, industrial zones, ports, and roads between nearby cities
  - `render()` / `render_seasonal()` / `render_weather()` — ANSI color output with seasonal and weather overlays
  - `render_stats()`, `render_city_list()`, `render_legend()` — metadata
- CLI entry via argparse (`--once`, `--seed`, `--seasons`, `--plain`, `--noload`, `--width`, `--height`)

## Running It

```bash
python3 worldgen.py --once --seed 42      # single world
python3 worldgen.py --seasons --seed 42   # animated season + weather cycle
python3 worldgen.py                       # infinite loop, new world every 15s, Ctrl+C to stop
```

## Current State (June 2026)

- Working single-file implementation
- Terrain generation with 12+ biome types
- City placement with roads, parks, industry, ports
- Seasonal color/character overrides (spring flowers, autumn leaves, winter snow)
- Weather overlays (rain, storm, snow, fog, clear)
- Animated loading bars during generation
- CLI flags for all modes
- No tests, no dependencies beyond stdlib

## Ideas for Next Steps

- **Cellular automata evolution** — simulate city growth, deforestation, erosion over time steps
- **SVG/PNG export** — render the world as an image instead of just terminal output
- **Heightmap visualization** — 3D wireframe or contour map in terminal
- **River generation** — flow water from mountains to ocean using gradient descent
- **Map tiling / zoom** — seamless infinite world by tiling noise at different scales
- **Save/load worlds** — serialize the grid and metadata to JSON
- **Tests** — verify terrain classification, city placement, render output

## Terrain Types

`D` Deep Water, `S` Shallow, `A` Sand/Beach, `G` Grass/Plains, `F` Forest, `J` Jungle, `W` Swamp, `M` Mountain, `N` Snow, `C` City, `R` Road, `P` Park, `I` Industrial, `O` Port
