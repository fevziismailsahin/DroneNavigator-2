"""
Core simulation components for the drone swarm simulation.
"""

import numpy as np
from collections import deque
from typing import List, Optional, Dict, Tuple

class Target:
    """Target entity that drones can attack."""
    
    def __init__(self, id: int, x: float, y: float, config: dict):
        """
        Initialize a target.
        
        Args:
            id (int): Unique identifier
            x (float): X position
            y (float): Y position
            config (dict): Simulation configuration
        """
        self.id = id
        self.pos = np.array([x, y], dtype=float)
        self.alive = True
        self.assigned_drones = 0
        self.config = config
    
    def get_pos(self) -> np.ndarray:
        """Get target position."""
        return self.pos


class Turret:
    """
    Defensive turret that can detect and destroy drones within range.
    """
    
    def __init__(self, id: int, x: float, y: float, config: dict):
        """
        Initialize a turret.
        
        Args:
            id (int): Unique identifier
            x (float): X position
            y (float): Y position
            config (dict): Simulation configuration
        """
        self.id = id
        self.pos = np.array([x, y], dtype=float)
        self.config = config
        self.range = config["TURRET_RANGE"]
        self.cooldown_timer = 0
        self.cooldown_max = config["TURRET_COOLDOWN"]
    
    def get_pos(self) -> np.ndarray:
        """Get turret position."""
        return self.pos
    
    def can_shoot(self) -> bool:
        """Check if turret can shoot."""
        return self.cooldown_timer <= 0
    
    def find_target(self, drones: List['Drone']) -> Optional['Drone']:
        """
        Find the closest drone within range.
        
        Args:
            drones (List[Drone]): List of drones to check
            
        Returns:
            Optional[Drone]: The closest drone or None
        """
        closest_drone = None
        min_dist_sq = self.range**2
        for drone in drones:
            if drone.alive and drone.status != "NoFuel":
                dist_sq = np.sum((drone.pos - self.pos)**2)
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    closest_drone = drone
        return closest_drone
    
    def shoot(self, drone: Optional['Drone'], all_drones: List['Drone']):
        """
        Shoot at a drone.
        
        Args:
            drone (Optional[Drone]): The drone to shoot at
            all_drones (List[Drone]): All drones in the simulation
        """
        if self.can_shoot() and drone and drone.alive:
            drone.alive = False
            drone.status = "Destroyed"
            self.cooldown_timer = self.cooldown_max
            # Notify nearby drones (simple learning mechanism)
            for d_notify in all_drones:
                if d_notify.alive and np.linalg.norm(d_notify.pos - drone.pos) < self.config["DRONE_SENSOR_RANGE"] / 2:
                    d_notify.register_threat(self.id, drone.pos)
    
    def update(self, drones: List['Drone']):
        """
        Update turret state.
        
        Args:
            drones (List[Drone]): All drones in the simulation
        """
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1
        if self.can_shoot():
            target_drone = self.find_target(drones)
            self.shoot(target_drone, drones)


class Obstacle:
    """
    Obstacle that drones must avoid.
    """
    
    def __init__(self, id: int, x: float, y: float, size: float, config: dict):
        """
        Initialize an obstacle.
        
        Args:
            id (int): Unique identifier
            x (float): X position
            y (float): Y position
            size (float): Size of the obstacle
            config (dict): Simulation configuration
        """
        self.id = id
        self.pos = np.array([x, y], dtype=float)
        self.size = size
        self.radius = size / 2.0
        self.config = config
    
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
        effective_radius = self.radius + self.config["OBSTACLE_AVOIDANCE_DISTANCE"]
        if 0 < dist_to_obs < effective_radius:
            strength = (1.0 - dist_to_obs / effective_radius)**2
            repulsion_direction = vec_to_obs / dist_to_obs if dist_to_obs > 1e-6 else np.random.rand(2) * 2 - 1
            return repulsion_direction * strength
        return np.zeros(2)


