"""
Headless Military-Grade Drone Swarm Simulation

This module provides a non-GUI version of the drone swarm simulation that
can run in headless environments like Replit, outputting results to the console.
"""

import sys
import time
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from config import DEFAULT_CONFIG
from simulation_core import Simulation
from gis_utils import GISData

class HeadlessSimulation:
    """Headless version of the drone swarm simulation."""
    
    def __init__(self, config=None, output_dir="output"):
        """
        Initialize the headless simulation.
        
        Args:
            config (dict): Simulation configuration
            output_dir (str): Directory for output files
        """
        self.config = config or DEFAULT_CONFIG.copy()
        self.simulation = Simulation(self.config)
        self.gis = GISData()
        self.simulation.set_gis(self.gis)
        self.step_count = 0
        self.max_steps = self.config["MAX_SIMULATION_STEPS"]
        
        # Create output directory if it doesn't exist
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def run_simulation(self, num_steps=None, generate_plots=True, save_interval=50):
        """
        Run the simulation for a specified number of steps.
        
        Args:
            num_steps (int): Number of steps to run, or None for max_steps
            generate_plots (bool): Whether to generate plots during simulation
            save_interval (int): Interval at which to save plots
        """
        if num_steps is None:
            num_steps = self.max_steps
        
        print(f"Starting headless simulation with {len(self.simulation.drones)} drones, "
              f"{len(self.simulation.targets)} targets, {len(self.simulation.turrets)} turrets")
        print(f"Running for {num_steps} steps...")
        
        start_time = time.time()
        
        for step in range(num_steps):
            self.simulation.step()
            self.step_count += 1
            
            # Print progress periodically
            if step % 10 == 0 or step == num_steps - 1:
                stats = self.simulation.get_statistics()
                self._print_stats(stats)
            
            # Generate and save plot periodically
            if generate_plots and (step % save_interval == 0 or step == num_steps - 1):
                self._generate_plot(step)
            
            # Check if simulation is complete
            if self.simulation.is_complete():
                print(f"Simulation completed after {step+1} steps")
                if generate_plots:
                    self._generate_plot(step, is_final=True)
                break
        
        end_time = time.time()
        
        # Final statistics
        final_stats = self.simulation.get_statistics()
        print("\n--- SIMULATION COMPLETE ---")
        print(f"Total steps: {self.step_count}")
        print(f"Execution time: {end_time - start_time:.2f} seconds")
        print(f"Steps per second: {self.step_count / (end_time - start_time):.2f}")
        self._print_final_report(final_stats)
    
    def _print_stats(self, stats):
        """Print current simulation statistics."""
        print(f"Step {stats['step_count']}: "
              f"Drones alive: {stats['drones_alive']}/{len(self.simulation.drones)}, "
              f"Targets remaining: {stats['targets_remaining']}/{len(self.simulation.targets)}")
    
    def _print_final_report(self, stats):
        """Print detailed final report."""
        print("\n--- FINAL REPORT ---")
        print(f"Mission Duration: {stats['step_count']} steps")
        
        # Calculate success metrics
        targets_destroyed = len(self.simulation.targets) - stats['targets_remaining']
        drones_lost = len(self.simulation.drones) - stats['drones_alive']
        
        print(f"Targets destroyed: {targets_destroyed}/{len(self.simulation.targets)} "
              f"({targets_destroyed/len(self.simulation.targets)*100:.1f}%)")
        print(f"Drones remaining: {stats['drones_alive']}/{len(self.simulation.drones)} "
              f"({stats['drones_alive']/len(self.simulation.drones)*100:.1f}%)")
        print(f"Drones lost: {drones_lost}")
        print(f"Exchange ratio: {targets_destroyed / max(drones_lost, 1):.2f} targets per drone")
        
        # Status breakdown of remaining drones
        statuses = {}
        for drone in self.simulation.drones:
            if not drone.alive:
                continue
            statuses[drone.status] = statuses.get(drone.status, 0) + 1
        
        print("\nRemaining drone statuses:")
        for status, count in statuses.items():
            print(f"  {status}: {count} drones")
    
    def _generate_plot(self, step, is_final=False):
        """
        Generate a plot of the current simulation state.
        
        Args:
            step (int): Current step number
            is_final (bool): Whether this is the final plot
        """
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Set plot limits and labels
        field_size = self.config["FIELD_SIZE"]
        ax.set_xlim(0, field_size)
        ax.set_ylim(0, field_size)
        ax.set_title(f"Drone Swarm Simulation - Step {step+1}")
        ax.set_xlabel("X Position")
        ax.set_ylabel("Y Position")
        
        # Plot obstacles
        for obstacle in self.simulation.obstacles:
            circle = plt.Circle(
                obstacle.pos, 
                obstacle.radius, 
                color='brown', 
                alpha=0.7
            )
            ax.add_patch(circle)
        
        # Plot turrets
        for turret in self.simulation.turrets:
            circle = plt.Circle(
                turret.pos, 
                1.0, 
                color='red', 
                alpha=0.9
            )
            range_circle = plt.Circle(
                turret.pos, 
                turret.range, 
                color='red', 
                alpha=0.1
            )
            ax.add_patch(circle)
            ax.add_patch(range_circle)
        
        # Plot targets
        for target in self.simulation.targets:
            if target.alive:
                square = plt.Rectangle(
                    (target.pos[0] - 1.5, target.pos[1] - 1.5), 
                    3, 3, 
                    color='green', 
                    alpha=0.8
                )
                ax.add_patch(square)
        
        # Plot drones with color based on status
        for drone in self.simulation.drones:
            if drone.alive:
                from config import STATUS_COLORS, DEFAULT_COLOR
                color = STATUS_COLORS.get(drone.status, DEFAULT_COLOR)
                circle = plt.Circle(
                    drone.pos, 
                    0.7, 
                    color=color, 
                    alpha=0.9
                )
                ax.add_patch(circle)
                
                # Draw velocity vector
                if np.linalg.norm(drone.velocity) > 0.1:
                    velocity = drone.velocity / np.linalg.norm(drone.velocity) * 2
                    ax.arrow(
                        drone.pos[0], 
                        drone.pos[1], 
                        velocity[0], 
                        velocity[1], 
                        head_width=0.4, 
                        head_length=0.7, 
                        fc=color, 
                        ec=color
                    )
                
                # Draw trajectory
                if len(drone.trajectory) > 1:
                    traj_x = [pos[0] for pos in drone.trajectory]
                    traj_y = [pos[1] for pos in drone.trajectory]
                    ax.plot(traj_x, traj_y, color=color, alpha=0.5, linewidth=1)
            else:
                # X for destroyed drones
                marker_size = 20
                ax.plot(
                    [drone.pos[0] - 0.5, drone.pos[0] + 0.5], 
                    [drone.pos[1] - 0.5, drone.pos[1] + 0.5], 
                    color='red', 
                    linewidth=2
                )
                ax.plot(
                    [drone.pos[0] - 0.5, drone.pos[0] + 0.5], 
                    [drone.pos[1] + 0.5, drone.pos[1] - 0.5], 
                    color='red', 
                    linewidth=2
                )
        
        # Add legend for drone status
        from config import STATUS_COLORS
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=color, markersize=10, label=status)
            for status, color in STATUS_COLORS.items()
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        # Save the plot
        filename = f"step_{step+1:04d}.png" if not is_final else "final_state.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=100)
        plt.close(fig)
        
        if step % 50 == 0 or is_final:
            print(f"Plot saved to {filepath}")

    def generate_animation(self, output_filename="simulation_animation.mp4", fps=10):
        """
        Generate an animation from saved plots.
        Requires FFmpeg installed on the system.
        
        Args:
            output_filename (str): Output animation filename
            fps (int): Frames per second
        """
        try:
            import moviepy.editor as mpy
            import glob
            
            # Get all plot files sorted
            plot_files = sorted(glob.glob(os.path.join(self.output_dir, "step_*.png")))
            
            if not plot_files:
                print("No plot files found to create animation")
                return
            
            # Create clip
            clip = mpy.ImageSequenceClip(plot_files, fps=fps)
            output_path = os.path.join(self.output_dir, output_filename)
            clip.write_videofile(output_path)
            
            print(f"Animation saved to {output_path}")
        except ImportError:
            print("MoviePy is required for animation generation. Install with: pip install moviepy")
        except Exception as e:
            print(f"Error generating animation: {e}")

