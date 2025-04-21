"""
Quick NATO Military Drone Swarm Simulation With Custom Configuration

This script lets you quickly run a drone swarm simulation with custom
parameters and advanced scenarios including enemy drones and rockets.
"""

import os
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for Replit
import matplotlib.pyplot as plt

from config import DEFAULT_CONFIG
from simulation_core import Simulation, Drone, Target, Turret, Obstacle
from gis_utils import GISData
from audio_system import SpatialAudioSystem, AUDIO_AVAILABLE

# Import and use our advanced scenarios if requested
try:
    from advanced_scenarios import (
        EnemyDrone, Rocket, AdvancedDroneAI,
        create_enemy_drones, fire_rocket, enhance_drones_with_ai
    )
    ADVANCED_SCENARIOS_AVAILABLE = True
except ImportError:
    ADVANCED_SCENARIOS_AVAILABLE = False
    print("Advanced scenarios not available. Using basic simulation only.")

# Configuration
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def print_banner():
    """Print a military-style banner."""
    print("\n" + "=" * 60)
    print(" " * 15 + "NATO MILITARY DRONE SWARM SIMULATION")
    print("=" * 60)
    print(" Interactive Tactical Simulation with Advanced AI Capabilities")
    print("-" * 60 + "\n")

def get_user_config():
    """Get user configuration for the simulation."""
    config = DEFAULT_CONFIG.copy()
    
    print("SIMULATION CONFIGURATION:")
    print("-" * 30)
    
    # Basic parameters
    try:
        config["NUM_DRONES"] = int(input(f"Number of friendly drones [{config['NUM_DRONES']}]: ") 
                                   or config["NUM_DRONES"])
        
        config["NUM_TARGETS"] = int(input(f"Number of targets [{config['NUM_TARGETS']}]: ") 
                                    or config["NUM_TARGETS"])
        
        config["NUM_TURRETS"] = int(input(f"Number of defensive turrets [{config['NUM_TURRETS']}]: ") 
                                    or config["NUM_TURRETS"])
        
        config["NUM_OBSTACLES"] = int(input(f"Number of terrain obstacles [{config['NUM_OBSTACLES']}]: ") 
                                      or config["NUM_OBSTACLES"])
        
        max_steps = int(input(f"Maximum simulation steps [100]: ") or 100)
        
        # Advanced parameters
        config["DRONE_SPEED"] = float(input(f"Drone speed [{config['DRONE_SPEED']}]: ") 
                                      or config["DRONE_SPEED"])
        
        config["TURRET_RANGE"] = float(input(f"Turret range [{config['TURRET_RANGE']}]: ") 
                                       or config["TURRET_RANGE"])
    except ValueError:
        print("Invalid input. Using default values.")
    
    # Advanced scenarios
    enemy_drones_enabled = False
    num_enemy_drones = 0
    rockets_enabled = False
    advanced_ai_enabled = False
    
    if ADVANCED_SCENARIOS_AVAILABLE:
        print("\nADVANCED SCENARIO OPTIONS:")
        print("-" * 30)
        
        try:
            enemy_choice = input("Enable enemy drones that hunt your drones? (y/n) [n]: ").lower() or 'n'
            enemy_drones_enabled = enemy_choice == 'y'
            
            if enemy_drones_enabled:
                num_enemy_drones = int(input(f"Number of enemy drones [3]: ") or 3)
            
            rockets_choice = input("Enable anti-drone rockets? (y/n) [n]: ").lower() or 'n'
            rockets_enabled = rockets_choice == 'y'
            
            ai_choice = input("Enable advanced AI for evasion and formation tactics? (y/n) [n]: ").lower() or 'n'
            advanced_ai_enabled = ai_choice == 'y'
        except ValueError:
            print("Invalid input. Using default values.")
    
    print("\nSTARTING SIMULATION WITH THE FOLLOWING CONFIGURATION:")
    print(f"- {config['NUM_DRONES']} friendly drones")
    print(f"- {config['NUM_TARGETS']} targets")
    print(f"- {config['NUM_TURRETS']} defensive turrets")
    print(f"- {config['NUM_OBSTACLES']} terrain obstacles")
    print(f"- Maximum steps: {max_steps}")
    
    if enemy_drones_enabled:
        print(f"- {num_enemy_drones} enemy drones hunting friendly drones")
    if rockets_enabled:
        print("- Anti-drone rockets enabled")
    if advanced_ai_enabled:
        print("- Advanced AI tactics enabled")
    
    return config, max_steps, {
        "enemy_drones": enemy_drones_enabled,
        "num_enemy_drones": num_enemy_drones, 
        "rockets": rockets_enabled,
        "advanced_ai": advanced_ai_enabled
    }

