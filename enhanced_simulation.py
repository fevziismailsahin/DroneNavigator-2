"""
Enhanced NATO Military Drone Swarm Simulation with Real-World Map Integration

This module provides enhanced simulation capabilities using realistic geographic
data, terrain analysis, and advanced tactical visualizations.
"""

import os
import json
import numpy as np
import time
import threading
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D

from config import DEFAULT_CONFIG
from simulation_core import Simulation, Drone, Target, Obstacle, Turret
from geo_data_manager import GeoDataManager
from advanced_scenarios import EnemyDrone, Rocket, AdvancedDroneAI

# Create output directory if it doesn't exist
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class EnhancedDrone(Drone):
    """Enhanced drone with terrain awareness and tactical behavior."""
    
    def __init__(self, drone_id, x, y, config):
        """Initialize an enhanced drone."""
        super().__init__(drone_id, x, y, config)
        self.terrain_awareness = True
        self.tactical_level = np.random.uniform(0.5, 1.0)  # Individual tactical skill
        self.operational_role = np.random.choice([
            "scout", "attacker", "defender", "support"
        ])
        
        # Role-specific parameters
        if self.operational_role == "scout":
            self.perception_range *= 1.5
            self.max_speed *= 1.2
        elif self.operational_role == "attacker":
            self.attack_strength *= 1.3
            self.attack_range *= 1.2
        elif self.operational_role == "defender":
            self.perception_range *= 1.2
            self.avoidance_strength *= 1.5
        elif self.operational_role == "support":
            self.cohesion_strength *= 2.0
            self.alignment_strength *= 1.5
    
    def update(self, drones, targets, obstacles, turrets, gis):
        """Update drone state with terrain awareness."""
        # Get terrain information at current position
        slope, aspect = (0, 0)
        if gis:
            elevation = gis.get_elevation(self.pos[0], self.pos[1])
            slope, aspect = gis.get_slope(self.pos[0], self.pos[1])
        
        # Adjust behavior based on terrain
        if slope > 30:  # Steep terrain
            self.max_speed *= 0.8  # Slow down on steep terrain
            self.avoidance_strength *= 1.5  # Increase obstacle avoidance
        
        # Execute role-based behavior
        if self.operational_role == "scout" and not self.target:
            # Scouts prioritize exploration and target identification
            self._execute_scout_behavior(drones, targets, obstacles, turrets, gis)
        elif self.operational_role == "attacker" and self.target:
            # Attackers prioritize target engagement
            self._execute_attacker_behavior(drones, targets, obstacles, turrets, gis)
        elif self.operational_role == "defender":
            # Defenders prioritize threat avoidance and swarm protection
            self._execute_defender_behavior(drones, targets, obstacles, turrets, gis)
        elif self.operational_role == "support":
            # Support drones prioritize coordination
            self._execute_support_behavior(drones, targets, obstacles, turrets, gis)
        
        # Fall back to standard behavior if role-specific behavior didn't apply
        if not self.force_applied:
            super().update(drones, targets, obstacles, turrets, gis)
    
    def _execute_scout_behavior(self, drones, targets, obstacles, turrets, gis):
        """Execute scout-specific behavior."""
        if len(targets) == 0:
            return
        
        # Find unexplored areas
        grid_size = 10
        grid = np.zeros((grid_size, grid_size))
        
        # Mark areas where drones have been
        for drone in drones:
            if drone.alive:
                # Convert position to grid coordinates
                gx = int(drone.pos[0] * (grid_size - 1))
                gy = int(drone.pos[1] * (grid_size - 1))
                if 0 <= gx < grid_size and 0 <= gy < grid_size:
                    grid[gy, gx] += 1
        
        # Find the least explored cell
        min_visits = np.min(grid)
        min_cells = np.where(grid == min_visits)
        
        if len(min_cells[0]) > 0:
            # Pick a random cell from the least explored ones
            idx = np.random.randint(len(min_cells[0]))
            target_y, target_x = min_cells[0][idx], min_cells[1][idx]
            
            # Convert back to simulation coordinates
            target_x = target_x / (grid_size - 1)
            target_y = target_y / (grid_size - 1)
            
            # Create a force towards the unexplored area
            direction = np.array([target_x, target_y]) - self.pos
            distance = np.linalg.norm(direction)
            if distance > 0:
                direction /= distance
                
                explore_force = direction * self.max_speed * 0.8
                self.force += explore_force
                self.force_applied = True
    
    def _execute_attacker_behavior(self, drones, targets, obstacles, turrets, gis):
        """Execute attacker-specific behavior."""
        if not self.target:
            return
        
        # Find the best attack vector based on terrain and turret positions
        attack_vectors = []
        
        # Generate possible attack angles
        for angle_deg in range(0, 360, 45):
            angle_rad = np.radians(angle_deg)
            direction = np.array([np.cos(angle_rad), np.sin(angle_rad)])
            
            # Check if this direction avoids turrets
            turret_risk = 0
            for turret in turrets:
                if turret.can_detect(self.pos):
                    # Calculate risk based on alignment with turret
                    turret_direction = turret.pos - self.pos
                    turret_distance = np.linalg.norm(turret_direction)
                    if turret_distance > 0:
                        turret_direction /= turret_distance
                        alignment = np.dot(direction, turret_direction)
                        # Higher alignment = higher risk
                        turret_risk += max(0, alignment) * (1.0 / max(0.1, turret_distance))
            
            # Check terrain advantage
            terrain_advantage = 0
            if gis:
                # Check if there's cover in this direction
                test_pos = self.pos + direction * 0.05
                if 0 <= test_pos[0] <= 1 and 0 <= test_pos[1] <= 1:
                    # Check if terrain provides cover between us and the target
                    target_pos = self.target.pos
                    has_los = gis.is_line_of_sight_clear(test_pos, target_pos)
                    if not has_los:
                        # No line of sight means good cover
                        terrain_advantage = -1  # Negative = better
            
            # Calculate overall vector quality (lower is better)
            vector_quality = turret_risk + terrain_advantage
            
            attack_vectors.append((direction, vector_quality))
        
        # Sort vectors by quality (lower is better)
        attack_vectors.sort(key=lambda x: x[1])
        
        if attack_vectors:
            # Use the best attack vector
            best_direction, _ = attack_vectors[0]
            
            # Create force toward target using this direction
            target_force = best_direction * self.max_speed
            
            # Apply the force
            self.force += target_force
            self.force_applied = True
    
    def _execute_defender_behavior(self, drones, targets, obstacles, turrets, gis):
        """Execute defender-specific behavior."""
        # Find threatened drones
        threatened_drones = []
        for drone in drones:
            if drone.alive and drone != self:
                # Check if drone is under threat from turrets
                for turret in turrets:
                    if turret.can_detect(drone.pos):
                        threatened_drones.append(drone)
                        break
        
        if threatened_drones:
            # Move to protective positions near threatened drones
            # Find the closest threatened drone
            closest_drone = min(threatened_drones, 
                               key=lambda d: np.linalg.norm(d.pos - self.pos))
            
            # Get the direction from the closest turret to the threatened drone
            closest_turret = min(turrets, 
                                key=lambda t: np.linalg.norm(t.pos - closest_drone.pos))
            
            threat_direction = closest_drone.pos - closest_turret.pos
            distance = np.linalg.norm(threat_direction)
            
            if distance > 0:
                threat_direction /= distance
                
                # Position self between turret and drone
                intercept_pos = closest_drone.pos - threat_direction * 0.03
                
                # Move to intercept position
                direction = intercept_pos - self.pos
                distance = np.linalg.norm(direction)
                
                if distance > 0:
                    direction /= distance
                    protect_force = direction * self.max_speed
                    self.force += protect_force
                    self.force_applied = True
    
    def _execute_support_behavior(self, drones, targets, obstacles, turrets, gis):
        """Execute support-specific behavior."""
        # Support drones help maintain formation and coordination
        
        # Find the center of the drone swarm
        if not drones:
            return
        
        swarm_center = np.zeros(2)
        count = 0
        
        for drone in drones:
            if drone.alive:
                swarm_center += drone.pos
                count += 1
        
        if count > 0:
            swarm_center /= count
            
            # Calculate ideal position based on swarm distribution
            # Support drones try to fill gaps in the formation
            
            # Find gaps in the formation
            positions = np.array([drone.pos for drone in drones if drone.alive])
            
            # Calculate average distance between drones
            distances = []
            for i in range(len(positions)):
                for j in range(i+1, len(positions)):
                    distances.append(np.linalg.norm(positions[i] - positions[j]))
            
            if distances:
                avg_distance = np.mean(distances)
                
                # Find the direction with fewest drones
                angles = np.linspace(0, 2*np.pi, 8, endpoint=False)
                directions = np.array([[np.cos(a), np.sin(a)] for a in angles])
                
                # Count drones in each direction
                direction_counts = np.zeros(len(directions))
                
                for drone_pos in positions:
                    rel_pos = drone_pos - swarm_center
                    if np.linalg.norm(rel_pos) > 0:
                        rel_pos /= np.linalg.norm(rel_pos)
                        
                        # Count contribution to each direction
                        for i, direction in enumerate(directions):
                            alignment = np.dot(rel_pos, direction)
                            if alignment > 0.7:  # Consider drones within ~45 degrees
                                direction_counts[i] += 1
                
                # Find direction with fewest drones
                min_idx = np.argmin(direction_counts)
                target_direction = directions[min_idx]
                
                # Set target position in that direction
                target_pos = swarm_center + target_direction * avg_distance
                
                # Create force towards this position
                direction = target_pos - self.pos
                distance = np.linalg.norm(direction)
                
                if distance > 0:
                    direction /= distance
                    formation_force = direction * self.max_speed
                    self.force += formation_force
                    self.force_applied = True

