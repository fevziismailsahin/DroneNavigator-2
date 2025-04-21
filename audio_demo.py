"""
NATO Military Drone Swarm Spatial Audio Demonstration

This script demonstrates the spatial audio system developed for the
military drone swarm simulation. It creates a variety of military
sound effects that are positioned and moved in 3D space.
"""

import os
import time
import math
import pygame
import numpy as np
from audio_system import SpatialAudioSystem

def demo_spatial_audio():
    """Run a demonstration of spatial audio capabilities."""
    
    print("\nNATO MILITARY DRONE SWARM SPATIAL AUDIO DEMONSTRATION")
    print("====================================================")
    print("Generating realistic military sound effects with spatial positioning...")
    print("This demonstration will play various sounds from the simulation.")
    print("Audio files will be cached in the 'audio_cache' directory.")
    print("\nStarting audio demonstration...\n")
    
    # Create audio system
    audio = SpatialAudioSystem()
    
    # Set listener position at center of field
    listener_x, listener_y = 50, 50
    audio.set_listener_position(listener_x, listener_y)
    
    # Phase 1: Mission Start
    print("[Phase 1] Mission Start")
    audio.play_mission_start()
    time.sleep(1.5)
    
    # Phase 2: Ambient Background
    print("[Phase 2] Ambient Background")
    ambient = audio.play_ambient()
    time.sleep(2)
    
    # Phase 3: Drone Swarm
    print("[Phase 3] Drone Swarm Approaching")
    drone_sounds = {}
    
    # Create a circle of drones
    num_drones = 6
    for i in range(num_drones):
        angle = (i * 360 / num_drones) * math.pi / 180
        radius = 30  # Distance from listener
        x = listener_x + radius * math.cos(angle)
        y = listener_y + radius * math.sin(angle)
        
        drone_sounds[i] = audio.play_drone_sound(i, x, y)
        time.sleep(0.3)  # Stagger drone sound creation
    
    # Make drones approach listener
    print("[Phase 4] Drones Moving - Notice the spatial positioning")
    for step in range(20):
        for i in range(num_drones):
            # Get original angle
            angle = (i * 360 / num_drones) * math.pi / 180
            # Calculate new position (slowly approach center)
            radius = 30 - step * 1.2
            x = listener_x + radius * math.cos(angle)
            y = listener_y + radius * math.sin(angle)
            
            # Update drone sound position
            audio.update_sound_position(drone_sounds[i], x, y)
        
        time.sleep(0.15)
    
    # Phase 5: Turret alerts and firing
    print("[Phase 5] Defensive Turrets Activated")
    
    # Position turrets in different quadrants
    turret_positions = [
        (20, 20),  # Bottom left
        (80, 20),  # Bottom right
        (20, 80),  # Top left
        (80, 80),  # Top right
    ]
    
    # Alert sounds
    for i, pos in enumerate(turret_positions):
        audio.play_turret_alert(i, pos[0], pos[1])
        time.sleep(0.7)
    
    # Fire at drones
    print("[Phase 6] Turrets Firing")
    for i, pos in enumerate(turret_positions):
        audio.play_turret_fire(i, pos[0], pos[1])
        time.sleep(0.2)
        
        # Create drone destruction near this turret
        if i < len(drone_sounds):
            # Stop the drone sound
            audio.stop_sound(drone_sounds[i])
            
            # Play explosion near the turret
            explosion_x = pos[0] + (5 * (np.random.random() - 0.5))
            explosion_y = pos[1] + (5 * (np.random.random() - 0.5))
            audio.play_drone_destroyed(explosion_x, explosion_y)
            time.sleep(0.8)
    
    # Phase 7: Target destruction
    print("[Phase 7] Target Engagement")
    
    # Destroy targets
    target_positions = [
        (30, 60),
        (70, 40),
    ]
    
    for i, pos in enumerate(target_positions):
        audio.play_target_destroyed(pos[0], pos[1])
        time.sleep(1.5)
        
        # Play warning sound after target destroyed
        audio.play_warning(listener_x, listener_y)
        time.sleep(1.0)
    
    # Phase 8: Mission complete
    print("[Phase 8] Mission Complete")
    audio.play_mission_complete()
    time.sleep(2.0)
    
    # Clean up
    audio.cleanup()
    print("\nSpatial audio demonstration complete!")
    print("Audio files have been cached to the 'audio_cache' directory.")

if __name__ == "__main__":
    demo_spatial_audio()