def run_simulation(config, max_steps, advanced_options):
    """Run the simulation with the specified configuration."""
    # Initialize core simulation
    gis = GISData()
    simulation = Simulation(config)
    simulation.set_gis(gis)
    
    # Initialize audio
    audio = None
    drone_sounds = {}
    if AUDIO_AVAILABLE:
        try:
            audio = SpatialAudioSystem()
            field_size = simulation.config["FIELD_SIZE"]
            audio.set_listener_position(field_size / 2, field_size / 2)
            audio.play_mission_start()
            print("Spatial audio initialized in silent mode (no audio device available)")
        except Exception as e:
            print(f"Warning: Could not initialize audio system: {e}")
    
    # Add advanced scenario elements
    enemy_drones = []
    rockets = []
    enhanced_drones = {}
    
    if ADVANCED_SCENARIOS_AVAILABLE:
        if advanced_options["enemy_drones"]:
            enemy_drones = create_enemy_drones(
                advanced_options["num_enemy_drones"], 
                config
            )
            print(f"Added {len(enemy_drones)} enemy drones")
        
        if advanced_options["advanced_ai"]:
            enhanced_drones = enhance_drones_with_ai(simulation.drones)
            print(f"Enhanced {len(enhanced_drones)} drones with advanced AI")
    
    # Prepare for audio tracking
    previous_drone_statuses = {d.id: d.alive for d in simulation.drones}
    if enemy_drones:
        for d in enemy_drones:
            previous_drone_statuses[d.id] = d.alive
    
    previous_target_statuses = {t.id: t.alive for t in simulation.targets}
    previous_turret_fired = {t.id: False for t in simulation.turrets}
    
    print("\nStarting simulation...")
    
    # Run simulation steps
    for step in range(max_steps):
        # Step the core simulation
        simulation.step()
        
        # Update enemy drones
        for enemy in enemy_drones:
            if enemy.alive:
                enemy.update(simulation.drones + enemy_drones, 
                           simulation.targets, 
                           simulation.obstacles, 
                           simulation.turrets, 
                           gis)
        
        # Update rockets
        for rocket in rockets[:]:
            if rocket.alive:
                rocket.update(simulation.drones + enemy_drones, simulation.obstacles)
            else:
                rockets.remove(rocket)
        
        # Launch rockets occasionally if enabled
        if advanced_options["rockets"] and step % 15 == 0:
            for turret in simulation.turrets:
                if turret.can_shoot():
                    # Find a target drone
                    possible_targets = []
                    # Try to target enemy drones first
                    for drone in enemy_drones:
                        if drone.alive and np.linalg.norm(drone.pos - turret.pos) < turret.range:
                            possible_targets.append(drone)
                    
                    # If no enemy drones in range, target random drones
                    if not possible_targets:
                        for drone in simulation.drones:
                            if drone.alive and np.linalg.norm(drone.pos - turret.pos) < turret.range:
                                possible_targets.append(drone)
                    
                    if possible_targets:
                        target = np.random.choice(possible_targets)
                        rockets.append(fire_rocket(turret, target, len(rockets) + 1, config))
        
        # Update audio if available
        if audio:
            update_audio(audio, simulation, enemy_drones, step, 
                       previous_drone_statuses, 
                       previous_target_statuses,
                       previous_turret_fired,
                       drone_sounds)
            
            # Update previous state trackers for next step
            previous_drone_statuses = {d.id: d.alive for d in simulation.drones}
            if enemy_drones:
                for d in enemy_drones:
                    previous_drone_statuses[d.id] = d.alive
                    
            previous_target_statuses = {t.id: t.alive for t in simulation.targets}
            previous_turret_fired = {t.id: t.cooldown_timer > 0 for t in simulation.turrets}
        
        # Generate visualization
        if step % 5 == 0 or step == 0:
            generate_visualization(simulation, enemy_drones, rockets, step)
            
        # Print progress
        friendly_drones_alive = sum(1 for d in simulation.drones if d.alive)
        enemy_drones_alive = sum(1 for d in enemy_drones if d.alive)
        targets_alive = sum(1 for t in simulation.targets if t.alive)
        
        print(f"Step {step+1}: "
              f"Friendly drones: {friendly_drones_alive}/{len(simulation.drones)}, "
              f"Targets: {len(simulation.targets) - targets_alive}/{len(simulation.targets)}, "
              f"Enemy drones: {enemy_drones_alive}/{len(enemy_drones)}" if enemy_drones else
              f"Step {step+1}: "
              f"Drones: {friendly_drones_alive}/{len(simulation.drones)}, "
              f"Targets: {len(simulation.targets) - targets_alive}/{len(simulation.targets)}")
        
        # Check if simulation is complete
        all_targets_destroyed = all(not t.alive for t in simulation.targets)
        all_friendly_drones_destroyed = all(not d.alive for d in simulation.drones)
        
        if all_targets_destroyed or all_friendly_drones_destroyed:
            print(f"Simulation completed at step {step+1}")
            generate_visualization(simulation, enemy_drones, rockets, step, is_final=True)
            
            # Play mission complete sound if audio enabled
            if audio:
                audio.play_mission_complete()
                time.sleep(1)
            
            break
            
        # Small delay to prevent overwhelming output
        time.sleep(0.1)
    
    # Print final stats
    print_final_stats(simulation, enemy_drones, step)
    
    # Clean up audio resources
    if audio:
        audio.cleanup()