class EnhancedEnemyDrone(EnemyDrone):
    """Enhanced enemy drone with improved tactical AI."""
    
    def __init__(self, drone_id, x, y, config):
        """Initialize an enhanced enemy drone."""
        super().__init__(drone_id, x, y, config)
        self.tactical_level = np.random.uniform(0.6, 1.0)
        self.attack_pattern = np.random.choice([
            "direct", "flanking", "ambush", "swarm"
        ])
        
        # Override some parameters based on attack pattern
        if self.attack_pattern == "direct":
            self.max_speed *= 1.2
            self.attack_strength *= 1.3
        elif self.attack_pattern == "flanking":
            self.perception_range *= 1.3
            self.separation_strength *= 1.5
        elif self.attack_pattern == "ambush":
            self.attack_range *= 1.5
            self.cohesion_strength *= 0.5
        elif self.attack_pattern == "swarm":
            self.cohesion_strength *= 2.0
            self.alignment_strength *= 2.0
    
    def update(self, drones, targets, obstacles, turrets, gis):
        """Update enemy drone with enhanced tactical behavior."""
        # Check terrain and adapt
        if gis:
            elevation = gis.get_elevation(self.pos[0], self.pos[1])
            slope, aspect = gis.get_slope(self.pos[0], self.pos[1])
            
            # Use terrain to tactical advantage
            if slope > 25:  # Steep terrain
                self.max_speed *= 0.7  # Slow down on steep terrain
        
        # Execute pattern-specific behavior
        if self.attack_pattern == "direct":
            self._execute_direct_attack(drones, obstacles, turrets, gis)
        elif self.attack_pattern == "flanking":
            self._execute_flanking_attack(drones, obstacles, turrets, gis)
        elif self.attack_pattern == "ambush":
            self._execute_ambush_attack(drones, obstacles, turrets, gis)
        elif self.attack_pattern == "swarm":
            self._execute_swarm_attack(drones, obstacles, turrets, gis)
        
        # If no specific behavior executed, fall back to standard behavior
        if not self.force_applied:
            super().update(drones, targets, obstacles, turrets, gis)
    
    def _execute_direct_attack(self, drones, obstacles, turrets, gis):
        """Execute direct attack pattern."""
        target_drone = self._find_closest_friendly_drone(drones)
        if target_drone:
            # Simply charge directly at the target
            direction = target_drone.pos - self.pos
            distance = np.linalg.norm(direction)
            
            if distance > 0:
                direction /= distance
                attack_force = direction * self.max_speed
                self.force += attack_force
                self.force_applied = True
                
                # Attack if in range
                if distance < self.attack_range:
                    self._attack_nearby_drones(drones)
    
    def _execute_flanking_attack(self, drones, obstacles, turrets, gis):
        """Execute flanking attack pattern."""
        target_drone = self._find_closest_friendly_drone(drones)
        if not target_drone:
            return
        
        # Get target's velocity direction
        if np.linalg.norm(target_drone.velocity) > 0.1:
            target_dir = target_drone.velocity / np.linalg.norm(target_drone.velocity)
            
            # Calculate perpendicular direction for flanking
            flank_dir = np.array([-target_dir[1], target_dir[0]])
            
            # Choose side based on which one is closer to current position
            rel_pos = self.pos - target_drone.pos
            if np.dot(rel_pos, flank_dir) < 0:
                flank_dir = -flank_dir
            
            # Calculate flanking position
            flank_distance = 0.07  # Distance from target
            flank_pos = target_drone.pos + flank_dir * flank_distance
            
            # Move to flanking position
            direction = flank_pos - self.pos
            distance = np.linalg.norm(direction)
            
            if distance > 0:
                direction /= distance
                flank_force = direction * self.max_speed
                self.force += flank_force
                self.force_applied = True
                
                # Attack if close to target
                if np.linalg.norm(self.pos - target_drone.pos) < self.attack_range:
                    self._attack_nearby_drones(drones)
        else:
            # Target not moving, fall back to direct attack
            self._execute_direct_attack(drones, obstacles, turrets, gis)
    
    def _execute_ambush_attack(self, drones, obstacles, turrets, gis):
        """Execute ambush attack pattern."""
        # Find potential ambush positions
        if len(drones) == 0:
            return
        
        # Calculate probable paths of friendly drones
        friendly_positions = np.array([drone.pos for drone in drones if drone.alive])
        if len(friendly_positions) == 0:
            return
        
        # Find most promising ambush point
        # Prefer positions near obstacles for cover
        best_ambush_pos = None
        best_score = -np.inf
        
        # Sample potential ambush points
        for _ in range(10):
            # Pick a random friendly drone to ambush
            target_idx = np.random.randint(len(friendly_positions))
            target_pos = friendly_positions[target_idx]
            
            # Find nearby obstacles for cover
            nearby_obstacles = [obs for obs in obstacles 
                               if np.linalg.norm(np.array(obs.pos) - target_pos) < 0.15]
            
            if nearby_obstacles:
                # Use obstacle for cover
                obstacle = nearby_obstacles[0]
                
                # Calculate position on the opposite side of obstacle from drone
                obs_to_drone = target_pos - np.array(obstacle.pos)
                if np.linalg.norm(obs_to_drone) > 0:
                    obs_to_drone /= np.linalg.norm(obs_to_drone)
                    ambush_pos = np.array(obstacle.pos) - obs_to_drone * obstacle.radius * 1.2
                    
                    # Score this position
                    # Consider: distance from self, coverage, distance to target
                    dist_to_self = np.linalg.norm(ambush_pos - self.pos)
                    dist_to_target = np.linalg.norm(ambush_pos - target_pos)
                    
                    # Check if obstacle blocks line of sight
                    has_los = True
                    if gis:
                        has_los = gis.is_line_of_sight_clear(ambush_pos, target_pos)
                    
                    # Calculate score (lower distance is better, no LOS is better for ambush)
                    score = -dist_to_self - dist_to_target * 0.5
                    if not has_los:
                        score += 20  # Big bonus for being hidden
                    
                    if score > best_score:
                        best_score = score
                        best_ambush_pos = ambush_pos
        
        if best_ambush_pos is not None:
            # Move to ambush position
            direction = best_ambush_pos - self.pos
            distance = np.linalg.norm(direction)
            
            if distance > 0:
                direction /= distance
                ambush_force = direction * self.max_speed
                self.force += ambush_force
                self.force_applied = True
                
                # If close enough to ambush position, look for targets
                if distance < 0.02:
                    close_drones = [drone for drone in drones
                                  if drone.alive and np.linalg.norm(drone.pos - self.pos) < self.attack_range]
                    
                    if close_drones:
                        self._attack_nearby_drones(drones)
    
    def _execute_swarm_attack(self, drones, obstacles, turrets, gis):
        """Execute coordinated swarm attack with other enemy drones."""
        # Find all enemy drones to coordinate with
        enemy_drones = [drone for drone in drones 
                       if not drone.alive and isinstance(drone, EnemyDrone)]
        
        if len(enemy_drones) <= 1:
            # Not enough enemy drones for swarm tactics
            self._execute_direct_attack(drones, obstacles, turrets, gis)
            return
        
        # Find friendly drones to attack
        friendly_drones = [drone for drone in drones 
                          if drone.alive and not isinstance(drone, EnemyDrone)]
        
        if not friendly_drones:
            return
        
        # Calculate swarm center
        swarm_center = np.zeros(2)
        for drone in enemy_drones:
            swarm_center += drone.pos
        swarm_center /= len(enemy_drones)
        
        # Choose closest friendly drone as swarm target
        target_drone = min(friendly_drones, 
                          key=lambda d: np.linalg.norm(swarm_center - d.pos))
        
        # Calculate ideal position in the swarm
        # Distribute enemy drones around the target
        num_enemies = len(enemy_drones)
        idx = enemy_drones.index(self)
        angle = 2 * np.pi * idx / num_enemies
        
        # Calculate position in the formation
        formation_radius = 0.05
        formation_pos = target_drone.pos + np.array([
            np.cos(angle), np.sin(angle)
        ]) * formation_radius
        
        # Move to formation position
        direction = formation_pos - self.pos
        distance = np.linalg.norm(direction)
        
        if distance > 0:
            direction /= distance
            swarm_force = direction * self.max_speed
            self.force += swarm_force
            self.force_applied = True
            
            # Attack if close enough to target
            if np.linalg.norm(self.pos - target_drone.pos) < self.attack_range:
                self._attack_nearby_drones(drones)

