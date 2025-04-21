# Military-Grade Drone Swarm Simulation

A sophisticated simulation of military drone swarms with GIS integration, flocking behavior, target seeking, threat avoidance, and interactive visualization. This project demonstrates advanced agent-based modeling techniques in a tactical environment.

## Features

- **Drone Swarm Intelligence**: Implements cohesion, separation, and alignment behaviors for realistic flocking
- **Military Tactical Elements**: Targets, defensive turrets, and obstacles in a simulated battlespace
- **GIS Integration**: Support for terrain data affecting movement and line-of-sight
- **Learning Mechanisms**: Drones "learn" to avoid threats based on experiences
- **Interactive GUI**: Real-time visualization and parameter adjustment
- **Physics Simulation**: Simple but effective physical model for drone movement

## System Requirements

This application requires:

- Python 3.x
- PyQt5 for the GUI components
- Matplotlib for visualization
- NumPy for mathematical operations
- GIS libraries: geopandas, rasterio, shapely (optional, for terrain features)

## Running the Simulation

The application is designed to run with a graphical user interface:

```bash
python main.py
```

### Important Note

This simulation requires a desktop environment with GUI support, as it uses PyQt5 for its interface. 
When running in a headless environment (like Replit's server), it will operate in command-line mode with limited functionality.

## Using the Application

The GUI provides several panels:

1. **Simulation Control**: Start, pause, and reset the simulation
2. **Configuration**: Adjust drone parameters, flocking weights, and more
3. **GIS Integration**: Load terrain data for enhanced realism
4. **Visualization**: Interactive map showing drone movements and status

## Implementation Details

The simulation is structured around several core components:

- **Drones**: Autonomous agents with flocking behavior and target-seeking
- **Targets**: Objectives for drones to attack
- **Turrets**: Defensive elements that can destroy drones
- **Obstacles**: Physical barriers drones must avoid
- **GIS Data**: Optional terrain information affecting movement

## Source Code Structure

- `main.py`: Application entry point
- `gui.py`: PyQt5 GUI components
- `simulation_core.py`: Core simulation logic and entities
- `mpl_canvas.py`: Matplotlib visualization canvas
- `gis_utils.py`: GIS data handling utilities
- `config.py`: Simulation parameters and constants

## Desktop Usage

For proper visualization and interaction, this simulation should be run on a desktop environment with full GUI support. The application uses PyQt5 which requires a graphical interface.