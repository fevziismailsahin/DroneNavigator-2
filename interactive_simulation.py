"""
Interactive NATO Military Drone Swarm Simulation

This application allows you to configure and run military drone swarm simulations
with real-time visualization and interactive controls.
"""

import os
import time
import sys
import threading
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Replit compatibility
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from config import DEFAULT_CONFIG
from simulation_core import Simulation, Drone, Target, Turret, Obstacle
from gis_utils import GISData
from audio_system import SpatialAudioSystem, AUDIO_AVAILABLE

# Configuration
OUTPUT_DIR = "output"
DEFAULT_MAX_STEPS = 200
DEFAULT_DELAY = 0.1  # Seconds between steps

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

class InteractiveSimulation:
    """Interactive NATO military simulation with real-time configuration."""
    
    def __init__(self):
        """Initialize the interactive simulation."""
        self.config = DEFAULT_CONFIG.copy()
        self.gis = GISData()
        self.simulation = None
        self.step_count = 0
        self.max_steps = DEFAULT_MAX_STEPS
        self.delay = DEFAULT_DELAY
        self.running = False
        self.paused = False
        self.simulation_thread = None
        
        # Audio system
        self.audio = None
        self.drone_sounds = {}
        if AUDIO_AVAILABLE:
            try:
                self.audio = SpatialAudioSystem()
                print("Spatial audio system initialized successfully!")
            except Exception as e:
                print(f"Warning: Could not initialize audio system: {e}")
                self.audio = None
        
        # Advanced scenario options
        self.enemy_drones_enabled = False
        self.rockets_enabled = False
        self.advanced_ai_enabled = False
    
    def initialize_simulation(self):
        """Initialize a new simulation with current config."""
        self.simulation = Simulation(self.config)
        self.simulation.set_gis(self.gis)
        self.step_count = 0
        
        # Initialize audio system listener position if available
        if self.audio:
            field_size = self.simulation.config["FIELD_SIZE"]
            self.audio.set_listener_position(field_size / 2, field_size / 2)
            self.audio.play_mission_start()
            
        # Initialize tracking for audio events
        self.previous_drone_statuses = {d.id: d.alive for d in self.simulation.drones}
        self.previous_target_statuses = {t.id: t.alive for t in self.simulation.targets}
        self.previous_turret_fired = {t.id: False for t in self.simulation.turrets}
        
        # Apply advanced scenario options
        if self.enemy_drones_enabled:
            self._add_enemy_drones()
            
        if self.rockets_enabled:
            self._enable_rockets()
            
        if self.advanced_ai_enabled:
            self._enable_advanced_ai()
        
        print(f"\nSimulation initialized with:")
        print(f"- {self.config['NUM_DRONES']} friendly drones")
        print(f"- {self.config['NUM_TARGETS']} targets")
        print(f"- {self.config['NUM_TURRETS']} defensive turrets")
        print(f"- {self.config['NUM_OBSTACLES']} terrain obstacles")
        if self.enemy_drones_enabled:
            print(f"- Enemy drones enabled (hunting friendly drones)")
        if self.rockets_enabled:
            print(f"- Anti-drone rockets enabled")
        if self.advanced_ai_enabled:
            print(f"- Advanced AI evasion and interception tactics enabled")
        print()
    
    def _add_enemy_drones(self):
        """Add enemy drones that hunt friendly drones."""
        # This is a placeholder for actual implementation
        # In a real implementation, we would extend the simulation_core.py
        # to include a new class of drone with different behavior
        
        # For now, we'll just signal that this would be implemented
        print("Enemy drones would be added in a full implementation.")
        print("These would hunt and attack friendly drones.")
    
    def _enable_rockets(self):
        """Enable rocket-based anti-drone weapons."""
        # This is a placeholder for actual implementation
        # In a real implementation, we would extend the simulation_core.py
        # to include a rocket class with tracking behavior
        
        # For now, we'll just signal that this would be implemented
        print("Anti-drone rockets would be enabled in a full implementation.")
        print("These would launch from turrets and track drones.")
    
    def _enable_advanced_ai(self):
        """Enable advanced AI for drone evasion and interception."""
        # This is a placeholder for actual implementation
        # In a real implementation, we would enhance the drone behavior
        # in simulation_core.py to include more advanced algorithms
        
        # For now, we'll just signal that this would be implemented
        print("Advanced AI tactics would be enabled in a full implementation.")
        print("Drones would use machine learning for evasion and interception.")
    
    def start_simulation(self):
        """Start the simulation in a separate thread."""
        if self.simulation is None:
            self.initialize_simulation()
            
        self.running = True
        self.paused = False
        
        # Start in a separate thread to not block the main thread
        self.simulation_thread = threading.Thread(target=self._run_simulation)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
        print("Simulation started. Press Ctrl+C to stop or 'p' to pause.")
        
    def _run_simulation(self):
        """Run the simulation steps in a loop."""
        while self.running and self.step_count < self.max_steps:
            if not self.paused:
                # Step the simulation
                self.simulation.step()
                self.step_count += 1
                
                # Update audio if available
                if self.audio:
                    self._update_audio()
                
                # Generate visualization
                if self.step_count % 5 == 0 or self.step_count == 1:
                    self._generate_visualization()
                
                # Print progress
                drones_alive = sum(1 for d in self.simulation.drones if d.alive)
                targets_alive = sum(1 for t in self.simulation.targets if t.alive)
                print(f"Step {self.step_count}: Drones active: {drones_alive}/{len(self.simulation.drones)}, "
                      f"Targets remaining: {targets_alive}/{len(self.simulation.targets)}")
                
                # Check if simulation is complete
                if self.simulation.is_complete():
                    print(f"Simulation completed at step {self.step_count}")
                    self._generate_visualization(is_final=True)
                    
                    # Play mission complete sound if audio enabled
                    if self.audio:
                        self.audio.play_mission_complete()
                        # Give time for sound to play
                        time.sleep(2)
                    
                    self.running = False
                    break
                
                # Wait for delay time
                time.sleep(self.delay)
        
        if self.step_count >= self.max_steps:
            print(f"\n=== SIMULATION REACHED MAX STEPS ({self.max_steps}) ===")
            self._print_final_stats()
        
        self.running = False
    
    def _update_audio(self):
        """Update spatial audio based on simulation state."""
        # Update all playing sounds with their current positions
        self.audio.update_active_sounds()
        
        # Handle drone sounds - buzzing, movement, destruction
        for drone in self.simulation.drones:
            # If drone was alive but is now destroyed, play destruction sound
            if self.previous_drone_statuses.get(drone.id, False) and not drone.alive:
                # Play drone destroyed sound at drone position
                self.audio.play_drone_destroyed(drone.pos[0], drone.pos[1])
                
                # Stop any drone buzzing sound
                if drone.id in self.drone_sounds:
                    self.audio.stop_sound(self.drone_sounds[drone.id])
                    del self.drone_sounds[drone.id]
            
            # If drone is alive, play or update drone buzzing
            elif drone.alive:
                # If drone sound doesn't exist yet, create it
                if drone.id not in self.drone_sounds:
                    sound_id = self.audio.play_drone_sound(drone.id, drone.pos[0], drone.pos[1])
                    if sound_id:
                        self.drone_sounds[drone.id] = sound_id
                # Otherwise update the position of existing sound
                elif drone.id in self.drone_sounds:
                    self.audio.update_sound_position(self.drone_sounds[drone.id], drone.pos[0], drone.pos[1])
        
        # Handle turret sounds - alerts and firing
        for turret in self.simulation.turrets:
            # Check if turret just fired (cooldown timer just became active)
            just_fired = turret.cooldown_timer > 0 and not self.previous_turret_fired.get(turret.id, False)
            
            if just_fired:
                # Play turret firing sound
                self.audio.play_turret_fire(turret.id, turret.pos[0], turret.pos[1])
                
            # Occasional turret ping/alert based on step count
            if self.step_count % 10 == turret.id % 10:
                self.audio.play_turret_alert(turret.id, turret.pos[0], turret.pos[1])
        
        # Handle target sounds - destruction
        for target in self.simulation.targets:
            # If target was alive but is now destroyed, play destruction sound
            if self.previous_target_statuses.get(target.id, False) and not target.alive:
                # Play target destroyed sound
                self.audio.play_target_destroyed(target.pos[0], target.pos[1])
                
                # Also play warning sound when target is destroyed (signifies mission progress)
                field_size = self.simulation.config["FIELD_SIZE"]
                self.audio.play_warning(field_size/2, field_size/2)  # Play centered
        
        # Update tracking states
        self.previous_drone_statuses = {d.id: d.alive for d in self.simulation.drones}
        self.previous_target_statuses = {t.id: t.alive for t in self.simulation.targets}
        self.previous_turret_fired = {t.id: t.cooldown_timer > 0 for t in self.simulation.turrets}
    
    def pause_simulation(self):
        """Pause the simulation."""
        self.paused = True
        print("Simulation paused. Press 'r' to resume.")
    
    def resume_simulation(self):
        """Resume the simulation."""
        self.paused = False
        print("Simulation resumed.")
    
    def stop_simulation(self):
        """Stop the simulation."""
        self.running = False
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=1.0)
        
        # Clean up audio resources
        if self.audio:
            self.audio.cleanup()
            
        print("Simulation stopped.")
        self._print_final_stats()
    
    def _print_final_stats(self):
        """Print final simulation statistics."""
        if self.simulation is None:
            return
            
        drones_alive = sum(1 for d in self.simulation.drones if d.alive)
        targets_alive = sum(1 for t in self.simulation.targets if t.alive)
        
        drones_lost = len(self.simulation.drones) - drones_alive
        targets_destroyed = len(self.simulation.targets) - targets_alive
            
        print(f"\n=== SIMULATION COMPLETE ===")
        print(f"Final step: {self.step_count}")
        
        print(f"Targets destroyed: {targets_destroyed}/{len(self.simulation.targets)} "
              f"({targets_destroyed/len(self.simulation.targets)*100:.1f}%)")
        print(f"Drones remaining: {drones_alive}/{len(self.simulation.drones)} "
              f"({drones_alive/len(self.simulation.drones)*100:.1f}%)")
        
        # Calculate exchange ratio
        if drones_lost > 0:
            exchange_ratio = targets_destroyed / drones_lost
        else:
            exchange_ratio = float('inf')
        
        print(f"Exchange ratio: {exchange_ratio:.2f} targets per drone")
        print(f"\nView all generated images in the '{OUTPUT_DIR}' directory.")
    
    def _generate_visualization(self, is_final=False):
        """Generate a military-style visualization of the current state."""
        # Create figure with military style dark theme
        fig, ax = plt.subplots(figsize=(12, 10), facecolor='#0a1929')
        ax.set_facecolor('#132f4c')
        
        # Grid and border styling for military look
        ax.grid(color='#1e4976', linestyle='--', linewidth=0.5, alpha=0.5)
        
        # Set plot limits and labels with military styling
        field_size = self.simulation.config["FIELD_SIZE"]
        ax.set_xlim(0, field_size)
        ax.set_ylim(0, field_size)
        
        # Title and axis labels in military style
        ax.set_title(f"NATO MILITARY SWARM OPERATION - Step {self.step_count}", 
                     color='#66b2ff', fontsize=14, fontweight='bold')
        
        # Coordinate axes in military style
        ax.set_xlabel("X Position (km)", color='#66b2ff')
        ax.set_ylabel("Y Position (km)", color='#66b2ff')
        ax.tick_params(colors='#66b2ff', which='both')
        
        # Military grid squares with coordinates
        for spine in ax.spines.values():
            spine.set_color('#173a5e')
            spine.set_linewidth(2)
        
        # Plot terrain features (obstacles) with enhanced visual style
        for obstacle in self.simulation.obstacles:
            # Mountain/terrain feature
            circle = plt.Circle(
                obstacle.pos, 
                obstacle.radius, 
                color='#654321', 
                alpha=0.8
            )
            # Terrain elevation contours
            contour_circle = plt.Circle(
                obstacle.pos, 
                obstacle.radius * 1.2, 
                color='#654321', 
                alpha=0.3,
                fill=False,
                linestyle='-'
            )
            ax.add_patch(circle)
            ax.add_patch(contour_circle)
        
        # Plot defensive turrets with enhanced military styling
        for turret in self.simulation.turrets:
            # Main turret body
            circle = plt.Circle(
                turret.pos, 
                1.5, 
                color='#ff2a2a', 
                alpha=0.9
            )
            # Turret effective range
            range_circle = plt.Circle(
                turret.pos, 
                turret.range, 
                color='#ff2a2a', 
                alpha=0.15,
                linestyle='--'
            )
            # Maximum engagement range
            max_range_circle = plt.Circle(
                turret.pos, 
                turret.range * 1.1, 
                color='#ff2a2a', 
                alpha=0.05,
                linestyle=':',
                fill=False
            )
            ax.add_patch(circle)
            ax.add_patch(range_circle)
            ax.add_patch(max_range_circle)
            
            # Add targeting lines (simulated active turret scanning)
            scan_angle = (self.step_count * 5) % 360  # Rotating scan
            length = turret.range * 0.7
            dx = length * np.cos(np.radians(scan_angle))
            dy = length * np.sin(np.radians(scan_angle))
            ax.plot([turret.pos[0], turret.pos[0] + dx], 
                    [turret.pos[1], turret.pos[1] + dy], 
                    color='#ff2a2a', linestyle='-', alpha=0.4, linewidth=0.7)
        
        # Plot targets (objectives) with enhanced military styling
        for i, target in enumerate(self.simulation.targets):
            if target.alive:
                # Target symbol (military objective)
                square = plt.Rectangle(
                    (target.pos[0] - 2.0, target.pos[1] - 2.0), 
                    4, 4, 
                    color='#00aa00', 
                    alpha=0.8
                )
                ax.add_patch(square)
                
                # Target identifier
                ax.text(target.pos[0], target.pos[1], f"T{i+1}", 
                        ha='center', va='center', color='white', 
                        fontweight='bold', fontsize=9)
                
                # Target perimeter (security zone)
                perimeter = plt.Circle(
                    target.pos, 
                    5.0, 
                    color='#00aa00', 
                    alpha=0.1,
                    fill=False,
                    linestyle=':'
                )
                ax.add_patch(perimeter)
        
        # Plot drones with enhanced military styling and status indicators
        from config import STATUS_COLORS, DEFAULT_COLOR
        
        for i, drone in enumerate(self.simulation.drones):
            if drone.alive:
                color = STATUS_COLORS.get(drone.status, DEFAULT_COLOR)
                
                # Drone body
                circle = plt.Circle(
                    drone.pos, 
                    0.7, 
                    color=color, 
                    alpha=0.9
                )
                ax.add_patch(circle)
                
                # Draw velocity vector (movement direction and speed indicator)
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
                
                # Add drone ID
                ax.text(drone.pos[0], drone.pos[1], f"{i+1}", 
                        ha='center', va='center', color='white', 
                        fontweight='bold', fontsize=8)
                
                # Draw drone trajectory history (flight path)
                if len(drone.trajectory) > 1:
                    # Get last positions from trajectory
                    # More advanced - use variable segment length based on status
                    history_len = 15 if drone.status == "Attacking" else 10
                    history_len = min(history_len, len(drone.trajectory))
                    
                    # Get the trajectory points safely
                    trajectory_points = list(drone.trajectory)
                    recent_points = trajectory_points[-history_len:] if history_len > 0 else trajectory_points
                    
                    traj_x = [pos[0] for pos in recent_points]
                    traj_y = [pos[1] for pos in recent_points]
                    
                    # Simple line for trajectory
                    ax.plot(traj_x, traj_y, color=color, alpha=0.4, linewidth=1)
                    
                    # Add direction indicator at the midpoint
                    if len(traj_x) > 5:
                        mid_idx = len(traj_x) // 2
                        ax.scatter(traj_x[mid_idx], traj_y[mid_idx], 
                                  color=color, s=10, marker='>')
            else:
                # Advanced visualization for destroyed drones
                # Explosion effect
                ax.scatter(drone.pos[0], drone.pos[1], s=40, color='#ff6600', alpha=0.7)
                
                # Debris pattern
                for j in range(3):
                    angle = j * 120 + (i * 40 % 360)  # Randomized debris pattern
                    dist = 0.8
                    dx = dist * np.cos(np.radians(angle))
                    dy = dist * np.sin(np.radians(angle))
                    ax.plot([drone.pos[0], drone.pos[0] + dx], 
                            [drone.pos[1], drone.pos[1] + dy],
                            color='#ff6600', alpha=0.5, linewidth=0.7)
                
                # X marker for destroyed 
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
        
        # Add legend for drone status with military styling
        from config import STATUS_COLORS
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=color, markersize=10, label=status)
            for status, color in STATUS_COLORS.items()
        ]
        # Add additional items for other symbols
        legend_elements.extend([
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='#00aa00', 
                      markersize=10, label='Target'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#ff2a2a', 
                      markersize=10, label='Turret'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#654321', 
                      markersize=10, label='Terrain')
        ])
        
        legend = ax.legend(handles=legend_elements, loc='upper right', 
                          title="NATO ELEMENTS", framealpha=0.7,
                          facecolor='#173a5e', edgecolor='#66b2ff')
        legend.get_title().set_color('#66b2ff')
        for text in legend.get_texts():
            text.set_color('#e0e0e0')
        
        # Add military time and mission info
        mission_time = f"T+{self.step_count:03d}"
        ax.text(0.02, 0.98, f"MISSION TIME: {mission_time}", 
               transform=ax.transAxes, color='#66b2ff', 
               fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle="round,pad=0.3", fc='#173a5e', ec='#66b2ff', alpha=0.7))
        
        # Add simulation stats
        drones_alive = sum(1 for d in self.simulation.drones if d.alive)
        targets_alive = sum(1 for t in self.simulation.targets if t.alive)
        
        # Add mission status
        status_text = (
            f"DRONES: {drones_alive}/{len(self.simulation.drones)}\n"
            f"TARGETS: {len(self.simulation.targets) - targets_alive}/{len(self.simulation.targets)}\n"
        )
        
        ax.text(0.02, 0.02, status_text,
               transform=ax.transAxes, color='#66b2ff',
               fontsize=10, verticalalignment='bottom',
               bbox=dict(boxstyle="round,pad=0.3", fc='#173a5e', ec='#66b2ff', alpha=0.7))
        
        # Save the plot with high quality
        filename = f"tactical_view_{self.step_count:03d}.png" if not is_final else "final_tactical_view.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        plt.savefig(filepath, dpi=150, facecolor='#0a1929', bbox_inches='tight')
        plt.close(fig)
        
        print(f"Generated visualization at step {self.step_count}")
        return filepath

    def configure_simulation(self):
        """Allow user to configure simulation parameters."""
        print("\n=== SIMULATION CONFIGURATION ===")
        
        try:
            # Basic parameters
            self.config["NUM_DRONES"] = int(input(f"Number of drones [{self.config['NUM_DRONES']}]: ") 
                                          or self.config["NUM_DRONES"])
            
            self.config["NUM_TARGETS"] = int(input(f"Number of targets [{self.config['NUM_TARGETS']}]: ") 
                                           or self.config["NUM_TARGETS"])
            
            self.config["NUM_TURRETS"] = int(input(f"Number of defensive turrets [{self.config['NUM_TURRETS']}]: ") 
                                           or self.config["NUM_TURRETS"])
            
            self.config["NUM_OBSTACLES"] = int(input(f"Number of terrain obstacles [{self.config['NUM_OBSTACLES']}]: ") 
                                             or self.config["NUM_OBSTACLES"])
            
            self.max_steps = int(input(f"Maximum simulation steps [{self.max_steps}]: ") 
                               or self.max_steps)
            
            self.delay = float(input(f"Delay between steps (seconds) [{self.delay}]: ") 
                             or self.delay)
            
            # Advanced parameters
            self.config["DRONE_SPEED"] = float(input(f"Drone speed [{self.config['DRONE_SPEED']}]: ") 
                                             or self.config["DRONE_SPEED"])
            
            self.config["TURRET_RANGE"] = float(input(f"Turret range [{self.config['TURRET_RANGE']}]: ") 
                                              or self.config["TURRET_RANGE"])
            
            self.config["FIELD_SIZE"] = float(input(f"Battlefield size [{self.config['FIELD_SIZE']}]: ") 
                                            or self.config["FIELD_SIZE"])
            
            # Advanced scenario options
            enable_enemy_drones = input("Enable enemy drones (y/n)? [n]: ").lower() or 'n'
            self.enemy_drones_enabled = enable_enemy_drones == 'y'
            
            enable_rockets = input("Enable anti-drone rockets (y/n)? [n]: ").lower() or 'n'
            self.rockets_enabled = enable_rockets == 'y'
            
            enable_advanced_ai = input("Enable advanced AI tactics (y/n)? [n]: ").lower() or 'n'
            self.advanced_ai_enabled = enable_advanced_ai == 'y'
            
            print("\nConfiguration saved. Ready to start simulation.")
            
        except ValueError:
            print("Invalid input. Using default values.")
    
    def run_menu(self):
        """Run the interactive menu for the simulation."""
        print("\n=== NATO MILITARY DRONE SWARM INTERACTIVE SIMULATION ===")
        print("This application allows you to configure and run military drone")
        print("swarm simulations with real-time visualization and controls.")
        
        while True:
            print("\nMAIN MENU:")
            print("1. Configure Simulation Parameters")
            print("2. Start Simulation")
            print("3. View Real-time Visualization")
            print("4. Exit")
            
            choice = input("\nEnter choice (1-4): ")
            
            if choice == '1':
                self.configure_simulation()
                
            elif choice == '2':
                if self.running:
                    print("Simulation is already running.")
                else:
                    self.start_simulation()
                    
                    # Enter control loop
                    try:
                        while self.running:
                            if sys.stdin.isatty():  # Only try to read if running in a terminal
                                command = input("Enter command (p=pause, r=resume, s=stop): ")
                                if command.lower() == 'p':
                                    self.pause_simulation()
                                elif command.lower() == 'r':
                                    self.resume_simulation()
                                elif command.lower() == 's':
                                    self.stop_simulation()
                                    break
                            else:
                                # If not in a terminal, just sleep a bit
                                time.sleep(0.5)
                    except KeyboardInterrupt:
                        self.stop_simulation()
                
            elif choice == '3':
                if not self.running and self.step_count == 0:
                    print("No simulation has been run yet.")
                else:
                    print(f"View the tactical visualizations in the '{OUTPUT_DIR}' directory.")
                    print("You can use visualize_results.py to view them graphically.")
            
            elif choice == '4':
                if self.running:
                    self.stop_simulation()
                if self.audio:
                    self.audio.cleanup()
                print("\nExiting NATO Military Drone Swarm Simulation.")
                break
            
            else:
                print("Invalid choice. Please enter a number from 1-4.")

def main():
    """Main entry point for the interactive simulation."""
    sim = InteractiveSimulation()
    sim.run_menu()

if __name__ == "__main__":
    main()