def generate_visualization(simulation, enemy_drones, rockets, step, is_final=False):
    """Generate a military-style visualization of the current state."""
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
    
    # Plot terrain features (obstacles)
    for obstacle in simulation.obstacles:
        circle = plt.Circle(
            obstacle.pos, 
            obstacle.radius, 
            color='#654321', 
            alpha=0.8
        )
        ax.add_patch(circle)
    
    # Plot defensive turrets
    for turret in simulation.turrets:
        circle = plt.Circle(
            turret.pos, 
            1.5, 
            color='#ff2a2a', 
            alpha=0.9
        )
        range_circle = plt.Circle(
            turret.pos, 
            turret.range, 
            color='#ff2a2a', 
            alpha=0.15,
            linestyle='--'
        )
        ax.add_patch(circle)
        ax.add_patch(range_circle)
        
        # Add targeting lines
        scan_angle = (step * 5) % 360
        length = turret.range * 0.7
        dx = length * np.cos(np.radians(scan_angle))
        dy = length * np.sin(np.radians(scan_angle))
        ax.plot([turret.pos[0], turret.pos[0] + dx], 
                [turret.pos[1], turret.pos[1] + dy], 
                color='#ff2a2a', linestyle='-', alpha=0.4, linewidth=0.7)
    
    # Plot targets
    for i, target in enumerate(simulation.targets):
        if target.alive:
            square = plt.Rectangle(
                (target.pos[0] - 2.0, target.pos[1] - 2.0), 
                4, 4, 
                color='#00aa00', 
                alpha=0.8
            )
            ax.add_patch(square)
            ax.text(target.pos[0], target.pos[1], f"T{i+1}", 
                    ha='center', va='center', color='white', 
                    fontweight='bold', fontsize=9)
    
    # Plot friendly drones
    from config import STATUS_COLORS, DEFAULT_COLOR
    
    for i, drone in enumerate(simulation.drones):
        if drone.alive:
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
            
            ax.text(drone.pos[0], drone.pos[1], f"{i+1}", 
                    ha='center', va='center', color='white', 
                    fontweight='bold', fontsize=8)
        else:
            # Show destroyed drones
            ax.scatter(drone.pos[0], drone.pos[1], s=40, color='#ff6600', alpha=0.7)
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
    
    # Plot enemy drones if present
    for i, enemy in enumerate(enemy_drones):
        if enemy.alive:
            # Enemy drones are red
            circle = plt.Circle(
                enemy.pos, 
                0.9,  # Slightly bigger
                color='#ff0000', 
                alpha=0.9
            )
            ax.add_patch(circle)
            
            # Draw velocity vector
            if np.linalg.norm(enemy.velocity) > 0.1:
                velocity = enemy.velocity / np.linalg.norm(enemy.velocity) * 2
                ax.arrow(
                    enemy.pos[0], 
                    enemy.pos[1], 
                    velocity[0], 
                    velocity[1], 
                    head_width=0.4, 
                    head_length=0.7, 
                    fc='#ff0000', 
                    ec='#ff0000'
                )
            
            # Enemy ID
            ax.text(enemy.pos[0], enemy.pos[1], f"E{i+1}", 
                    ha='center', va='center', color='white', 
                    fontweight='bold', fontsize=8)
        else:
            # Show destroyed enemy drones
            ax.scatter(enemy.pos[0], enemy.pos[1], s=40, color='#ff6600', alpha=0.7)
            ax.plot(
                [enemy.pos[0] - 0.5, enemy.pos[0] + 0.5], 
                [enemy.pos[1] - 0.5, enemy.pos[1] + 0.5], 
                color='#ff0000', 
                linewidth=2
            )
            ax.plot(
                [enemy.pos[0] - 0.5, enemy.pos[0] + 0.5], 
                [enemy.pos[1] + 0.5, enemy.pos[1] - 0.5], 
                color='#ff0000', 
                linewidth=2
            )
    
    # Plot rockets if present
    for rocket in rockets:
        if rocket.alive:
            # Rocket symbol
            ax.scatter(rocket.pos[0], rocket.pos[1], color='#ffff00', marker='^', s=50)
            
            # Trail
            if np.linalg.norm(rocket.velocity) > 0:
                trail_length = 2.0
                direction = -rocket.velocity / np.linalg.norm(rocket.velocity)
                trail_end = rocket.pos + direction * trail_length
                ax.plot([rocket.pos[0], trail_end[0]], 
                        [rocket.pos[1], trail_end[1]], 
                        color='#ffff00', alpha=0.6, linestyle='-')
    
    # Add legend
    from config import STATUS_COLORS
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor=color, markersize=10, label=status)
        for status, color in STATUS_COLORS.items()
    ]
    
    # Add enemy drone to legend if present
    if enemy_drones:
        legend_elements.append(
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor='#ff0000', markersize=10, label='Enemy')
        )
    
    # Add rocket to legend if present
    if rockets:
        legend_elements.append(
            plt.Line2D([0], [0], marker='^', color='w', 
                      markerfacecolor='#ffff00', markersize=10, label='Rocket')
        )
    
    # Add remaining elements
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
    
    # Add mission time
    mission_time = f"T+{step+1:03d}"
    ax.text(0.02, 0.98, f"MISSION TIME: {mission_time}", 
           transform=ax.transAxes, color='#66b2ff', 
           fontsize=10, verticalalignment='top',
           bbox=dict(boxstyle="round,pad=0.3", fc='#173a5e', ec='#66b2ff', alpha=0.7))
    
    # Add mission status
    friendly_drones_alive = sum(1 for d in simulation.drones if d.alive)
    enemy_drones_alive = sum(1 for d in enemy_drones if d.alive)
    targets_alive = sum(1 for t in simulation.targets if t.alive)
    
    status_text = (
        f"FRIENDLY DRONES: {friendly_drones_alive}/{len(simulation.drones)}\n"
        f"TARGETS DESTROYED: {len(simulation.targets) - targets_alive}/{len(simulation.targets)}"
    )
    
    if enemy_drones:
        status_text += f"\nENEMY DRONES: {enemy_drones_alive}/{len(enemy_drones)}"
    
    ax.text(0.02, 0.02, status_text,
           transform=ax.transAxes, color='#66b2ff',
           fontsize=10, verticalalignment='bottom',
           bbox=dict(boxstyle="round,pad=0.3", fc='#173a5e', ec='#66b2ff', alpha=0.7))
    
    # Save the plot
    filename = f"tactical_view_{step+1:03d}.png" if not is_final else "final_tactical_view.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=150, facecolor='#0a1929', bbox_inches='tight')
    plt.close(fig)
    
    print(f"Generated tactical visualization: {filename}")
    return filepath

