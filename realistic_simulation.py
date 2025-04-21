"""
NATO Military Drone Swarm Simulation with Real-World Map Integration

This script provides a command-line interface for running enhanced drone swarm
simulations with realistic terrain, advanced tactical AI, and military-grade visuals.
"""

import os
import sys
import argparse
import time
from enhanced_simulation import run_enhanced_simulation, EnhancedSimulation
from config import DEFAULT_CONFIG
from geo_data_manager import GeoDataManager

def main():
    """
    Main entry point for realistic drone swarm simulation.
    
    Parses command-line arguments and runs the simulation with the specified
    parameters, including terrain, weather, time of day, and mission type.
    """
    parser = argparse.ArgumentParser(
        description="NATO Military Drone Swarm Simulation with Real-World Maps",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Simulation parameters
    parser.add_argument("--num-drones", type=int, default=10,
                      help="Number of friendly drones in the swarm")
    parser.add_argument("--num-enemies", type=int, default=3,
                      help="Number of enemy drones (set to 0 to disable)")
    parser.add_argument("--num-steps", type=int, default=200,
                      help="Maximum number of simulation steps")
    
    # Environmental conditions
    parser.add_argument("--time", type=str, choices=["day", "dusk", "night"],
                      default="day", help="Time of day affecting visibility")
    parser.add_argument("--weather", type=str, 
                      choices=["clear", "cloudy", "rain", "fog"],
                      default="clear", help="Weather conditions")
    
    # Mission parameters
    parser.add_argument("--mission", type=str,
                      choices=["strike", "recon", "defend", "escort"],
                      default="strike", help="Mission type")
    parser.add_argument("--threat", type=str,
                      choices=["low", "medium", "high"],
                      default="medium", help="Threat level")
    
    # Output options
    parser.add_argument("--output-dir", type=str, default="output",
                      help="Directory for output files")
    parser.add_argument("--save-interval", type=int, default=10,
                      help="Interval for saving visualization frames")
    parser.add_argument("--show-map", action="store_true",
                      help="Show the tactical map after generation")
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Prepare output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Prepare configuration
    config = DEFAULT_CONFIG.copy()
    config["NUM_DRONES"] = args.num_drones
    
    # Generate the initial map visualization
    print("\nNATO MILITARY DRONE SWARM SIMULATION")
    print("=====================================")
    print(f"Initializing geographic data...")
    
    # Initialize map data
    geo_manager = GeoDataManager()
    geo_manager.load_terrain_data()
    geo_manager.load_map_data()
    
    # Generate initial tactical map
    print("Generating tactical map...")
    tactical_map = geo_manager.render_full_map(
        show_terrain=True,
        show_features=True
    )
    map_file = os.path.join(args.output_dir, "tactical_map_initial.png")
    tactical_map.savefig(map_file, dpi=150, bbox_inches='tight')
    print(f"Tactical map saved to {map_file}")
    
    # Show mission parameters
    print("\nMISSION PARAMETERS:")
    print(f"Time: {args.time.upper()}")
    print(f"Weather: {args.weather.upper()}")
    print(f"Mission Type: {args.mission.upper()}")
    print(f"Threat Level: {args.threat.upper()}")
    print(f"Friendly Drones: {args.num_drones}")
    print(f"Enemy Drones: {args.num_enemies}")
    
    # Run the simulation
    print("\nStarting simulation...")
    
    start_time = time.time()
    simulation = run_enhanced_simulation(
        config=config,
        num_steps=args.num_steps,
        with_enemy_drones=(args.num_enemies > 0),
        time_of_day=args.time,
        weather=args.weather,
        mission_type=args.mission,
        output_dir=args.output_dir,
        save_interval=args.save_interval
    )
    end_time = time.time()
    
    # Show final statistics
    stats = simulation.get_statistics()
    
    print("\nMISSION STATISTICS:")
    print(f"Simulation time: {end_time - start_time:.2f} seconds")
    print(f"Mission steps: {stats.get('step_count', 0)}")
    print(f"Drones remaining: {stats['drones_alive']}/{stats['total_drones']}")
    print(f"Enemy drones destroyed: {stats.get('enemy_drones_destroyed', 0)}/{args.num_enemies}")
    print(f"Targets destroyed: {stats['targets_destroyed']}/{stats['total_targets']}")
    
    if stats['mission_complete']:
        print("Mission status: SUCCESS")
    elif stats['mission_failed']:
        print("Mission status: FAILED")
    else:
        print("Mission status: INCOMPLETE")
    
    # Show output file information
    print(f"\nVisualization frames saved to: {args.output_dir}/")
    print(f"Final tactical map: {args.output_dir}/tactical_map_{stats.get('step_count', args.num_steps-1):03d}.png")

def generate_demo(output_dir="output"):
    """
    Generate a demonstration of the realistic simulation with a set of predefined scenarios.
    
    Args:
        output_dir (str): Directory for output files
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Define scenarios for demonstration
    scenarios = [
        {
            "name": "Daytime Strike Mission",
            "time": "day",
            "weather": "clear",
            "mission": "strike",
            "num_drones": 10,
            "num_enemies": 3,
            "num_steps": 100
        },
        {
            "name": "Night Recon Mission",
            "time": "night",
            "weather": "clear",
            "mission": "recon",
            "num_drones": 8,
            "num_enemies": 2,
            "num_steps": 100
        },
        {
            "name": "Adverse Weather Combat",
            "time": "day",
            "weather": "fog",
            "mission": "strike",
            "num_drones": 12,
            "num_enemies": 4,
            "num_steps": 100
        }
    ]
    
    print("\nNATO MILITARY DRONE SWARM SIMULATION DEMO")
    print("=========================================")
    print("Generating demonstrations of multiple scenarios...")
    
    for i, scenario in enumerate(scenarios):
        scenario_dir = os.path.join(output_dir, f"scenario_{i+1}")
        os.makedirs(scenario_dir, exist_ok=True)
        
        print(f"\nScenario {i+1}: {scenario['name']}")
        print(f"Time: {scenario['time'].upper()}")
        print(f"Weather: {scenario['weather'].upper()}")
        print(f"Mission: {scenario['mission'].upper()}")
        
        config = DEFAULT_CONFIG.copy()
        config["NUM_DRONES"] = scenario["num_drones"]
        
        # Run the simulation for this scenario
        run_enhanced_simulation(
            config=config,
            num_steps=scenario["num_steps"],
            with_enemy_drones=(scenario["num_enemies"] > 0),
            time_of_day=scenario["time"],
            weather=scenario["weather"],
            mission_type=scenario["mission"],
            output_dir=scenario_dir,
            save_interval=20
        )
        
        print(f"Scenario {i+1} completed. Output saved to {scenario_dir}/")
    
    print("\nAll demonstration scenarios completed.")
    print(f"Output saved to {output_dir}/")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        generate_demo()
    else:
        main()