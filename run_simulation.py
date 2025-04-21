"""
Run Simulation Script

A simple script to run the drone swarm simulation with custom parameters.
This provides an easy way to customize simulation runs without editing code.
"""

import argparse
from headless_simulation import HeadlessSimulation
from config import DEFAULT_CONFIG

def main():
    """Main entry point for running customized simulations."""
    parser = argparse.ArgumentParser(
        description="NATO Military Drone Swarm Simulation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Basic simulation parameters
    parser.add_argument("--steps", type=int, default=200,
                       help="Number of simulation steps")
    parser.add_argument("--drones", type=int, default=DEFAULT_CONFIG["NUM_DRONES"],
                       help="Number of drones in the swarm")
    parser.add_argument("--targets", type=int, default=DEFAULT_CONFIG["NUM_TARGETS"],
                       help="Number of targets")
    parser.add_argument("--turrets", type=int, default=DEFAULT_CONFIG["NUM_TURRETS"],
                       help="Number of defensive turrets")
    parser.add_argument("--obstacles", type=int, default=DEFAULT_CONFIG["NUM_OBSTACLES"],
                       help="Number of obstacles in the terrain")
    
    # Field parameters
    parser.add_argument("--field-size", type=float, default=DEFAULT_CONFIG["FIELD_SIZE"],
                       help="Size of the simulation field")
    
    # Drone parameters
    parser.add_argument("--drone-speed", type=float, default=DEFAULT_CONFIG["DRONE_MAX_SPEED"],
                       help="Maximum drone speed")
    parser.add_argument("--drone-fuel", type=float, default=DEFAULT_CONFIG["DRONE_MAX_FUEL"],
                       help="Maximum drone fuel")
    parser.add_argument("--fuel-consumption", type=float, 
                       default=DEFAULT_CONFIG["DRONE_FUEL_CONSUMPTION_RATE"],
                       help="Fuel consumption rate per step")
    parser.add_argument("--sensor-range", type=float, default=DEFAULT_CONFIG["DRONE_SENSOR_RANGE"],
                       help="Drone sensor detection range")
    
    # Turret parameters
    parser.add_argument("--turret-range", type=float, default=DEFAULT_CONFIG["TURRET_RANGE"],
                       help="Defensive turret range")
    parser.add_argument("--turret-cooldown", type=int, default=DEFAULT_CONFIG["TURRET_COOLDOWN"],
                       help="Turret reload time (in steps)")
    
    # Behavior weights
    parser.add_argument("--cohesion", type=float, default=DEFAULT_CONFIG["WEIGHT_COHESION"],
                       help="Weight for cohesion behavior")
    parser.add_argument("--separation", type=float, default=DEFAULT_CONFIG["WEIGHT_SEPARATION"],
                       help="Weight for separation behavior")
    parser.add_argument("--alignment", type=float, default=DEFAULT_CONFIG["WEIGHT_ALIGNMENT"],
                       help="Weight for alignment behavior")
    parser.add_argument("--target-seeking", type=float, 
                       default=DEFAULT_CONFIG["WEIGHT_TARGET_SEEKING"],
                       help="Weight for target seeking behavior")
    parser.add_argument("--obstacle-avoidance", type=float, 
                       default=DEFAULT_CONFIG["WEIGHT_OBSTACLE_AVOIDANCE"],
                       help="Weight for obstacle avoidance behavior")
    parser.add_argument("--turret-avoidance", type=float, 
                       default=DEFAULT_CONFIG["WEIGHT_TURRET_AVOIDANCE"],
                       help="Weight for turret avoidance behavior")
    
    # Output options
    parser.add_argument("--output-dir", type=str, default="output",
                       help="Directory for output files")
    parser.add_argument("--interval", type=int, default=10,
                       help="Interval for saving plots (in steps)")
    parser.add_argument("--no-plots", action="store_true",
                       help="Disable plot generation for faster simulation")
    
    args = parser.parse_args()
    
    # Create custom configuration with user-provided parameters
    config = DEFAULT_CONFIG.copy()
    config.update({
        "NUM_DRONES": args.drones,
        "NUM_TARGETS": args.targets,
        "NUM_TURRETS": args.turrets,
        "NUM_OBSTACLES": args.obstacles,
        "FIELD_SIZE": args.field_size,
        "DRONE_MAX_SPEED": args.drone_speed,
        "DRONE_MAX_FUEL": args.drone_fuel,
        "DRONE_FUEL_CONSUMPTION_RATE": args.fuel_consumption,
        "DRONE_SENSOR_RANGE": args.sensor_range,
        "TURRET_RANGE": args.turret_range,
        "TURRET_COOLDOWN": args.turret_cooldown,
        "WEIGHT_COHESION": args.cohesion,
        "WEIGHT_SEPARATION": args.separation,
        "WEIGHT_ALIGNMENT": args.alignment,
        "WEIGHT_TARGET_SEEKING": args.target_seeking,
        "WEIGHT_OBSTACLE_AVOIDANCE": args.obstacle_avoidance,
        "WEIGHT_TURRET_AVOIDANCE": args.turret_avoidance
    })
    
    # Print simulation parameters
    print("=== NATO MILITARY DRONE SWARM SIMULATION ===")
    print(f"Running with custom parameters:")
    print(f"- Drones: {args.drones}")
    print(f"- Targets: {args.targets}")
    print(f"- Turrets: {args.turrets}")
    print(f"- Obstacles: {args.obstacles}")
    print(f"- Field size: {args.field_size}")
    print(f"- Steps: {args.steps}")
    print()
    
    # Run simulation with custom config
    sim = HeadlessSimulation(config, output_dir=args.output_dir)
    sim.run_simulation(
        num_steps=args.steps,
        generate_plots=not args.no_plots,
        save_interval=args.interval
    )
    
    print("\nSimulation complete!")

if __name__ == "__main__":
    main()