class EnhancedSimulation(Simulation):
    """Enhanced simulation with geographic data integration."""
    
    def __init__(self, config=None):
        """Initialize an enhanced simulation."""
        super().__init__(config)
        self.geo_data = GeoDataManager()
        self.geo_data.load_terrain_data()
        self.geo_data.load_map_data()
        self.load_geo_entities()
        
        # Additional simulation parameters
        self.time_of_day = "day"  # "day", "dusk", "night"
        self.weather_condition = "clear"  # "clear", "cloudy", "rain", "fog"
        self.visibility = 1.0  # 0.0-1.0
        
        # Tactical parameters
        self.mission_type = "strike"  # "strike", "recon", "defend", "escort"
        self.threat_level = "medium"  # "low", "medium", "high"
        
        # Update visibility based on time and weather
        if self.time_of_day == "dusk":
            self.visibility *= 0.7
        elif self.time_of_day == "night":
            self.visibility *= 0.4
            
        if self.weather_condition == "cloudy":
            self.visibility *= 0.8
        elif self.weather_condition == "rain":
            self.visibility *= 0.6
        elif self.weather_condition == "fog":
            self.visibility *= 0.3
    
    def load_geo_entities(self):
        """Load entities from geographic data."""
        # Load obstacles
        geo_obstacles = self.geo_data.convert_to_simulation_obstacles()
        for obs_data in geo_obstacles:
            obstacle = Obstacle(obs_data["pos"][0], obs_data["pos"][1], 
                               obs_data["radius"])
            self.obstacles.append(obstacle)
        
        # Load turrets
        geo_turrets = self.geo_data.convert_to_simulation_turrets()
        for turret_data in geo_turrets:
            turret = Turret(turret_data["pos"][0], turret_data["pos"][1],
                           turret_data["range"], turret_data["fire_rate"])
            self.turrets.append(turret)
        
        # Load targets
        geo_targets = self.geo_data.convert_to_simulation_targets()
        for target_data in geo_targets:
            target = Target(target_data["pos"][0], target_data["pos"][1],
                           target_data["value"])
            self.targets.append(target)
    
    def create_drones(self, enhanced=True):
        """Create drones for the simulation with enhanced behavior."""
        num_drones = self.config["NUM_DRONES"]
        
        # Determine valid starting area (friendly territory)
        valid_area = {
            "x_min": 0.1,
            "x_max": 0.3,
            "y_min": 0.1,
            "y_max": 0.5
        }
        
        for i in range(num_drones):
            # Generate position in valid starting area
            x = np.random.uniform(valid_area["x_min"], valid_area["x_max"])
            y = np.random.uniform(valid_area["y_min"], valid_area["y_max"])
            
            if enhanced:
                drone = EnhancedDrone(i, x, y, self.config)
            else:
                drone = Drone(i, x, y, self.config)
                
            self.drones.append(drone)
    
    def create_enemy_drones(self, num_enemies=3, enhanced=True):
        """Create enemy drones."""
        # Determine valid starting area (enemy territory)
        valid_area = {
            "x_min": 0.7,
            "x_max": 0.9,
            "y_min": 0.1,
            "y_max": 0.5
        }
        
        start_id = len(self.drones)
        
        for i in range(num_enemies):
            # Generate position in valid starting area
            x = np.random.uniform(valid_area["x_min"], valid_area["x_max"])
            y = np.random.uniform(valid_area["y_min"], valid_area["y_max"])
            
            if enhanced:
                enemy = EnhancedEnemyDrone(start_id + i, x, y, self.config)
            else:
                enemy = EnemyDrone(start_id + i, x, y, self.config)
                
            self.drones.append(enemy)
    
    def step(self):
        """Advance the simulation by one step."""
        # Apply time effects
        if self.time_of_day == "night":
            # Reduce perception range at night
            for drone in self.drones:
                if hasattr(drone, 'perception_range'):
                    drone.perception_range_original = drone.perception_range
                    drone.perception_range *= self.visibility
        
        # Apply weather effects
        if self.weather_condition in ["rain", "fog"]:
            # Reduce speed in bad weather
            for drone in self.drones:
                if hasattr(drone, 'max_speed'):
                    drone.max_speed_original = drone.max_speed
                    drone.max_speed *= self.visibility
        
        # Run standard simulation step
        super().step()
        
        # Restore original values
        if self.time_of_day == "night":
            for drone in self.drones:
                if hasattr(drone, 'perception_range_original'):
                    drone.perception_range = drone.perception_range_original
        
        if self.weather_condition in ["rain", "fog"]:
            for drone in self.drones:
                if hasattr(drone, 'max_speed_original'):
                    drone.max_speed = drone.max_speed_original