def update_audio(audio, simulation, enemy_drones, step, prev_drone_status, 
               prev_target_status, prev_turret_fired, drone_sounds):
    """Update spatial audio based on simulation state."""
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
    
    # Handle enemy drone sounds
    for enemy in enemy_drones:
        # If enemy drone was alive but is now destroyed, play destruction sound
        if prev_drone_status.get(enemy.id, False) and not enemy.alive:
            # Play drone destroyed sound at drone position (different tone for enemy)
            audio.play_drone_destroyed(enemy.pos[0], enemy.pos[1])
            
            # Stop any drone buzzing sound
            if enemy.id in drone_sounds:
                audio.stop_sound(drone_sounds[enemy.id])
                del drone_sounds[enemy.id]
        
        # If enemy drone is alive, play or update buzzing
        elif enemy.alive:
            # If drone sound doesn't exist yet, create it
            if enemy.id not in drone_sounds:
                sound_id = audio.play_drone_sound(enemy.id, enemy.pos[0], enemy.pos[1])
                if sound_id:
                    drone_sounds[enemy.id] = sound_id
            # Otherwise update the position of existing sound
            elif enemy.id in drone_sounds:
                audio.update_sound_position(drone_sounds[enemy.id], enemy.pos[0], enemy.pos[1])
    
    # Handle turret sounds - alerts and firing
    for turret in simulation.turrets:
        # Check if turret just fired (cooldown timer just became active)
        just_fired = turret.cooldown_timer > 0 and not prev_turret_fired.get(turret.id, False)
        
        if just_fired:
            # Play turret firing sound
            audio.play_turret_fire(turret.id, turret.pos[0], turret.pos[1])
            
        # Occasional turret ping/alert based on step count
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

