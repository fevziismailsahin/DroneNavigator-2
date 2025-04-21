"""
Compatible simulation classes for the enhanced NATO drone swarm simulation.

This module provides simplified compatible versions of the simulation classes
that work with both the original simulation_core and enhanced_simulation modules.
"""

import numpy as np
from typing import List, Optional, Dict, Tuple

class SimpleObstacle:
    """
    Simplified obstacle that drones must avoid.
    Compatible with both simulation versions.
    """
    
    def __init__(self, x: float, y: float, radius: float):
        """
        Initialize a simplified obstacle.
        
        Args:
            x (float): X position
            y (float): Y position
            radius (float): Radius of the obstacle
        """
        self.pos = np.array([x, y], dtype=float)
        self.radius = radius
    
    def get_pos(self) -> np.ndarray:
        """Get obstacle position."""
        return self.pos
    
    def get_repulsion_vector(self, drone_pos: np.ndarray) -> np.ndarray:
        """
        Calculate repulsion vector for a drone.
        
        Args:
            drone_pos (np.ndarray): Position of the drone
            
        Returns:
            np.ndarray: Repulsion vector
        """
        vec_to_obs = drone_pos - self.pos
        dist_to_obs = np.linalg.norm(vec_to_obs)
        effective_radius = self.radius + 5.0  # Default avoidance distance
        if 0 < dist_to_obs < effective_radius:
            strength = (1.0 - dist_to_obs / effective_radius)**2
            repulsion_direction = vec_to_obs / dist_to_obs if dist_to_obs > 1e-6 else np.random.rand(2) * 2 - 1
            return repulsion_direction * strength
        return np.zeros(2)

class SimpleTarget:
    """
    Simplified target for drones to attack.
    Compatible with both simulation versions.
    """
    
    def __init__(self, x: float, y: float, value: float = 10.0):
        """
        Initialize a simplified target.
        
        Args:
            x (float): X position
            y (float): Y position
            value (float): Value/importance of the target
        """
        self.pos = np.array([x, y], dtype=float)
        self.value = value
        self.alive = True
        self.health = 100.0
        
    def get_pos(self) -> np.ndarray:
        """Get target position."""
        return self.pos
    
    def take_damage(self, amount: float) -> bool:
        """
        Apply damage to the target.
        
        Args:
            amount (float): Damage amount
            
        Returns:
            bool: True if target was destroyed
        """
        if not self.alive:
            return False
            
        self.health -= amount
        if self.health <= 0:
            self.alive = False
            return True
        return False

class SimpleTurret:
    """
    Simplified air defense turret.
    Compatible with both simulation versions.
    """
    
    def __init__(self, x: float, y: float, range_val: float, fire_rate: float):
        """
        Initialize a simplified turret.
        
        Args:
            x (float): X position
            y (float): Y position
            range_val (float): Detection/firing range
            fire_rate (float): Rate of fire (probability of firing per step)
        """
        self.pos = np.array([x, y], dtype=float)
        self.range = range_val
        self.fire_rate = fire_rate
        self.last_fired = 0
        
    def can_detect(self, drone_pos: np.ndarray) -> bool:
        """
        Check if a drone is within detection range.
        
        Args:
            drone_pos (np.ndarray): Position of the drone
            
        Returns:
            bool: True if drone is detected
        """
        dist = np.linalg.norm(drone_pos - self.pos)
        return dist <= self.range
        
    def try_fire(self, step: int) -> bool:
        """
        Try to fire the turret based on fire rate.
        
        Args:
            step (int): Current simulation step
            
        Returns:
            bool: True if turret fired
        """
        if step - self.last_fired < 10:  # Cooldown period
            return False
            
        if np.random.random() < self.fire_rate:
            self.last_fired = step
            return True
        return False