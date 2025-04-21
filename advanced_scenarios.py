"""
Advanced NATO Military Drone Swarm Simulation Scenarios

This module extends the core simulation with:
1. Enemy drones that hunt friendly drones
2. Anti-drone rockets
3. Advanced AI for evasion and interception tactics
"""

import numpy as np
from simulation_core import Drone, Target, Turret, Obstacle

class EnemyDrone(Drone):
    """Enemy drone that hunts friendly drones."""
    
    def __init__(self, drone_id, x, y, config):
        """Initialize an enemy drone."""
        super().__init__(drone_id, x, y, config)
        self.is_enemy = True
        self.status = "Enemy"
        self.target_drone = None
        self.hunt_radius = 30.0  # Radius to search for friendly drones
        
    def update(self, drones, targets, obstacles, turrets, gis):
        """Update enemy drone state with hunting behavior."""
        # Enemy drones don't care about targets, just hunt friendly drones
        # Find the closest friendly drone if we don't have a target
        if self.target_drone is None or not self.target_drone.alive:
            self._find_closest_friendly_drone(drones)
        
        # Calculate steering force focused on hunting friendly drones
        force = self._calculate_hunting_force(drones, obstacles, turrets)
        
        # Apply steering force
        self.velocity += force
        
        # Limit speed
        speed = np.linalg.norm(self.velocity)
        if speed > self.max_speed:
            self.velocity = (self.velocity / speed) * self.max_speed
        
        # Update position based on velocity
        self.pos += self.velocity
        
        # Keep position within field bounds
        self.pos[0] = max(0, min(self.pos[0], self.config["FIELD_SIZE"]))
        self.pos[1] = max(0, min(self.pos[1], self.config["FIELD_SIZE"]))
        
        # Add current position to trajectory history
        self.trajectory.append(np.copy(self.pos))
        
        # Maximum history length
        while len(self.trajectory) > self.config.get("TRAJECTORY_LENGTH", 50):
            self.trajectory.popleft()
            
        # Update fuel
        self.fuel -= 1
        if self.fuel <= 0:
            self.alive = False
            self.status = "NoFuel"
            
        # Attack nearby friendly drones
        self._attack_nearby_drones(drones)
    
    def _find_closest_friendly_drone(self, drones):
        """Find the closest friendly drone to hunt."""
        min_dist = float('inf')
        closest_drone = None
        
        for drone in drones:
            # Skip other enemy drones and destroyed drones
            if hasattr(drone, 'is_enemy') or not drone.alive:
                continue
                
            dist = np.linalg.norm(drone.pos - self.pos)
            if dist < min_dist:
                min_dist = dist
                closest_drone = drone
                
        self.target_drone = closest_drone
    
    def _calculate_hunting_force(self, drones, obstacles, turrets):
        """Calculate force for hunting friendly drones."""
        # Start with zero force
        force = np.zeros(2)
        
        # If we have a target drone, seek it
        if self.target_drone and self.target_drone.alive:
            # Vector towards target
            desired_velocity = self.target_drone.pos - self.pos
            dist = np.linalg.norm(desired_velocity)
            
            if dist > 0:
                # Scale by max speed
                desired_velocity = (desired_velocity / dist) * self.max_speed
                
                # Steering = desired - current
                steering_force = desired_velocity - self.velocity
                
                # Limit force magnitude
                steering_force_mag = np.linalg.norm(steering_force)
                if steering_force_mag > self.max_force:
                    steering_force = (steering_force / steering_force_mag) * self.max_force
                
                force += steering_force
        
        # Add obstacle avoidance (stronger for enemy drones - they're more agile)
        for obstacle in obstacles:
            dist_vec = self.pos - obstacle.pos
            dist = np.linalg.norm(dist_vec)
            
            if dist < obstacle.radius + 5.0:  # Extra margin
                # Calculate repulsion force (inversely proportional to distance)
                if dist > 0:
                    repulsion = (dist_vec / dist) * (1.0 / max(0.1, dist - obstacle.radius))
                    force += repulsion * 2.0  # Stronger avoidance
        
        # Add turret avoidance (enemy drones are skilled at evading)
        for turret in turrets:
            dist_vec = self.pos - turret.pos
            dist = np.linalg.norm(dist_vec)
            
            if dist < turret.range * 1.2:  # Stay further from turrets
                if dist > 0:
                    evasion = (dist_vec / dist) * (1.0 / max(0.1, dist - 5.0))
                    force += evasion * 1.5
        
        return force
    
    def _attack_nearby_drones(self, drones):
        """Attack nearby friendly drones."""
        attack_radius = 2.0  # Close range for "attacking"
        
        for drone in drones:
            # Skip enemy drones and destroyed drones
            if hasattr(drone, 'is_enemy') or not drone.alive:
                continue
                
            dist = np.linalg.norm(drone.pos - self.pos)
            
            # If close enough, attack the drone
            if dist < attack_radius:
                # 30% chance to destroy the drone per update when in range
                if np.random.random() < 0.3:
                    drone.alive = False
                    drone.status = "Destroyed"
                    print(f"Enemy drone {self.id} destroyed friendly drone {drone.id}!")
                    break

