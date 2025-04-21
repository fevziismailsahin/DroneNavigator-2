"""
Direct Military Drone Swarm Simulation with Matplotlib Output and Spatial Audio.

This application runs a drone swarm simulation with immersive military sound effects
and automatically saves visualization images that you can view directly without
a web interface.
"""

import os
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from config import DEFAULT_CONFIG
from simulation_core import Simulation
from gis_utils import GISData
from audio_system import SpatialAudioSystem

# Configuration
OUTPUT_DIR = "output"
MAX_STEPS = 100
SAVE_INTERVAL = 5
USE_AUDIO = True  # Set to False to disable audio

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_simulation():
    """Run the simulation and generate visualization frames with spatial audio"""
    
    # Initialize simulation
    config = DEFAULT_CONFIG.copy()
    # Increase number of entities for a more impressive demo
    config["NUM_DRONES"] = 20
    config["NUM_TARGETS"] = 7
    config["NUM_TURRETS"] = 6
    config["NUM_OBSTACLES"] = 10
    
    gis = GISData()
    simulation = Simulation(config)
    simulation.set_gis(gis)
    
    # Initialize audio system if enabled
    audio = None
    drone_sounds = {}
    if USE_AUDIO:
        try:
            audio = SpatialAudioSystem()
            # Set listener at the center of the field
            field_size = simulation.config["FIELD_SIZE"]
            audio.set_listener_position(field_size / 2, field_size / 2)
            # Play mission start sound
            audio.play_mission_start()
            print("Spatial audio system initialized successfully!")
        except Exception as e:
            print(f"Warning: Could not initialize audio system: {e}")
            audio = None
    
    print(f"=== NATO MILITARY DRONE SWARM SIMULATION ===")
    print(f"Starting simulation with {config['NUM_DRONES']} drones, "
          f"{config['NUM_TARGETS']} targets, {config['NUM_TURRETS']} turrets")
    print(f"View the output images in the '{OUTPUT_DIR}' directory")
    print(f"New frames will be generated every {SAVE_INTERVAL} steps")
    if audio:
        print(f"Immersive spatial audio is ENABLED")
    print()
    
    # Track previous simulation state for audio events
    previous_drone_statuses = {d.id: d.alive for d in simulation.drones}
    previous_target_statuses = {t.id: t.alive for t in simulation.targets}
    previous_turret_fired = {t.id: False for t in simulation.turrets}
    
    # Run simulation and generate frames
    for step in range(MAX_STEPS):
        # Step the simulation
        simulation.step()
        
        # Handle audio events if enabled
        if audio:
            # Update spatial audio based on simulation state
            update_spatial_audio(audio, simulation, step, 
                               previous_drone_statuses, 
                               previous_target_statuses,
                               previous_turret_fired,
                               drone_sounds)
            
            # Update previous state trackers for next step
            previous_drone_statuses = {d.id: d.alive for d in simulation.drones}
            previous_target_statuses = {t.id: t.alive for t in simulation.targets}
            previous_turret_fired = {t.id: t.cooldown_timer > 0 for t in simulation.turrets}
        
        # Generate visualization at regular intervals
        if step % SAVE_INTERVAL == 0 or step == MAX_STEPS - 1:
            print(f"Step {step+1}: Generating visualization...")
            generate_military_style_visualization(simulation, step)
            
        # Print progress
        stats = simulation.get_statistics()
        drones_alive = sum(1 for d in simulation.drones if d.alive)
        targets_alive = sum(1 for t in simulation.targets if t.alive)
        print(f"Step {step+1}: Drones active: {drones_alive}/{len(simulation.drones)}, "
              f"Targets remaining: {targets_alive}/{len(simulation.targets)}")
        
        # Check if simulation is complete
        if simulation.is_complete():
            print(f"Simulation completed at step {step+1}")
            generate_military_style_visualization(simulation, step, is_final=True)
            
            # Play mission complete sound if audio enabled
            if audio:
                audio.play_mission_complete()
                # Give time for sound to play
                time.sleep(2)
            break
            
        # Small delay to allow audio processing
        if audio:
            time.sleep(0.05)
            
    # Print final stats
    print("\n=== SIMULATION COMPLETE ===")
    print(f"Final step: {step+1}")
    
    # Calculate and print mission results
    drones_lost = len(simulation.drones) - drones_alive
    targets_destroyed = len(simulation.targets) - targets_alive
    
    print(f"Targets destroyed: {targets_destroyed}/{len(simulation.targets)} "
          f"({targets_destroyed/len(simulation.targets)*100:.1f}%)")
    print(f"Drones remaining: {drones_alive}/{len(simulation.drones)} "
          f"({drones_alive/len(simulation.drones)*100:.1f}%)")
    
    # Calculate exchange ratio
    if drones_lost > 0:
        exchange_ratio = targets_destroyed / drones_lost
    else:
        exchange_ratio = float('inf')
    
    print(f"Exchange ratio: {exchange_ratio:.2f} targets per drone")
    print(f"\nView all generated images in the '{OUTPUT_DIR}' directory.")
    
    # Clean up audio resources
    if audio:
        audio.cleanup()