def run_demo(num_steps=200, save_interval=10):
    """Run a demonstration of the headless simulation."""
    print("=== NATO MILITARY DRONE SWARM SIMULATION ===")
    print("Running headless simulation demonstration...\n")
    
    # Use a smaller configuration for faster demo
    config = DEFAULT_CONFIG.copy()
    config["NUM_DRONES"] = 15
    config["NUM_TARGETS"] = 5
    config["NUM_TURRETS"] = 4
    config["NUM_OBSTACLES"] = 7
    config["WEIGHT_TURRET_AVOIDANCE"] = 2.5  # More cautious drones
    
    sim = HeadlessSimulation(config)
    sim.run_simulation(num_steps=num_steps, save_interval=save_interval)
    
    print("\nDemo completed. Check the 'output' directory for plot images.")
    
    # Uncomment to generate animation if moviepy is available
    # sim.generate_animation()

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Run headless drone swarm simulation")
    parser.add_argument("--steps", type=int, default=200, 
                        help="Number of simulation steps")
    parser.add_argument("--interval", type=int, default=10,
                        help="Interval for saving plots")
    parser.add_argument("--drones", type=int, default=None,
                        help="Number of drones (overrides default)")
    parser.add_argument("--targets", type=int, default=None,
                        help="Number of targets (overrides default)")
    parser.add_argument("--no-plots", action="store_true",
                        help="Disable plot generation for faster simulation")
    
    args = parser.parse_args()
    
    if args.drones or args.targets:
        config = DEFAULT_CONFIG.copy()
        if args.drones:
            config["NUM_DRONES"] = args.drones
        if args.targets:
            config["NUM_TARGETS"] = args.targets
        sim = HeadlessSimulation(config)
    else:
        sim = HeadlessSimulation()
    
    sim.run_simulation(
        num_steps=args.steps,
        generate_plots=not args.no_plots,
        save_interval=args.interval
    )