class Drone:
    """
    Drone agent with autonomous behavior capabilities.
    """
    
    def __init__(self, drone_id: int, x: float, y: float, config: dict):
        """
        Initialize a drone.
        
        Args:
            drone_id (int): Unique identifier
            x (float): X position
            y (float): Y position
            config (dict): Simulation configuration
        """
        self.id = drone_id
        self.pos = np.array([x, y], dtype=float)
        self.velocity = np.zeros(2, dtype=float)
        self.alive = True
        self.config = config
        self.fuel = config["DRONE_MAX_FUEL"]
        self.max_speed = config["DRONE_MAX_SPEED"]
        self.target: Optional[Target] = None
        self.status = "Idle"
        self.trajectory = deque(maxlen=20)  # Fixed length for GUI perf
        self.turret_avoidance_factors: Dict[int, float] = {}  # Specific avoidance factors per turret ID
    
    def get_pos(self) -> np.ndarray:
        """Get drone position."""
        return self.pos
    
    def assign_target(self, target: Optional[Target]):
        """
        Assign a target to the drone.
        
        Args:
            target (Optional[Target]): Target to assign
        """
        if self.target and self.target.alive:
            self.target.assigned_drones -= 1
        self.target = target
        if self.target:
            self.target.assigned_drones += 1
            if self.alive and self.status != "NoFuel":
                self.status = "Moving"
        elif self.alive and self.status != "NoFuel":
            self.status = "Idle"
    
    def register_threat(self, turret_id: int, hit_location: np.ndarray):
        """
        Register a threat from a turret.
        
        Args:
            turret_id (int): ID of the turret
            hit_location (np.ndarray): Location where a drone was hit
        """
        current_factor = self.turret_avoidance_factors.get(turret_id, self.config["DRONE_INITIAL_AVOID_FACTOR"])
        new_factor = min(current_factor + self.config["DRONE_LEARNED_AVOID_INCREASE"], 5.0)  # Cap max avoidance
        self.turret_avoidance_factors[turret_id] = new_factor
    
    def calculate_steering_force(self, drones: List['Drone'], targets: List[Target],
                              obstacles: List[Obstacle], turrets: List[Turret], gis) -> np.ndarray:
        """
        Calculate steering force for the drone based on flocking behavior.
        
        Args:
            drones (List[Drone]): All drones in the simulation
            targets (List[Target]): All targets in the simulation
            obstacles (List[Obstacle]): All obstacles in the simulation
            turrets (List[Turret]): All turrets in the simulation
            gis: GIS data handler
            
        Returns:
            np.ndarray: Steering force vector
        """
        # --- Target Seeking ---
        target_force = np.zeros(2)
        if self.target and self.target.alive:
            target_pos_actual = self.target.get_pos()
            desired_velocity = target_pos_actual - self.pos
            dist_to_target = np.linalg.norm(desired_velocity)
            
            if dist_to_target < self.config["DRONE_ATTACK_RANGE"]:
                self.attack()
            elif dist_to_target > 1e-6:
                desired_velocity = (desired_velocity / dist_to_target) * self.max_speed
                target_force = (desired_velocity - self.velocity) * self.config["WEIGHT_TARGET_SEEKING"]
        
        # --- Obstacle Avoidance ---
        obstacle_force = np.zeros(2)
        for obstacle in obstacles:
            obstacle_force += obstacle.get_repulsion_vector(self.pos) * self.config["WEIGHT_OBSTACLE_AVOIDANCE"]
        
        # --- Turret Avoidance ---
        turret_force = np.zeros(2)
        for turret in turrets:
            vec_to_turret = self.pos - turret.pos
            dist_to_turret = np.linalg.norm(vec_to_turret)
            
            # Enhanced avoidance for turrets that have hit nearby drones
            turret_specific_factor = self.turret_avoidance_factors.get(
                turret.id, self.config["DRONE_INITIAL_AVOID_FACTOR"]
            )
            
            if 0 < dist_to_turret < turret.range:
                # Avoidance strength increases as drone gets closer
                avoidance_str = (1.0 - dist_to_turret / turret.range) ** 2
                avoid_dir = vec_to_turret / dist_to_turret if dist_to_turret > 1e-6 else np.random.rand(2) * 2 - 1
                turret_force += avoid_dir * avoidance_str * self.config["WEIGHT_TURRET_AVOIDANCE"] * turret_specific_factor
                
                # Set status to Avoiding if strong avoidance
                if avoidance_str > 0.5 and self.status != "NoFuel" and self.alive:
                    self.status = "Avoiding"
        
        # --- Flocking Behavior ---
        # 1. Cohesion: steer towards center of mass of nearby drones
        # 2. Separation: avoid crowding nearby drones
        # 3. Alignment: steer towards average heading of nearby drones
        
        nearby_drones = [d for d in drones if d.id != self.id and d.alive and 
                        np.linalg.norm(d.pos - self.pos) < self.config["DRONE_SENSOR_RANGE"]]
        
        cohesion_force = np.zeros(2)
        separation_force = np.zeros(2)
        alignment_force = np.zeros(2)
        
        if nearby_drones:
            # Cohesion
            center_of_mass = np.mean([d.pos for d in nearby_drones], axis=0)
            cohesion_force = (center_of_mass - self.pos) * self.config["WEIGHT_COHESION"]
            
            # Separation
            for drone in nearby_drones:
                vec_away = self.pos - drone.pos
                dist = np.linalg.norm(vec_away)
                if dist < 1e-6:  # Avoid division by zero
                    vec_away = np.random.rand(2) * 2 - 1
                    dist = 1.0
                
                # Separation force is stronger when drones are closer
                separation_force += (vec_away / dist) * (self.config["DRONE_SENSOR_RANGE"] / max(dist, 1e-6)) * self.config["WEIGHT_SEPARATION"]
            
            # Alignment
            avg_velocity = np.mean([d.velocity for d in nearby_drones], axis=0)
            alignment_force = (avg_velocity - self.velocity) * self.config["WEIGHT_ALIGNMENT"]
        
        # Combine all forces
        steering_force = (
            target_force + 
            obstacle_force + 
            turret_force + 
            cohesion_force + 
            separation_force + 
            alignment_force
        )
        
        # Terrain influence if GIS is available
        if hasattr(gis, 'get_slope'):
            slope = gis.get_slope(self.pos[0], self.pos[1])
            if slope > 30:  # Steep slope, reduce speed
                steering_force *= max(0.5, 1.0 - (slope - 30) / 60.0)
        
        return steering_force
    
    def attack(self):
        """Attack the assigned target."""
        if self.target and self.target.alive:
            self.target.alive = False
            if self.status != "NoFuel" and self.alive:
                self.status = "Attacking"
                # Reset target assignment
                self.assign_target(None)
    
    def update(self, drones: List['Drone'], targets: List[Target], 
               obstacles: List[Obstacle], turrets: List[Turret], gis):
        """
        Update drone state.
        
        Args:
            drones (List[Drone]): All drones in the simulation
            targets (List[Target]): All targets in the simulation
            obstacles (List[Obstacle]): All obstacles in the simulation
            turrets (List[Turret]): All turrets in the simulation
            gis: GIS data handler
        """
        if not self.alive or self.status == "NoFuel":
            return
        
        # Reduce fuel
        self.fuel -= self.config["DRONE_FUEL_CONSUMPTION_RATE"]
        if self.fuel <= 0:
            self.fuel = 0
            self.status = "NoFuel"
            return
        elif self.fuel / self.config["DRONE_MAX_FUEL"] < self.config["LOW_FUEL_THRESHOLD"]:
            self.status = "LowFuel"
        
        # Calculate steering force
        steering_force = self.calculate_steering_force(drones, targets, obstacles, turrets, gis)
        
        # Apply steering force to velocity
        self.velocity += steering_force
        
        # Limit velocity to max speed
        speed = np.linalg.norm(self.velocity)
        if speed > self.max_speed:
            self.velocity = (self.velocity / speed) * self.max_speed
        
        # Update position
        self.pos += self.velocity
        
        # Boundary handling (wrap or bounce)
        field_size = self.config["FIELD_SIZE"]
        for i in range(2):
            if self.pos[i] < 0:
                self.pos[i] = 0
                self.velocity[i] *= -0.5  # Bounce with energy loss
            elif self.pos[i] > field_size:
                self.pos[i] = field_size
                self.velocity[i] *= -0.5  # Bounce with energy loss
        
        # Update trajectory history for visualization
        self.trajectory.append(np.copy(self.pos))