def generate_military_style_visualization(simulation, step, is_final=False):
    """Generate a military-style visualization of the simulation"""
    
    # Create figure with military style dark theme
    fig, ax = plt.subplots(figsize=(12, 10), facecolor='#0a1929')
    ax.set_facecolor('#132f4c')
    
    # Grid and border styling for military look
    ax.grid(color='#1e4976', linestyle='--', linewidth=0.5, alpha=0.5)
    
    # Set plot limits and labels with military styling
    field_size = simulation.config["FIELD_SIZE"]
    ax.set_xlim(0, field_size)
    ax.set_ylim(0, field_size)
    
    # Title and axis labels in military style
    ax.set_title(f"NATO MILITARY SWARM OPERATION - Step {step+1}", 
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
    for obstacle in simulation.obstacles:
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
    for turret in simulation.turrets:
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
        scan_angle = (step * 5) % 360  # Rotating scan
        length = turret.range * 0.7
        dx = length * np.cos(np.radians(scan_angle))
        dy = length * np.sin(np.radians(scan_angle))
        ax.plot([turret.pos[0], turret.pos[0] + dx], 
                [turret.pos[1], turret.pos[1] + dy], 
                color='#ff2a2a', linestyle='-', alpha=0.4, linewidth=0.7)
    
    # Plot targets (objectives) with enhanced military styling
    for i, target in enumerate(simulation.targets):
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
    
    for i, drone in enumerate(simulation.drones):
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
    mission_time = f"T+{step+1:03d}"
    ax.text(0.02, 0.98, f"MISSION TIME: {mission_time}", 
           transform=ax.transAxes, color='#66b2ff', 
           fontsize=10, verticalalignment='top',
           bbox=dict(boxstyle="round,pad=0.3", fc='#173a5e', ec='#66b2ff', alpha=0.7))
    
    # Add simulation stats
    drones_alive = sum(1 for d in simulation.drones if d.alive)
    targets_alive = sum(1 for t in simulation.targets if t.alive)
    
    # Add mission status
    status_text = (
        f"DRONES: {drones_alive}/{len(simulation.drones)}\n"
        f"TARGETS: {len(simulation.targets) - targets_alive}/{len(simulation.targets)}\n"
    )
    
    ax.text(0.02, 0.02, status_text,
           transform=ax.transAxes, color='#66b2ff',
           fontsize=10, verticalalignment='bottom',
           bbox=dict(boxstyle="round,pad=0.3", fc='#173a5e', ec='#66b2ff', alpha=0.7))
    
    # Save the plot with high quality
    filename = f"tactical_view_{step+1:03d}.png" if not is_final else "final_tactical_view.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=150, facecolor='#0a1929', bbox_inches='tight')
    plt.close(fig)
    
    return filepath

def update_spatial_audio(audio, simulation, step, prev_drone_status, prev_target_status, prev_turret_fired, drone_sounds):
    """
    Update spatial audio based on simulation state.
    
    Args:
        audio: SpatialAudioSystem instance
        simulation: Current simulation state
        step: Current simulation step
        prev_drone_status: Previous drone alive status dictionary
        prev_target_status: Previous target alive status dictionary
        prev_turret_fired: Previous turret firing status dictionary
        drone_sounds: Dictionary tracking active drone sound IDs
    """
    # Update all playing sounds with their current positions
    audio.update_active_sounds()
    
    # Handle drone sounds - buzzing, movement, destruction
    for drone in simulation.drones:
        # If drone was alive but is now destroyed, play destruction sound
        if prev_drone_status.get(drone.id, False) and not drone.alive:
            # Play drone destroyed sound at drone position
            audio.play_drone_destroyed(drone.pos[0], drone.pos[1])
            
            # Stop any drone buzzing sound
            if drone.id in drone_sounds:
                audio.stop_sound(drone_sounds[drone.id])
                del drone_sounds[drone.id]
        
        # If drone is alive, play or update drone buzzing
        elif drone.alive:
            # If drone sound doesn't exist yet, create it
            if drone.id not in drone_sounds:
                sound_id = audio.play_drone_sound(drone.id, drone.pos[0], drone.pos[1])
                if sound_id:
                    drone_sounds[drone.id] = sound_id
            # Otherwise update the position of existing sound
            elif drone.id in drone_sounds:
                audio.update_sound_position(drone_sounds[drone.id], drone.pos[0], drone.pos[1])
    
    # Handle turret sounds - alerts and firing
    for turret in simulation.turrets:
        # Check if turret just fired (cooldown timer just became active)
        just_fired = turret.cooldown_timer > 0 and not prev_turret_fired.get(turret.id, False)
        
        if just_fired:
            # Play turret firing sound
            audio.play_turret_fire(turret.id, turret.pos[0], turret.pos[1])
            
        # Occasional turret ping/alert based on step count (every ~10 steps)
        if step % 10 == turret.id % 10:
            audio.play_turret_alert(turret.id, turret.pos[0], turret.pos[1])
    
    # Handle target sounds - destruction
    for target in simulation.targets:
        # If target was alive but is now destroyed, play destruction sound
        if prev_target_status.get(target.id, False) and not target.alive:
            # Play target destroyed sound
            audio.play_target_destroyed(target.pos[0], target.pos[1])
            
            # Also play warning sound when target is destroyed (signifies mission progress)
            field_size = simulation.config["FIELD_SIZE"]
            audio.play_warning(field_size/2, field_size/2)  # Play centered

if __name__ == "__main__":
    print("\nNATO MILITARY DRONE SWARM SIMULATION")
    print("====================================")
    print("This simulation will generate high-quality tactical visualizations")
    print("Images will be saved to the 'output' directory")
    print("Immersive spatial audio will be generated for military realism\n")
    
    run_simulation()