def generate_tactical_visualization(simulation, step, is_final=False):
    """Generate enhanced tactical visualization with terrain and map data."""
    # Create figure with specified size and style
    fig, ax = plt.subplots(figsize=(12, 10), facecolor='#0a1929')
    ax.set_facecolor('#132f4c')
    
    # Render terrain if available
    if simulation.geo_data and simulation.geo_data.dem_data is not None:
        simulation.geo_data.render_terrain_map(ax=ax, with_contours=True)
    
    # Render map data if available
    if simulation.geo_data and simulation.geo_data.map_data is not None:
        simulation.geo_data.render_map_data(ax=ax)
    
    # Grid and border styling for military look
    ax.grid(color='#1e4976', linestyle='--', linewidth=0.5, alpha=0.5)
    
    # Set plot limits and labels with military styling
    field_size = simulation.config["FIELD_SIZE"]
    ax.set_xlim(0, field_size)
    ax.set_ylim(0, field_size)
    
    # Create title based on mission parameters
    mission_title = f"NATO DRONE SWARM OPERATION"
    if hasattr(simulation, 'mission_type'):
        mission_type_name = simulation.mission_type.upper()
        mission_title = f"NATO {mission_type_name} OPERATION"
    
    # Add time and weather info
    time_weather = ""
    if hasattr(simulation, 'time_of_day') and hasattr(simulation, 'weather_condition'):
        time_weather = f" - {simulation.time_of_day.upper()} / {simulation.weather_condition.upper()}"
    
    # Title and axis labels in military style
    ax.set_title(f"{mission_title}{time_weather} - T+{step:03d}", 
                color='#66b2ff', fontsize=14, fontweight='bold')
    
    # Coordinate axes in military style
    ax.set_xlabel("X Position (km)", color='#66b2ff')
    ax.set_ylabel("Y Position (km)", color='#66b2ff')
    ax.tick_params(colors='#66b2ff', which='both')
    
    # Military grid squares with coordinates
    for spine in ax.spines.values():
        spine.set_color('#173a5e')
        spine.set_linewidth(2)
    
    # Plot obstacles
    for obstacle in simulation.obstacles:
        circle = plt.Circle(
            obstacle.pos, 
            obstacle.radius, 
            color='#654321', 
            alpha=0.8
        )
        ax.add_patch(circle)
    
    # Plot turrets
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
        else:
            # Show destroyed targets
            ax.scatter(target.pos[0], target.pos[1], s=80, 
                     marker='*', color='#ffaa00', alpha=0.9)
            ax.text(target.pos[0], target.pos[1] + 0.02, f"T{i+1} NEUTRALIZED", 
                   ha='center', va='bottom', color='#ffaa00', 
                   fontsize=8, alpha=0.9)
    
    # Plot drones with enhanced styling
    from config import STATUS_COLORS, DEFAULT_COLOR
    
    for i, drone in enumerate(simulation.drones):
        if drone.alive:
            # Use role-based colors for enhanced drones
            if hasattr(drone, 'operational_role'):
                role_colors = {
                    "scout": "#00ffff",  # Cyan
                    "attacker": "#ff0000",  # Red
                    "defender": "#0000ff",  # Blue
                    "support": "#ffff00",  # Yellow
                }
                color = role_colors.get(drone.operational_role, 
                                      STATUS_COLORS.get(drone.status, DEFAULT_COLOR))
            else:
                color = STATUS_COLORS.get(drone.status, DEFAULT_COLOR)
            
            # Different style for enemy drones
            if isinstance(drone, EnemyDrone):
                marker = '^'  # Triangle
                ms = 10
                color = '#ff0000'  # Red
            else:
                marker = 'o'  # Circle
                ms = 8
            
            # Plot the drone
            ax.scatter(drone.pos[0], drone.pos[1], 
                     marker=marker, s=ms**2, color=color, 
                     edgecolors='black', linewidths=1)
            
            # Draw velocity vector
            if np.linalg.norm(drone.velocity) > 0.1:
                velocity = drone.velocity / np.linalg.norm(drone.velocity) * 0.02
                ax.arrow(
                    drone.pos[0], 
                    drone.pos[1], 
                    velocity[0], 
                    velocity[1], 
                    head_width=0.01, 
                    head_length=0.015, 
                    fc=color, 
                    ec='black',
                    linewidth=1
                )
            
            # Label drones
            if isinstance(drone, EnemyDrone):
                label = f"E{i+1}"
            else:
                label = f"{i+1}"
            
            ax.text(drone.pos[0], drone.pos[1] + 0.02, label, 
                   ha='center', va='bottom', color='white', 
                   fontsize=8, fontweight='bold')
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
    
    # Add custom legend
    legend_elements = []
    
    # Add drone types
    legend_elements.append(Line2D([0], [0], marker='o', color='w', 
                                 markerfacecolor='#00aa00', markersize=8,
                                 label='Friendly Drone'))
    
    legend_elements.append(Line2D([0], [0], marker='^', color='w', 
                                 markerfacecolor='#ff0000', markersize=8,
                                 label='Enemy Drone'))
    
    # Add drone roles if enhanced
    has_roles = any(hasattr(d, 'operational_role') for d in simulation.drones if d.alive)
    if has_roles:
        role_colors = {
            "scout": "#00ffff",  # Cyan
            "attacker": "#ff0000",  # Red
            "defender": "#0000ff",  # Blue
            "support": "#ffff00",  # Yellow
        }
        
        for role, color in role_colors.items():
            legend_elements.append(Line2D([0], [0], marker='o', color='w', 
                                         markerfacecolor=color, markersize=8,
                                         label=f'{role.capitalize()} Role'))
    
    # Add other elements
    legend_elements.extend([
        Line2D([0], [0], marker='s', color='w', markerfacecolor='#00aa00', 
              markersize=8, label='Target'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ff2a2a', 
              markersize=8, label='Air Defense'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#654321', 
              markersize=8, label='Terrain')
    ])
    
    legend = ax.legend(handles=legend_elements, loc='upper right', 
                      title="NATO ELEMENTS", framealpha=0.7,
                      facecolor='#173a5e', edgecolor='#66b2ff')
    legend.get_title().set_color('#66b2ff')
    for text in legend.get_texts():
        text.set_color('#e0e0e0')
    
    # Add mission time
    mission_time = f"T+{step:03d}"
    ax.text(0.02, 0.98, f"MISSION TIME: {mission_time}", 
           transform=ax.transAxes, color='#66b2ff', 
           fontsize=10, verticalalignment='top',
           bbox=dict(boxstyle="round,pad=0.3", fc='#173a5e', ec='#66b2ff', alpha=0.7))
    
    # Add mission status
    stats = simulation.get_statistics()
    drones_text = f"DRONES: {stats['drones_alive']}/{stats['total_drones']}"
    targets_text = f"TARGETS: {stats['targets_destroyed']}/{stats['total_targets']}"
    
    status_box = f"{drones_text}\n{targets_text}"
    if stats['mission_complete']:
        status_box += "\nMISSION COMPLETE"
    elif stats['mission_failed']:
        status_box += "\nMISSION FAILED"
    
    ax.text(0.02, 0.02, status_box, 
           transform=ax.transAxes, color='#66b2ff', 
           fontsize=10, verticalalignment='bottom',
           bbox=dict(boxstyle="round,pad=0.3", fc='#173a5e', ec='#66b2ff', alpha=0.7))
    
    # Visibility conditions
    if hasattr(simulation, 'visibility') and simulation.visibility < 0.7:
        # Apply a semi-transparent overlay to simulate reduced visibility
        visibility_rect = plt.Rectangle((0, 0), 1, 1, 
                                      transform=ax.transAxes,
                                      color='black', 
                                      alpha=0.7 - simulation.visibility)
        ax.add_patch(visibility_rect)
        
        ax.text(0.98, 0.98, f"VISIBILITY: {int(simulation.visibility*100)}%", 
               transform=ax.transAxes, color='#ff6600', 
               fontsize=10, ha='right', va='top',
               bbox=dict(boxstyle="round,pad=0.3", fc='#173a5e', ec='#ff6600', alpha=0.7))
    
    return fig

