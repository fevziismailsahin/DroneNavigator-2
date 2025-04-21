"""
Configuration settings for the drone swarm simulation.
"""

# Simulation Default Configuration
DEFAULT_CONFIG = {
    "FIELD_SIZE": 100.0,
    "NUM_DRONES": 10,
    "NUM_TARGETS": 3,
    "NUM_TURRETS": 3,
    "NUM_OBSTACLES": 5,
    "DRONE_MAX_SPEED": 2.0,
    "DRONE_MAX_FUEL": 600.0,
    "DRONE_FUEL_CONSUMPTION_RATE": 1.0,
    "DRONE_SENSOR_RANGE": 30.0,
    "DRONE_ATTACK_RANGE": 4.0,
    "DRONE_RADIUS": 0.5,
    "WEIGHT_COHESION": 0.02,
    "WEIGHT_SEPARATION": 0.2,
    "WEIGHT_ALIGNMENT": 0.05,
    "WEIGHT_TARGET_SEEKING": 1.0,
    "WEIGHT_OBSTACLE_AVOIDANCE": 2.5,
    "WEIGHT_TURRET_AVOIDANCE": 1.8,
    "TURRET_RANGE": 20.0,
    "TURRET_COOLDOWN": 8,
    "TURRET_DAMAGE": 100.0,
    "OBSTACLE_MIN_SIZE": 4.0,
    "OBSTACLE_MAX_SIZE": 8.0,
    "OBSTACLE_AVOIDANCE_DISTANCE": 12.0,
    "TARGET_ASSIGNMENT_LIMIT": 3,
    "SIMULATION_INTERVAL_MS": 50,  # Faster update for smoother GUI feel
    "MAX_SIMULATION_STEPS": 2000,
    "LOW_FUEL_THRESHOLD": 0.2,
    "DRONE_INITIAL_AVOID_FACTOR": 1.0,  # Base avoidance factor
    "DRONE_LEARNED_AVOID_INCREASE": 0.5  # How much avoidance increases per hit nearby
}

# Color configurations for visualization
STATUS_COLORS = {
    "Idle": "grey",
    "Moving": "blue",
    "Attacking": "orange",
    "Avoiding": "purple",
    "LowFuel": "yellow",
    "NoFuel": "black",
    "Destroyed": "red"
}

DEFAULT_COLOR = "cyan"