class Simulation:
    """
    Main simulation class for managing all entities and simulation state.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the simulation.
        
        Args:
            config (dict): Simulation configuration
        """
        self.config = config
        self.drones: List[Drone] = []
        self.targets: List[Target] = []
        self.obstacles: List[Obstacle] = []
        self.turrets: List[Turret] = []
        self.step_count = 0
        self.gis = None
        self.initialize()
    
    def initialize(self):
        """Initialize simulation with random entities."""
        # Clear existing entities
        self.drones.clear()
        self.targets.clear()
        self.obstacles.clear()
        self.turrets.clear()
        self.step_count = 0
        
        field_size = self.config["FIELD_SIZE"]
        
        # Create drones
        for i in range(self.config["NUM_DRONES"]):
            x = np.random.uniform(0, field_size)
            y = np.random.uniform(0, field_size)
            self.drones.append(Drone(i, x, y, self.config))
        
        # Create targets
        for i in range(self.config["NUM_TARGETS"]):
            x = np.random.uniform(0, field_size)
            y = np.random.uniform(0, field_size)
            self.targets.append(Target(i, x, y, self.config))
        
        # Create obstacles
        for i in range(self.config["NUM_OBSTACLES"]):
            x = np.random.uniform(0, field_size)
            y = np.random.uniform(0, field_size)
            size = np.random.uniform(self.config["OBSTACLE_MIN_SIZE"], self.config["OBSTACLE_MAX_SIZE"])
            self.obstacles.append(Obstacle(i, x, y, size, self.config))
        
        # Create turrets
        for i in range(self.config["NUM_TURRETS"]):
            x = np.random.uniform(0, field_size)
            y = np.random.uniform(0, field_size)
            self.turrets.append(Turret(i, x, y, self.config))
    
    def set_gis(self, gis):
        """
        Set the GIS data handler.
        
        Args:
            gis: GIS data handler
        """
        self.gis = gis
    
    def step(self):
        """Execute one simulation step."""
        self.step_count += 1
        
        # Update turrets
        for turret in self.turrets:
            turret.update(self.drones)
        
        # Update drones
        for drone in self.drones:
            drone.update(self.drones, self.targets, self.obstacles, self.turrets, self.gis)
        
        # Auto-assign targets to idle drones
        self.assign_targets()
    
    def assign_targets(self):
        """Assign targets to idle drones."""
        # Find idle drones that need targets
        idle_drones = [d for d in self.drones if d.alive and d.target is None and d.status != "NoFuel"]
        
        # Find alive targets
        alive_targets = [t for t in self.targets if t.alive]
        
        for drone in idle_drones:
            # Find best target based on distance and current assignments
            best_target = None
            best_score = float('inf')
            
            for target in alive_targets:
                if target.assigned_drones >= self.config["TARGET_ASSIGNMENT_LIMIT"]:
                    continue
                
                # Score based on distance and current assignments
                dist = np.linalg.norm(drone.pos - target.pos)
                assignment_penalty = target.assigned_drones * 10  # Penalty for targets with many assignments
                score = dist + assignment_penalty
                
                if score < best_score:
                    best_score = score
                    best_target = target
            
            # Assign the best target
            if best_target:
                drone.assign_target(best_target)
    
    def is_complete(self):
        """Check if simulation is complete."""
        # Check max steps
        if self.step_count >= self.config["MAX_SIMULATION_STEPS"]:
            return True
        
        # Check if all targets are destroyed
        if all(not target.alive for target in self.targets):
            return True
        
        # Check if all drones are destroyed or out of fuel
        active_drones = any(drone.alive and drone.status != "NoFuel" for drone in self.drones)
        if not active_drones:
            return True
        
        return False
    
    def get_statistics(self):
        """
        Get current simulation statistics.
        
        Returns:
            dict: Simulation statistics
        """
        stats = {
            "step_count": self.step_count,
            "drones_alive": sum(1 for d in self.drones if d.alive),
            "drones_active": sum(1 for d in self.drones if d.alive and d.status != "NoFuel"),
            "targets_remaining": sum(1 for t in self.targets if t.alive),
            "targets_destroyed": self.config["NUM_TARGETS"] - sum(1 for t in self.targets if t.alive),
            "drone_statuses": {status: sum(1 for d in self.drones if d.status == status) for status in 
                              ["Idle", "Moving", "Attacking", "Avoiding", "LowFuel", "NoFuel", "Destroyed"]}
        }
        return stats