def print_final_stats(simulation, enemy_drones, step):
    """Print final simulation statistics."""
    friendly_drones_alive = sum(1 for d in simulation.drones if d.alive)
    enemy_drones_alive = sum(1 for d in enemy_drones if d.alive)
    targets_alive = sum(1 for t in simulation.targets if t.alive)
    
    friendly_drones_lost = len(simulation.drones) - friendly_drones_alive
    targets_destroyed = len(simulation.targets) - targets_alive
    
    print("\n" + "=" * 40)
    print("SIMULATION COMPLETE - FINAL REPORT")
    print("=" * 40)
    print(f"Mission Duration: {step+1} steps")
    print(f"Targets Destroyed: {targets_destroyed}/{len(simulation.targets)} "
          f"({targets_destroyed/len(simulation.targets)*100:.1f}%)")
    print(f"Friendly Drones Remaining: {friendly_drones_alive}/{len(simulation.drones)} "
          f"({friendly_drones_alive/len(simulation.drones)*100:.1f}%)")
    
    if enemy_drones:
        enemy_drones_destroyed = len(enemy_drones) - enemy_drones_alive
        print(f"Enemy Drones Destroyed: {enemy_drones_destroyed}/{len(enemy_drones)} "
              f"({enemy_drones_destroyed/len(enemy_drones)*100:.1f}%)")
    
    # Calculate exchange ratio
    if friendly_drones_lost > 0:
        exchange_ratio = targets_destroyed / friendly_drones_lost
    else:
        exchange_ratio = float('inf')
    
    print(f"Exchange Ratio: {exchange_ratio:.2f} targets per drone")
    
    # Mission success determination
    if targets_destroyed == len(simulation.targets):
        if friendly_drones_alive > 0:
            success_rate = friendly_drones_alive / len(simulation.drones) * 100
            if success_rate > 50:
                print("\nMISSION OUTCOME: OUTSTANDING SUCCESS")
            elif success_rate > 25:
                print("\nMISSION OUTCOME: SUCCESSFUL")
            else:
                print("\nMISSION OUTCOME: PYRRHIC VICTORY")
        else:
            print("\nMISSION OUTCOME: MUTUAL DESTRUCTION")
    elif targets_destroyed > len(simulation.targets) / 2:
        print("\nMISSION OUTCOME: PARTIAL SUCCESS")
    else:
        print("\nMISSION OUTCOME: FAILURE")
    
    print("\nView all tactical visualizations in the 'output' directory.")
    print("Use 'python visualize_results.py' to view them interactively.")

def main():
    """Main function to run the simulation."""
    print_banner()
    
    config, max_steps, advanced_options = get_user_config()
    run_simulation(config, max_steps, advanced_options)

if __name__ == "__main__":
    main()