def run_enhanced_simulation(config=None, num_steps=200, with_enemy_drones=True, 
                          time_of_day="day", weather="clear", mission_type="strike",
                          output_dir=OUTPUT_DIR, save_interval=10):
    """Run an enhanced simulation with realistic terrain and advanced tactical behavior."""
    if config is None:
        config = DEFAULT_CONFIG.copy()
    
    # Initialize the enhanced simulation
    simulation = EnhancedSimulation(config)
    simulation.time_of_day = time_of_day
    simulation.weather_condition = weather
    simulation.mission_type = mission_type
    
    # Create friendly drones
    simulation.create_drones(enhanced=True)
    
    # Add enemy drones if requested
    if with_enemy_drones:
        num_enemies = max(1, config["NUM_DRONES"] // 3)
        simulation.create_enemy_drones(num_enemies, enhanced=True)
    
    # Run the simulation
    for step in range(num_steps):
        if simulation.is_complete():
            break
        
        simulation.step()
        
        # Save visualization at intervals
        if step % save_interval == 0 or step == num_steps - 1 or simulation.is_complete():
            is_final = step == num_steps - 1 or simulation.is_complete()
            fig = generate_tactical_visualization(simulation, step, is_final)
            
            # Save the visualization
            filename = f"tactical_map_{step:03d}.png"
            plt.savefig(os.path.join(output_dir, filename), 
                       dpi=100, bbox_inches='tight')
            plt.close(fig)
            
            print(f"Step {step+1}/{num_steps} completed.")
    
    # Final stats
    stats = simulation.get_statistics()
    print("\nSimulation completed.")
    print(f"Drones remaining: {stats['drones_alive']}/{stats['total_drones']}")
    print(f"Targets destroyed: {stats['targets_destroyed']}/{stats['total_targets']}")
    if stats['mission_complete']:
        print("Mission status: SUCCESS")
    elif stats['mission_failed']:
        print("Mission status: FAILED")
    else:
        print("Mission status: INCOMPLETE")
    
    return simulation

# Example usage
if __name__ == "__main__":
    run_enhanced_simulation(
        with_enemy_drones=True,
        time_of_day="day",
        weather="clear",
        mission_type="strike"
    )