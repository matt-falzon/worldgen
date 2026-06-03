import math
from typing import List, Tuple

# Configuration
TERRAIN_COLORS = {
    "D": "#1a237e",   # WATER_DEEP
    "S": "#0288d1",   # WATER_SHALLOW
    "A": "#ffd54f",   # SAND
    "G": "#4caf50",   # GRASS
    "F": "#1b5e20",   # FOREST
    "M": "#616161",   # MOUNTAIN
    "N": "#f5f5f5",   # SNOW
    "C": "#e65100",   # CITY
    "R": "#424242",   # ROAD
    "P": "#81c784",   # PARK
    "I": "#bf360c",   # INDUSTRIAL
    "O": "#ff5722",   # PORT
}

def export_svg(world, filename: str, tile_size: int = 10):
    width = world.width * tile_size
    height = world.height * tile_size + 100 # Extra space for header/legend
    
    svg = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        f'  <defs>',
        f'    <style>text {{ font-family: sans-serif; font-size: 12px; }}</style>',
        f'  </defs>',
    ]
    
    # Background
    svg.append(f'  <rect width="{width}" height="{height}" fill="white" />')
    
    # Title Bar
    svg.append(f'  <text x="10" y="20" font-weight="bold" font-size="16">World: {getattr(world, "seed", "Unknown Seed")}</text>')
    
    # Tile Rendering
    for y in range(world.height):
        for x in range(world.width):
            terrain = world.grid[y][x]
            fill = TERRAIN_COLORS.get(terrain, "#ffffff")
            svg.append(f'  <rect x="{x * tile_size}" y="{y * tile_size + 40}" width="{tile_size}" height="{tile_size}" fill="{fill}" />')
            
    # City Labels
    for cx, cy, name in world.cities:
        svg.append(f'  <text x="{cx * tile_size + 2}" y="{cy * tile_size + 40 + tile_size - 2}" font-size="8" fill="white">{name}</text>')
        
    # Legend
    legend_y = world.height * tile_size + 60
    for i, (code, label) in enumerate([("C", "City"), ("G", "Grass"), ("F", "Forest"), ("M", "Mountain")]):
        svg.append(f'  <rect x="{10 + i * 80}" y="{legend_y}" width="15" height="15" fill="{TERRAIN_COLORS.get(code, "#000")}" />')
        svg.append(f'  <text x="{30 + i * 80}" y="{legend_y + 12}">{label}</text>')
        
    svg.append('</svg>')
    
    with open(filename, 'w') as f:
        f.write("\n".join(svg))
    
    # PNG Fallback logic
    try:
        from cairosvg import svg2png
        png_filename = filename.replace(".svg", ".png")
        svg2png(url=filename, write_to=png_filename)
    except ImportError:
        pass
