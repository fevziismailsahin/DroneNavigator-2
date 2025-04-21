# Military-Grade Drone Swarm Simulation

A sophisticated simulation of military drone swarms with GIS integration, flocking behavior, target seeking, threat avoidance, and interactive visualization. This project demonstrates advanced agent-based modeling techniques in a tactical environment.

## Features

- **Drone Swarm Intelligence**: Implements cohesion, separation, and alignment behaviors for realistic flocking
- **Military Tactical Elements**: Targets, defensive turrets, and obstacles in a simulated battlespace
- **GIS Integration**: Support for terrain data affecting movement and line-of-sight
- **Learning Mechanisms**: Drones "learn" to avoid threats based on experiences
- **Interactive GUI**: Real-time visualization and parameter adjustment (when run on desktop)
- **Headless Operation**: Command-line simulation with plot generation for non-GUI environments
- **Physics Simulation**: Simple but effective physical model for drone movement

## System Requirements

This application requires:

- Python 3.x
- NumPy for mathematical operations
- Matplotlib for visualization
- PyQt5 for the GUI components (optional, only for desktop mode)
- GIS libraries: geopandas, rasterio, shapely (optional, for terrain features)

## Running the Simulation

The application automatically detects your environment and runs in the appropriate mode:

```bash
python main.py
```

In a desktop environment with GUI support, it will launch the full interactive application.
In a headless environment (like Replit), it will run the command-line version.

### Headless Mode Options

For more control over the headless simulation, run it directly:

```bash
python headless_simulation.py --steps 300 --interval 20 --drones 20 --targets 8
```

Command line options:
- `--steps`: Number of simulation steps
- `--interval`: How often to save plot images
- `--drones`: Number of drones to simulate
- `--targets`: Number of targets
- `--no-plots`: Disable plot generation for faster simulation

## Implementation Details

The simulation is structured around several core components:

- **Drones**: Autonomous agents with flocking behavior and target-seeking
- **Targets**: Objectives for drones to attack
- **Turrets**: Defensive elements that can destroy drones
- **Obstacles**: Physical barriers drones must avoid
- **GIS Data**: Optional terrain information affecting movement

## Source Code Structure

- `main.py`: Application entry point with environment detection
- `headless_simulation.py`: Command-line simulation for headless environments
- `gui.py`: PyQt5 GUI components for desktop mode
- `simulation_core.py`: Core simulation logic and entities
- `mpl_canvas.py`: Matplotlib visualization canvas
- `gis_utils.py`: GIS data handling utilities
- `config.py`: Simulation parameters and constants

## Output

In headless mode, the simulation generates:
- Console output with simulation statistics and progress
- Plot images saved to the `output` directory showing drone positions and status
- Optional animation generation (requires moviepy package)

## Desktop Usage

For the full interactive experience with real-time parameter adjustment and visualization, run the simulation on a desktop environment with GUI support. The desktop version uses PyQt5 for its graphical interface.