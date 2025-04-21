"""
Matplotlib canvas for visualization of the drone swarm simulation.
"""

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')  # Set the backend
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PyQt5.QtWidgets import QSizePolicy

from config import STATUS_COLORS, DEFAULT_COLOR


class SimulationCanvas(FigureCanvas):
    """Canvas for visualizing the simulation."""
    
    def __init__(self, parent=None, width=5, height=5, dpi=100):
        """
        Initialize the simulation canvas.
        
        Args:
            parent: Parent widget
            width (int): Width in inches
            height (int): Height in inches
            dpi (int): Resolution in dots per inch
        """
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        
        # Initialize empty collections for all entities
        self.drone_markers = []
        self.target_markers = []
        self.obstacle_markers = []
        self.turret_markers = []
        self.trajectory_lines = []
        
        # Enhanced visual style
        self.fig.patch.set_facecolor('#f0f0f0')
        self.axes.set_facecolor('#e6e6e6')
        self.axes.grid(True, linestyle='--', alpha=0.7)
        
        super(SimulationCanvas, self).__init__(self.fig)
        self.setParent(parent)
        
        FigureCanvas.setSizePolicy(self,
                                  QSizePolicy.Expanding,
                                  QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
    
    def reset_plot(self):
        """Clear all markers and reset the plot."""
        self.axes.clear()
        self.drone_markers = []
        self.target_markers = []
        self.obstacle_markers = []
        self.turret_markers = []
        self.trajectory_lines = []
    
    def update_plot(self, simulation, field_size=100.0, show_trajectories=True):
        """
        Update the plot with current simulation state.
        
        Args:
            simulation: The simulation object
            field_size (float): Size of the simulation field
            show_trajectories (bool): Whether to show drone trajectories
        """
        # Clear previous plot
        self.reset_plot()
        
        # Set plot limits
        self.axes.set_xlim(0, field_size)
        self.axes.set_ylim(0, field_size)
        self.axes.set_title("Drone Swarm Simulation")
        self.axes.set_xlabel("X Position")
        self.axes.set_ylabel("Y Position")
        
        # Plot GIS data if available
        if simulation.gis and hasattr(simulation.gis, 'dem_array') and simulation.gis.dem_array is not None:
            try:
                # Simple heat map of terrain
                extent = [0, field_size, 0, field_size]  # Adjust as needed for your GIS data
                terrain = self.axes.imshow(
                    simulation.gis.dem_array,
                    cmap='terrain',
                    extent=extent,
                    alpha=0.4,
                    origin='lower'
                )
                # Could add a colorbar for elevation
                # self.fig.colorbar(terrain, ax=self.axes, label='Elevation (m)')
            except Exception as e:
                print(f"Error displaying terrain: {e}")
        
        # Plot obstacles
        for obstacle in simulation.obstacles:
            circle = plt.Circle(
                obstacle.pos, 
                obstacle.radius, 
                color='brown', 
                alpha=0.7
            )
            self.axes.add_patch(circle)
        
        # Plot turrets with range indicator
        for turret in simulation.turrets:
            # Draw turret
            turret_marker = plt.Circle(
                turret.pos, 
                1.0, 
                color='red', 
                alpha=0.9
            )
            self.axes.add_patch(turret_marker)
            
            # Draw range
            range_circle = plt.Circle(
                turret.pos, 
                turret.range, 
                color='red', 
                alpha=0.1, 
                fill=True
            )
            self.axes.add_patch(range_circle)
            
            # Draw cooldown indicator
            if turret.cooldown_timer > 0:
                cooldown_pct = turret.cooldown_timer / turret.cooldown_max
                arc = patches.Wedge(
                    turret.pos, 
                    1.5, 
                    0, 
                    360 * cooldown_pct, 
                    width=0.3, 
                    color='orange'
                )
                self.axes.add_patch(arc)
        
        # Plot targets
        for target in simulation.targets:
            if target.alive:
                target_marker = plt.Rectangle(
                    (target.pos[0] - 1.5, target.pos[1] - 1.5), 
                    3, 3, 
                    color='green', 
                    alpha=0.8
                )
                self.axes.add_patch(target_marker)
                
                # Show assigned drones count
                if target.assigned_drones > 0:
                    self.axes.text(
                        target.pos[0], 
                        target.pos[1] + 3, 
                        f"{target.assigned_drones}", 
                        ha='center', 
                        color='black', 
                        bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2')
                    )
        
        # Plot drones and their trajectories
        for drone in simulation.drones:
            # Get status color or default
            color = STATUS_COLORS.get(drone.status, DEFAULT_COLOR)
            
            # Plot drone
            if drone.alive:
                drone_marker = plt.Circle(
                    drone.pos, 
                    0.7, 
                    color=color, 
                    alpha=0.9
                )
                self.axes.add_patch(drone_marker)
                
                # Display drone ID
                self.axes.text(
                    drone.pos[0], 
                    drone.pos[1] + 1, 
                    f"{drone.id}", 
                    ha='center', 
                    va='center', 
                    color='white',
                    fontsize=8,
                    bbox=dict(facecolor=color, alpha=0.7, boxstyle='round,pad=0.1')
                )
                
                # Plot sensor range (optional, can be disabled for clarity)
                # sensor_range = plt.Circle(
                #     drone.pos, 
                #     drone.config["DRONE_SENSOR_RANGE"], 
                #     color=color, 
                #     alpha=0.05, 
                #     fill=True
                # )
                # self.axes.add_patch(sensor_range)
                
                # Plot trajectories if enabled
                if show_trajectories and len(drone.trajectory) > 1:
                    traj_x = [pos[0] for pos in drone.trajectory]
                    traj_y = [pos[1] for pos in drone.trajectory]
                    self.axes.plot(traj_x, traj_y, color=color, alpha=0.5, linewidth=1)
                
                # Plot velocity vector (direction)
                if np.linalg.norm(drone.velocity) > 0.1:
                    vel_norm = drone.velocity / np.linalg.norm(drone.velocity)
                    self.axes.arrow(
                        drone.pos[0], 
                        drone.pos[1], 
                        vel_norm[0] * 2, 
                        vel_norm[1] * 2, 
                        head_width=0.4, 
                        head_length=0.7, 
                        fc=color, 
                        ec=color
                    )
                
                # Display fuel gauge for low fuel drones
                if drone.status == "LowFuel":
                    fuel_pct = drone.fuel / drone.config["DRONE_MAX_FUEL"]
                    self.axes.add_patch(
                        patches.Rectangle(
                            (drone.pos[0] - 0.75, drone.pos[1] - 1.5), 
                            1.5 * fuel_pct, 
                            0.3, 
                            color='yellow'
                        )
                    )
            else:
                # Draw X for destroyed drones
                marker_size = 20
                self.axes.plot(
                    [drone.pos[0] - 0.5, drone.pos[0] + 0.5], 
                    [drone.pos[1] - 0.5, drone.pos[1] + 0.5], 
                    color='red', 
                    linewidth=2
                )
                self.axes.plot(
                    [drone.pos[0] - 0.5, drone.pos[0] + 0.5], 
                    [drone.pos[1] + 0.5, drone.pos[1] - 0.5], 
                    color='red', 
                    linewidth=2
                )
        
        # Add a legend for drone status colors
        legend_elements = [
            patches.Patch(facecolor=color, edgecolor='black', label=status)
            for status, color in STATUS_COLORS.items()
        ]
        self.axes.legend(handles=legend_elements, loc='upper right', title="Drone Status")
        
        self.fig.tight_layout()
        self.draw()


class SimulationToolbar(NavigationToolbar):
    """Custom toolbar for simulation canvas."""
    
    def __init__(self, canvas, parent):
        """
        Initialize the simulation toolbar.
        
        Args:
            canvas: The canvas to attach to
            parent: Parent widget
        """
        NavigationToolbar.__init__(self, canvas, parent)
