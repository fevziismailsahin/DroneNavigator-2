"""
NATO Military Drone Swarm Simulation - Geographic Data Manager

This module handles the integration of real-world geographical data into the simulation,
including terrain analysis, map rendering, and spatial coordinate transformations.
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
import matplotlib.colors as mcolors
from matplotlib.colors import LightSource
import math

# Constants for coordinate transformations
EARTH_RADIUS = 6371000  # meters

class GeoDataManager:
    """
    Manages geographical data for the NATO Military Drone Swarm Simulation.
    Provides integration of real-world maps, terrain analysis, and coordinates.
    """
    
    def __init__(self, data_dir="geo_data"):
        """
        Initialize the geographic data manager.
        
        Args:
            data_dir (str): Directory for geographic data files
        """
        self.data_dir = data_dir
        self.dem_data = None  # Digital Elevation Model data
        self.map_data = None  # Vector map data
        self.terrain_data = None  # Terrain features
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Default bounds (degrees) - Ukrainian conflict area
        self.default_bounds = {
            "north": 52.5,  # North latitude
            "south": 44.0,  # South latitude
            "east": 40.0,    # East longitude
            "west": 22.0     # West longitude
        }
        
        # Initialize synthetic terrain if no data available
        self._initialize_synthetic_terrain()

    def load_map_data(self, geojson_file=None):
        """
        Load map data from a GeoJSON file.
        
        Args:
            geojson_file (str): Path to GeoJSON file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if geojson_file and os.path.exists(geojson_file):
                self.map_data = gpd.read_file(geojson_file)
                return True
            else:
                # Use built-in synthetic data if no file specified
                return self._generate_synthetic_map_data()
        except Exception as e:
            print(f"Error loading map data: {e}")
            return False
    
    def load_terrain_data(self, terrain_file=None):
        """
        Load terrain data from a file.
        
        Args:
            terrain_file (str): Path to terrain data file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if terrain_file and os.path.exists(terrain_file):
                # Load actual terrain data if available
                try:
                    import rasterio
                    with rasterio.open(terrain_file) as src:
                        self.dem_data = src.read(1)
                        self.terrain_transform = src.transform
                    return True
                except Exception as e:
                    print(f"Error loading terrain file: {e}")
                    return self._generate_synthetic_terrain_data()
            else:
                # Generate synthetic terrain if no data provided
                return self._generate_synthetic_terrain_data()
        except Exception as e:
            print(f"Error loading terrain data: {e}")
            return False
    
    def _initialize_synthetic_terrain(self):
        """Initialize synthetic terrain data for simulation."""
        self._generate_synthetic_terrain_data()
        self._generate_synthetic_map_data()
    
    def _generate_synthetic_terrain_data(self):
        """
        Generate synthetic terrain data for the simulation.
        Creates realistic-looking terrain for testing without requiring actual data.
        
        Returns:
            bool: True if successful
        """
        try:
            # Create a grid for terrain data
            grid_size = 100
            x = np.linspace(0, 1, grid_size)
            y = np.linspace(0, 1, grid_size)
            X, Y = np.meshgrid(x, y)
            
            # Generate synthetic mountainous terrain using perlin-like noise
            from numpy.random import RandomState
            rng = RandomState(42)  # Fixed seed for reproducibility
            
            # Multiple frequency components for realistic terrain
            z = np.zeros_like(X)
            
            # Large features (mountains, valleys)
            freq1 = 5
            amp1 = 100
            phase1 = rng.random((2, 2)) * 2 * np.pi
            z += amp1 * np.cos(freq1 * X + phase1[0, 0]) * np.cos(freq1 * Y + phase1[0, 1])
            
            # Medium features (hills, ridges)
            freq2 = 10
            amp2 = 50
            phase2 = rng.random((2, 2)) * 2 * np.pi
            z += amp2 * np.cos(freq2 * X + phase2[0, 0]) * np.cos(freq2 * Y + phase2[0, 1])
            
            # Small features (local variations)
            freq3 = 20
            amp3 = 25
            phase3 = rng.random((2, 2)) * 2 * np.pi
            z += amp3 * np.cos(freq3 * X + phase3[0, 0]) * np.cos(freq3 * Y + phase3[0, 1])
            
            # Add random noise for texture
            z += rng.normal(0, 5, size=X.shape)
            
            # Create some flat areas for military operations
            # Add several plateau-like areas (potential military bases)
            for _ in range(3):
                cx, cy = rng.random(2)
                radius = rng.uniform(0.05, 0.1)
                mask = ((X - cx)**2 + (Y - cy)**2) < radius**2
                z[mask] = np.mean(z[mask]) + rng.uniform(-10, 10)
            
            # Add valleys (potential invasion routes)
            for _ in range(2):
                cx, cy = rng.random(2)
                dx, dy = rng.random(2) - 0.5
                length = 0.3
                width = 0.03
                dir_vec = np.array([dx, dy])
                dir_vec = dir_vec / np.linalg.norm(dir_vec) * length
                
                # Define valley path
                for t in np.linspace(0, 1, 50):
                    vx = cx + t * dir_vec[0]
                    vy = cy + t * dir_vec[1]
                    mask = ((X - vx)**2 + (Y - vy)**2) < width**2
                    if np.any(mask):
                        valley_height = np.min(z[mask]) - 20
                        z[mask] = np.maximum(z[mask] * 0.7, valley_height)
            
            # Normalize to reasonable elevation range (meters)
            z = (z - np.min(z)) / (np.max(z) - np.min(z)) * 1000
            
            # Store the terrain data
            self.dem_data = z
            self.terrain_data = {
                "elevation": z,
                "resolution": (1.0/grid_size, 1.0/grid_size)
            }
            
            return True
        except Exception as e:
            print(f"Error generating synthetic terrain: {e}")
            return False
    
    def _generate_synthetic_map_data(self):
        """
        Generate synthetic map data for the simulation.
        Creates simulated countries, roads, and key features for military scenarios.
        
        Returns:
            bool: True if successful
        """
        try:
            # Create synthetic geopolitical boundaries
            from shapely.geometry import Polygon, LineString, Point
            import geopandas as gpd
            from numpy.random import RandomState
            
            rng = RandomState(42)  # Fixed seed for reproducibility
            
            # Generate country/region polygons
            countries = []
            
            # Country 1 - Main area of operations
            country1_coords = [
                (0.1, 0.1), (0.4, 0.1), (0.5, 0.3), 
                (0.4, 0.5), (0.2, 0.5), (0.1, 0.3), (0.1, 0.1)
            ]
            countries.append({
                "geometry": Polygon(country1_coords),
                "name": "Nordland",
                "status": "Allied"
            })
            
            # Country 2 - Conflict zone
            country2_coords = [
                (0.4, 0.1), (0.7, 0.1), (0.8, 0.3),
                (0.7, 0.5), (0.4, 0.5), (0.5, 0.3), (0.4, 0.1)
            ]
            countries.append({
                "geometry": Polygon(country2_coords),
                "name": "Easteria",
                "status": "Conflict Zone"
            })
            
            # Country 3 - Hostile territory
            country3_coords = [
                (0.7, 0.1), (0.9, 0.1), (0.9, 0.5),
                (0.7, 0.5), (0.8, 0.3), (0.7, 0.1)
            ]
            countries.append({
                "geometry": Polygon(country3_coords),
                "name": "Redland",
                "status": "Hostile"
            })
            
            # Generate roads/supply lines
            roads = []
            
            # Main highway
            roads.append({
                "geometry": LineString([(0.1, 0.3), (0.4, 0.3), (0.7, 0.3), (0.9, 0.3)]),
                "type": "Highway",
                "name": "Main Supply Route"
            })
            
            # Secondary roads
            roads.append({
                "geometry": LineString([(0.3, 0.1), (0.3, 0.5)]),
                "type": "Road",
                "name": "Northern Access"
            })
            
            roads.append({
                "geometry": LineString([(0.6, 0.1), (0.6, 0.5)]),
                "type": "Road",
                "name": "Southern Access"
            })
            
            # Generate military positions
            positions = []
            
            # Allied bases
            positions.append({
                "geometry": Point(0.2, 0.2),
                "type": "Base",
                "name": "Alpha Base",
                "faction": "Allied"
            })
            
            positions.append({
                "geometry": Point(0.3, 0.4),
                "type": "Base",
                "name": "Bravo Base",
                "faction": "Allied"
            })
            
            # Conflict zone positions
            positions.append({
                "geometry": Point(0.5, 0.2),
                "type": "Forward Operating Base",
                "name": "Charlie FOB",
                "faction": "Allied"
            })
            
            positions.append({
                "geometry": Point(0.6, 0.4),
                "type": "Checkpoint",
                "name": "Delta Checkpoint",
                "faction": "Contested"
            })
            
            # Enemy positions
            positions.append({
                "geometry": Point(0.75, 0.25),
                "type": "Base",
                "name": "Enemy Command",
                "faction": "Hostile"
            })
            
            positions.append({
                "geometry": Point(0.8, 0.4),
                "type": "Artillery",
                "name": "Enemy Artillery",
                "faction": "Hostile"
            })
            
            # Create GeoDataFrames
            countries_gdf = gpd.GeoDataFrame(countries)
            roads_gdf = gpd.GeoDataFrame(roads)
            positions_gdf = gpd.GeoDataFrame(positions)
            
            # Store as map data
            self.map_data = {
                "countries": countries_gdf,
                "roads": roads_gdf,
                "positions": positions_gdf
            }
            
            return True
        except Exception as e:
            print(f"Error generating synthetic map: {e}")
            return False
    
    def get_elevation(self, x, y, normalized=True):
        """
        Get terrain elevation at a specified point.
        
        Args:
            x (float): X coordinate (0-1 normalized or lon)
            y (float): Y coordinate (0-1 normalized or lat)
            normalized (bool): If True, input is in normalized coordinates
            
        Returns:
            float: Elevation value
        """
        if self.dem_data is None:
            return 0.0
        
        if not normalized:
            # Convert from geographic coordinates to normalized coordinates
            x, y = self._geo_to_normalized(x, y)
        
        # Get indices in elevation grid
        grid_size = self.dem_data.shape
        ix = int(x * (grid_size[1] - 1))
        iy = int(y * (grid_size[0] - 1))
        
        # Clamp to valid range
        ix = max(0, min(ix, grid_size[1] - 1))
        iy = max(0, min(iy, grid_size[0] - 1))
        
        return self.dem_data[iy, ix]
    
    def get_slope(self, x, y, normalized=True):
        """
        Calculate terrain slope at a position.
        
        Args:
            x (float): X coordinate
            y (float): Y coordinate
            normalized (bool): If True, input is in normalized coordinates
            
        Returns:
            tuple: (slope_degrees, aspect_degrees)
        """
        if self.dem_data is None:
            return (0.0, 0.0)
        
        if not normalized:
            # Convert from geographic coordinates to normalized coordinates
            x, y = self._geo_to_normalized(x, y)
        
        # Get indices in elevation grid
        grid_size = self.dem_data.shape
        sample_dist = 0.01  # Sample distance in normalized coordinates
        
        # Get elevations at sample points
        e_center = self.get_elevation(x, y, normalized=True)
        e_north = self.get_elevation(x, y + sample_dist, normalized=True)
        e_east = self.get_elevation(x + sample_dist, y, normalized=True)
        
        # Calculate slope components
        dy = (e_north - e_center) / sample_dist
        dx = (e_east - e_center) / sample_dist
        
        # Calculate slope and aspect
        slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
        slope_deg = np.degrees(slope_rad)
        
        # Calculate aspect (direction of slope)
        aspect_rad = np.arctan2(dy, dx)
        aspect_deg = (np.degrees(aspect_rad) + 90) % 360
        
        return (slope_deg, aspect_deg)
    
    def is_line_of_sight_clear(self, pos1, pos2, observer_height=10.0, target_height=0.0, normalized=True):
        """
        Check if there's a clear line of sight between two positions.
        
        Args:
            pos1 (tuple): First position (x, y)
            pos2 (tuple): Second position (x, y)
            observer_height (float): Height of observer above terrain
            target_height (float): Height of target above terrain
            normalized (bool): If True, input is in normalized coordinates
            
        Returns:
            bool: True if line of sight is clear, False otherwise
        """
        if self.dem_data is None:
            return True
        
        # Convert positions if needed
        if not normalized:
            pos1 = self._geo_to_normalized(pos1[0], pos1[1])
            pos2 = self._geo_to_normalized(pos2[0], pos2[1])
        
        # Calculate distance
        distance = np.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2)
        
        # Get number of sample points based on distance
        num_samples = max(10, int(distance * 100))
        
        # Get elevations at endpoints
        elev1 = self.get_elevation(pos1[0], pos1[1], normalized=True)
        elev2 = self.get_elevation(pos2[0], pos2[1], normalized=True)
        
        # Adjust for heights above terrain
        elev1 += observer_height
        elev2 += target_height
        
        # Sample points along the line
        for i in range(1, num_samples):
            t = i / (num_samples - 1)
            x = pos1[0] + t * (pos2[0] - pos1[0])
            y = pos1[1] + t * (pos2[1] - pos1[1])
            
            # Get elevation at sample point
            elev = self.get_elevation(x, y, normalized=True)
            
            # Calculate height of line of sight at this distance
            line_height = elev1 + t * (elev2 - elev1)
            
            # Check if terrain blocks line of sight
            if elev > line_height:
                return False
        
        return True
    
    def _geo_to_normalized(self, lon, lat):
        """
        Convert geographic coordinates to normalized simulation coordinates.
        
        Args:
            lon (float): Longitude in degrees
            lat (float): Latitude in degrees
            
        Returns:
            tuple: (x, y) in normalized coordinates (0-1)
        """
        bounds = self.default_bounds
        
        # Normalize to 0-1 range
        x = (lon - bounds["west"]) / (bounds["east"] - bounds["west"])
        y = (lat - bounds["south"]) / (bounds["north"] - bounds["south"])
        
        return (x, y)
    
    def _normalized_to_geo(self, x, y):
        """
        Convert normalized simulation coordinates to geographic coordinates.
        
        Args:
            x (float): X coordinate (0-1)
            y (float): Y coordinate (0-1)
            
        Returns:
            tuple: (longitude, latitude) in degrees
        """
        bounds = self.default_bounds
        
        # Convert from 0-1 to geographic coordinates
        lon = bounds["west"] + x * (bounds["east"] - bounds["west"])
        lat = bounds["south"] + y * (bounds["north"] - bounds["south"])
        
        return (lon, lat)
    
    def calculate_distance(self, lon1, lat1, lon2, lat2):
        """
        Calculate distance between two geographic points using Haversine formula.
        
        Args:
            lon1, lat1: Coordinates of first point in degrees
            lon2, lat2: Coordinates of second point in degrees
            
        Returns:
            float: Distance in meters
        """
        # Convert to radians
        lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        # Earth radius in meters
        return EARTH_RADIUS * c
    
    def render_terrain_map(self, ax=None, with_contours=True, colormap='terrain'):
        """
        Render terrain elevation data as a colored relief map.
        
        Args:
            ax (matplotlib.axes.Axes): Axes to plot on, or None for new figure
            with_contours (bool): Whether to add contour lines
            colormap (str): Name of matplotlib colormap to use
            
        Returns:
            matplotlib.axes.Axes: The axes with the plot
        """
        if self.dem_data is None:
            print("No terrain data available to render")
            return None
        
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create a LightSource object for shaded relief
        ls = LightSource(azdeg=315, altdeg=45)
        
        # Colorize the terrain
        rgb = ls.shade(self.dem_data, cmap=plt.get_cmap(colormap), 
                        blend_mode='soft', vert_exag=0.3)
        
        # Plot the terrain
        im = ax.imshow(rgb, origin='lower', extent=[0, 1, 0, 1])
        
        # Add contour lines if requested
        if with_contours:
            contour_levels = np.linspace(np.min(self.dem_data), np.max(self.dem_data), 10)
            contours = ax.contour(self.dem_data, levels=contour_levels, 
                                 colors='black', alpha=0.3, origin='lower', 
                                 extent=[0, 1, 0, 1])
            ax.clabel(contours, inline=True, fontsize=8, fmt='%1.0f')
        
        return ax
    
    def render_map_data(self, ax=None):
        """
        Render map data including borders, roads, and positions.
        
        Args:
            ax (matplotlib.axes.Axes): Axes to plot on, or None for new figure
            
        Returns:
            matplotlib.axes.Axes: The axes with the plot
        """
        if self.map_data is None:
            print("No map data available to render")
            return None
        
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 8))
        
        # Draw country polygons
        for idx, country in enumerate(self.map_data["countries"].itertuples()):
            # Choose color based on status
            if country.status == "Allied":
                color = 'blue'
                alpha = 0.2
            elif country.status == "Hostile":
                color = 'red'
                alpha = 0.2
            else:  # Conflict Zone
                color = 'orange'
                alpha = 0.2
            
            # Plot the polygon
            x, y = country.geometry.exterior.xy
            ax.fill(x, y, alpha=alpha, fc=color, ec='black', linewidth=1)
            
            # Add label at centroid
            centroid = country.geometry.centroid
            ax.text(centroid.x, centroid.y, country.name, 
                   ha='center', va='center', fontsize=10, fontweight='bold')
        
        # Draw roads
        for road in self.map_data["roads"].itertuples():
            x, y = road.geometry.xy
            if road.type == "Highway":
                ax.plot(x, y, 'k-', linewidth=2)
            else:
                ax.plot(x, y, 'k--', linewidth=1)
        
        # Draw military positions
        for pos in self.map_data["positions"].itertuples():
            x, y = pos.geometry.x, pos.geometry.y
            
            # Choose marker based on type and faction
            if pos.faction == "Allied":
                color = 'blue'
                marker = 's'  # square
            elif pos.faction == "Hostile":
                color = 'red'
                marker = '^'  # triangle
            else:  # Contested
                color = 'orange'
                marker = 'o'  # circle
            
            # Plot the marker
            ax.plot(x, y, marker=marker, markersize=8, color=color, 
                   markeredgecolor='black', markeredgewidth=1)
            
            # Add label
            ax.text(x, y + 0.02, pos.name, ha='center', va='bottom', 
                   fontsize=8, color='black', fontweight='bold')
        
        # Set axis labels and grid
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.grid(True, linestyle='--', alpha=0.3)
        
        return ax
    
    def render_full_map(self, show_terrain=True, show_features=True):
        """
        Render a complete map with terrain and features.
        
        Args:
            show_terrain (bool): Whether to show terrain
            show_features (bool): Whether to show map features
            
        Returns:
            matplotlib.figure.Figure: The figure with the map
        """
        fig, ax = plt.subplots(figsize=(12, 10), facecolor='#0a1929')
        
        # Set dark theme styling
        ax.set_facecolor('#132f4c')
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        
        # Add military-style grid
        ax.grid(color='#1e4976', linestyle='--', linewidth=0.5, alpha=0.5)
        
        # Add terrain if available and requested
        if show_terrain and self.dem_data is not None:
            self.render_terrain_map(ax=ax, with_contours=True, colormap='gist_earth')
        
        # Add map features if available and requested
        if show_features and self.map_data is not None:
            self.render_map_data(ax=ax)
        
        # Set plot limits and labels with military styling
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        # Title and axis labels in military style
        ax.set_title("NATO MILITARY OPERATIONAL AREA", 
                    color='#66b2ff', fontsize=14, fontweight='bold')
        
        # Coordinate axes in military style
        ax.set_xlabel("X Position (km)", color='#66b2ff')
        ax.set_ylabel("Y Position (km)", color='#66b2ff')
        ax.tick_params(colors='#66b2ff', which='both')
        
        # Military border with coordinates
        for spine in ax.spines.values():
            spine.set_color('#173a5e')
            spine.set_linewidth(2)
        
        return fig
    
    def convert_to_simulation_obstacles(self):
        """
        Convert terrain data into simulation obstacles.
        
        Returns:
            list: List of obstacle parameters for the simulation
        """
        obstacles = []
        
        if self.dem_data is None:
            return obstacles
        
        # Simplified version: Identify high elevation areas as obstacles
        from scipy import ndimage
        
        # Identify local maxima (hills, mountains) as potential obstacles
        data_max = ndimage.maximum_filter(self.dem_data, size=5)
        maxima = (self.dem_data == data_max)
        
        # Threshold for what counts as an obstacle (top 10% of elevations)
        elev_threshold = np.percentile(self.dem_data, 90)
        high_points = np.logical_and(maxima, self.dem_data > elev_threshold)
        
        # Get coordinates of obstacle points
        obstacle_points = np.where(high_points)
        
        for i in range(len(obstacle_points[0])):
            y, x = obstacle_points[0][i], obstacle_points[1][i]
            
            # Convert to normalized coordinates
            nx = x / (self.dem_data.shape[1] - 1)
            ny = y / (self.dem_data.shape[0] - 1)
            
            # Skip points too close to the edge
            if nx < 0.05 or nx > 0.95 or ny < 0.05 or ny > 0.95:
                continue
            
            # Get elevation at this point
            elev = self.dem_data[y, x]
            
            # Scale radius based on elevation (higher = larger obstacle)
            radius = 0.02 + 0.03 * (elev - elev_threshold) / (np.max(self.dem_data) - elev_threshold)
            
            obstacles.append({
                "pos": (nx, ny),
                "radius": radius,
                "type": "mountain" if elev > np.percentile(self.dem_data, 95) else "hill"
            })
        
        # Add obstacles from map data if available
        if self.map_data is not None:
            # Add hostile positions as obstacles
            if "positions" in self.map_data:
                for pos in self.map_data["positions"].itertuples():
                    if pos.faction == "Hostile":
                        obstacles.append({
                            "pos": (pos.geometry.x, pos.geometry.y),
                            "radius": 0.03,
                            "type": "enemy_base"
                        })
        
        return obstacles
    
    def convert_to_simulation_turrets(self):
        """
        Convert map data into simulation turrets/defense systems.
        
        Returns:
            list: List of turret parameters for the simulation
        """
        turrets = []
        
        if self.map_data is None:
            return turrets
        
        # Add turrets at hostile military positions
        if "positions" in self.map_data:
            for pos in self.map_data["positions"].itertuples():
                if pos.faction == "Hostile":
                    # Different types based on position type
                    if pos.type == "Artillery":
                        range_val = 0.2  # Long range
                        fire_rate = 0.01
                    else:
                        range_val = 0.15
                        fire_rate = 0.02
                    
                    turrets.append({
                        "pos": (pos.geometry.x, pos.geometry.y),
                        "range": range_val,
                        "fire_rate": fire_rate,
                        "name": pos.name
                    })
        
        # Ensure we have at least some turrets for gameplay
        if len(turrets) < 2:
            from numpy.random import RandomState
            rng = RandomState(42)
            
            # Add some default turrets in enemy territory
            for i in range(3):
                x = 0.7 + rng.random() * 0.2
                y = 0.1 + rng.random() * 0.4
                
                turrets.append({
                    "pos": (x, y),
                    "range": rng.uniform(0.1, 0.2),
                    "fire_rate": rng.uniform(0.01, 0.03),
                    "name": f"Defense System {i+1}"
                })
        
        return turrets
    
    def convert_to_simulation_targets(self):
        """
        Convert map data into simulation targets.
        
        Returns:
            list: List of target parameters for the simulation
        """
        targets = []
        
        if self.map_data is None:
            return targets
        
        # Add targets at hostile military positions
        if "positions" in self.map_data:
            for pos in self.map_data["positions"].itertuples():
                if pos.faction == "Hostile":
                    targets.append({
                        "pos": (pos.geometry.x, pos.geometry.y),
                        "value": 10 if pos.type == "Base" else 5,
                        "name": pos.name
                    })
        
        # Ensure we have at least some targets for gameplay
        if len(targets) < 3:
            from numpy.random import RandomState
            rng = RandomState(42)
            
            # Add some default targets in enemy territory
            for i in range(4):
                x = 0.7 + rng.random() * 0.2
                y = 0.1 + rng.random() * 0.4
                
                targets.append({
                    "pos": (x, y),
                    "value": rng.randint(5, 15),
                    "name": f"Target {i+1}"
                })
        
        return targets
    
    def export_geo_data(self, filename="simulation_geo_data.json"):
        """
        Export geographic data for the simulation.
        
        Args:
            filename (str): Output filename
            
        Returns:
            bool: True if successful
        """
        try:
            # Create data structure for export
            geo_data = {
                "obstacles": self.convert_to_simulation_obstacles(),
                "turrets": self.convert_to_simulation_turrets(),
                "targets": self.convert_to_simulation_targets(),
                "bounds": self.default_bounds
            }
            
            # Export to JSON
            with open(os.path.join(self.data_dir, filename), 'w') as f:
                json.dump(geo_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting geo data: {e}")
            return False

# Example usage
if __name__ == "__main__":
    # Initialize the geo data manager
    gdm = GeoDataManager()
    
    # Generate and load synthetic data
    gdm.load_terrain_data()
    gdm.load_map_data()
    
    # Render a full map
    fig = gdm.render_full_map()
    
    # Export data for simulation
    gdm.export_geo_data()
    
    # Show the map
    plt.savefig("tactical_map.png", dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    print("Geographic data manager initialized and map exported.")