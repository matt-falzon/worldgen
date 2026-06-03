import worldgen
import random

def test_lighting():
    world = worldgen.World(width=20, height=20, seed=42)
    world.generate()
    
    # Hour 12 (Day)
    day_render = world.render_with_time(12.0)
    # Hour 0 (Night)
    night_render = world.render_with_time(0.0)
    
    # Check that day and night differ significantly
    assert day_render != night_render, "Day and night renderings should be different"
    
    # Check night features
    assert "\033[93m" in night_render, "Night should have city lights (ANSI 93m)"
    assert "\033[90m" in night_render, "Night should have dim colors (ANSI 90m)"
    assert "\033[97m" in night_render, "Night should have star colors (ANSI 97m)"

    print("Successfully verified day vs night differences!")

if __name__ == "__main__":
    test_lighting()