class Rocket:
    """Anti-drone rocket that can track and intercept drones."""
    
    def __init__(self, rocket_id, x, y, target_drone, config):
        """Initialize a rocket."""
        self.id = rocket_id
        self.pos = np.array([x, y], dtype=float)
        self.velocity = np.zeros(2)
        self.target_drone = target_drone
        self.alive = True
        self.fuel = config.get("ROCKET_FUEL", 50)  # Limited flight time
        self.max_speed = config.get("ROCKET_SPEED", 2.0)  # Faster than drones
        self.blast_radius = config.get("ROCKET_BLAST_RADIUS", 3.0)
        self.config = config
        
    def update(self, drones, obstacles):
        """Update rocket position and tracking."""
        if not self.alive:
            return
            
        # If target is destroyed, self-destruct
        if not self.target_drone.alive:
            self.alive = False
            return
            
        # Calculate vector to target
        to_target = self.target_drone.pos - self.pos
        dist = np.linalg.norm(to_target)
        
        # If we've hit the target, detonate
        if dist < self.blast_radius:
            self._detonate(drones)
            return
            
        # Otherwise, update velocity towards target with some prediction
        if dist > 0:
            # Basic prediction of target's future position
            prediction = 2.0  # Look ahead factor
            future_pos = self.target_drone.pos + self.target_drone.velocity * prediction
            
            # Aim for the predicted position
            to_future = future_pos - self.pos
            to_future_norm = np.linalg.norm(to_future)
            
            if to_future_norm > 0:
                # Set velocity directly (rockets don't have inertia like drones)
                self.velocity = (to_future / to_future_norm) * self.max_speed
        
        # Update position
        self.pos += self.velocity
        
        # Check for obstacle collisions
        for obstacle in obstacles:
            if np.linalg.norm(self.pos - obstacle.pos) < obstacle.radius:
                # Rocket hit an obstacle
                self.alive = False
                return
        
        # Reduce fuel
        self.fuel -= 1
        if self.fuel <= 0:
            # Ran out of fuel, self-destruct without damage
            self.alive = False
    
    def _detonate(self, drones):
        """Detonate the rocket, potentially destroying nearby drones."""
        # Mark as destroyed
        self.alive = False
        
        # Check for drones in blast radius
        for drone in drones:
            if not drone.alive:
                continue
                
            dist = np.linalg.norm(drone.pos - self.pos)
            
            if dist < self.blast_radius:
                # Destroy the drone
                drone.alive = False
                drone.status = "Destroyed"
                print(f"Rocket {self.id} destroyed {'enemy' if hasattr(drone, 'is_enemy') else 'friendly'} drone {drone.id}!")

class AdvancedDroneAI:
    """
    Enhanced drone behavior with advanced tactics.
    This is a wrapper class to add to existing drones.
    """
    
    def __init__(self, drone):
        """Initialize advanced AI for a drone."""
        self.drone = drone
        self.evasion_cooldown = 0  # Cooldown for random evasion
        self.formation_enabled = True  # Whether to use formation flying
        self.threat_memory = {}  # Remember where threats were seen
        
    def enhance_drone_behavior(self, drones, targets, obstacles, turrets, enemy_drones=None):
        """Add advanced behavior to a drone's decision making."""
        # Start with the standard force calculation
        base_force = self.drone.calculate_steering_force(drones, targets, obstacles, turrets, None)
        
        # Add evasive maneuvers against turrets and enemy drones
        evasion_force = self._calculate_evasion(turrets, enemy_drones)
        
        # Add formation flying with friendly drones
        if self.formation_enabled:
            formation_force = self._calculate_formation(drones)
        else:
            formation_force = np.zeros(2)
        
        # Add threat avoidance based on memory
        threat_avoidance = self._calculate_threat_avoidance()
        
        # Combine forces with different weights
        total_force = base_force + evasion_force * 1.5 + formation_force * 0.8 + threat_avoidance * 1.2
        
        # Manage cooldowns
        if self.evasion_cooldown > 0:
            self.evasion_cooldown -= 1
        
        return total_force
    
    def _calculate_evasion(self, turrets, enemy_drones):
        """Calculate evasive maneuvers against threats."""
        evasion_force = np.zeros(2)
        
        # Random evasion occasionally
        if self.evasion_cooldown <= 0 and np.random.random() < 0.05:
            # Random direction change
            angle = np.random.random() * 2 * np.pi
            evasion_force += np.array([np.cos(angle), np.sin(angle)]) * 0.5
            self.evasion_cooldown = 10  # Set cooldown
        
        # Evade turrets that are targeting nearby
        for turret in turrets:
            dist = np.linalg.norm(self.drone.pos - turret.pos)
            
            # If within 90% of turret range, take evasive action
            if dist < turret.range * 0.9:
                away_vector = self.drone.pos - turret.pos
                if np.linalg.norm(away_vector) > 0:
                    away_vector = away_vector / np.linalg.norm(away_vector)
                    
                    # Stronger evasion as we get closer
                    strength = 1.0 - (dist / turret.range)
                    evasion_force += away_vector * strength * 2.0
                    
                    # Remember this threat
                    self.threat_memory[f"turret_{turret.id}"] = {
                        "pos": turret.pos.copy(),
                        "time": 20  # Remember for 20 steps
                    }
        
        # Evade enemy drones if provided
        if enemy_drones:
            for enemy in enemy_drones:
                if not enemy.alive:
                    continue
                    
                dist = np.linalg.norm(self.drone.pos - enemy.pos)
                
                # If within danger range, evade
                if dist < 10.0:
                    away_vector = self.drone.pos - enemy.pos
                    if np.linalg.norm(away_vector) > 0:
                        away_vector = away_vector / np.linalg.norm(away_vector)
                        
                        # Stronger evasion as we get closer
                        strength = 1.0 - (dist / 10.0)
                        evasion_force += away_vector * strength * 3.0
                        
                        # Remember this threat
                        self.threat_memory[f"enemy_{enemy.id}"] = {
                            "pos": enemy.pos.copy(),
                            "time": 15  # Remember for 15 steps
                        }
        
        return evasion_force
    
    def _calculate_formation(self, drones):
        """Calculate formation flying behavior."""
        formation_force = np.zeros(2)
        
        # Only form with other nearby drones
        nearby_drones = []
        for drone in drones:
            if drone.id == self.drone.id or not drone.alive:
                continue
                
            dist = np.linalg.norm(self.drone.pos - drone.pos)
            if dist < 15.0:
                nearby_drones.append(drone)
        
        if nearby_drones:
            # Find average position and velocity
            avg_pos = np.zeros(2)
            avg_vel = np.zeros(2)
            
            for drone in nearby_drones:
                avg_pos += drone.pos
                avg_vel += drone.velocity
            
            avg_pos /= len(nearby_drones)
            avg_vel /= len(nearby_drones)
            
            # Steer towards the average position but maintain some separation
            to_avg = avg_pos - self.drone.pos
            dist = np.linalg.norm(to_avg)
            
            if dist > 5.0:  # Too far from formation
                formation_force += to_avg * 0.03
            elif dist < 3.0:  # Too close in formation
                formation_force -= to_avg * 0.05
            
            # Align with average velocity
            formation_force += (avg_vel - self.drone.velocity) * 0.1
        
        return formation_force
    
    def _calculate_threat_avoidance(self):
        """Avoid areas where threats were recently seen."""
        avoidance_force = np.zeros(2)
        
        # Update threat memory and calculate avoidance
        keys_to_remove = []
        for key, threat in self.threat_memory.items():
            threat["time"] -= 1
            
            if threat["time"] <= 0:
                keys_to_remove.append(key)
            else:
                # Calculate avoidance force based on distance
                to_threat = self.drone.pos - threat["pos"]
                dist = np.linalg.norm(to_threat)
                
                if dist < 20.0 and dist > 0:  # Only avoid if reasonably close
                    normalized = to_threat / dist
                    
                    # Stronger avoidance for fresher threats and closer ones
                    strength = (threat["time"] / 20.0) * (1.0 - dist / 20.0)
                    avoidance_force += normalized * strength
        
        # Remove expired threats
        for key in keys_to_remove:
            del self.threat_memory[key]
        
        return avoidance_force


# Factory functions to create advanced scenario elements

def create_enemy_drones(num_drones, config):
    """Create enemy drones for the simulation."""
    enemy_drones = []
    
    field_size = config["FIELD_SIZE"]
    
    for i in range(num_drones):
        # Place enemy drones around the edges of the field
        if i % 4 == 0:  # Top edge
            x = np.random.uniform(0, field_size)
            y = field_size - np.random.uniform(0, 5)
        elif i % 4 == 1:  # Right edge
            x = field_size - np.random.uniform(0, 5)
            y = np.random.uniform(0, field_size)
        elif i % 4 == 2:  # Bottom edge
            x = np.random.uniform(0, field_size)
            y = np.random.uniform(0, 5)
        else:  # Left edge
            x = np.random.uniform(0, 5)
            y = np.random.uniform(0, field_size)
        
        # Create enemy drone with unique ID starting at 1000
        enemy_drone = EnemyDrone(1000 + i, x, y, config)
        enemy_drones.append(enemy_drone)
    
    return enemy_drones

def fire_rocket(turret, target_drone, rocket_id, config):
    """Fire a rocket from a turret at a target drone."""
    rocket = Rocket(rocket_id, turret.pos[0], turret.pos[1], target_drone, config)
    print(f"Turret {turret.id} fired rocket {rocket_id} at drone {target_drone.id}")
    return rocket

def enhance_drones_with_ai(drones):
    """Enhance existing drones with advanced AI."""
    enhanced_drones = {}
    
    for drone in drones:
        enhanced_drones[drone.id] = AdvancedDroneAI(drone)
    
    return enhanced_drones