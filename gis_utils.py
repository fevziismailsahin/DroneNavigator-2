"""
GIS utilities for terrain data handling and integration.
"""

import os
import numpy as np

# Check for GIS libraries availability
try:
    import geopandas as gpd
    import rasterio
    import rasterio.plot
    from shapely.geometry import Point, LineString
    GIS_ENABLED = True
except ImportError:
    print("Warning: GIS libraries (geopandas, rasterio, shapely) not found. GIS features disabled.")
    GIS_ENABLED = False


class GISData:
    """
    Class for handling GIS data, including Digital Elevation Models (DEM)
    and vector data for terrain representation.
    """
    
    def __init__(self):
        self.dem_dataset = None
        self.dem_array = None
        self.dem_transform = None
        self.vector_data = None  # GeoDataFrame
        self.map_bounds = None  # Store as (minx, miny, maxx, maxy)
        
    def load_dem(self, filepath):
        """
        Load a Digital Elevation Model (DEM) from a file.
        
        Args:
            filepath (str): Path to the DEM file
            
        Returns:
            tuple: (success, message)
        """
        if not GIS_ENABLED:
            return False, "GIS libraries not installed."
        
        try:
            self.dem_dataset = rasterio.open(filepath)
            self.dem_array = self.dem_dataset.read(1)
            self.dem_transform = self.dem_dataset.transform
            self.map_bounds = self.dem_dataset.bounds
            print(f"DEM loaded: {filepath}, Bounds: {self.map_bounds}")
            # Normalize array for basic visualization if needed (optional)
            # self.dem_normalized = (self.dem_array - np.min(self.dem_array)) / (np.max(self.dem_array) - np.min(self.dem_array))
            return True, f"DEM Loaded: {os.path.basename(filepath)}"
        except Exception as e:
            self.dem_dataset = None
            return False, f"Error loading DEM: {e}"
    
    def load_vector(self, filepath):
        """
        Load vector data (like shapefiles) for representing features.
        
        Args:
            filepath (str): Path to the vector data file
            
        Returns:
            tuple: (success, message)
        """
        if not GIS_ENABLED:
            return False, "GIS libraries not installed."
        
        try:
            self.vector_data = gpd.read_file(filepath)
            # Ensure vector data is in the same CRS as DEM if possible, or reproject
            if self.dem_dataset and self.vector_data.crs != self.dem_dataset.crs:
                print(f"Reprojecting vector data from {self.vector_data.crs} to {self.dem_dataset.crs}")
                self.vector_data = self.vector_data.to_crs(self.dem_dataset.crs)
            print(f"Vector data loaded: {filepath}")
            return True, f"Vector Data Loaded: {os.path.basename(filepath)}"
        except Exception as e:
            self.vector_data = None
            return False, f"Error loading vector data: {e}"
    
    def get_elevation(self, x, y):
        """
        Get elevation at a specified point.
        
        Args:
            x (float): X coordinate
            y (float): Y coordinate
            
        Returns:
            float: Elevation value or 0.0 if not available
        """
        if self.dem_dataset:
            try:
                row, col = self.dem_dataset.index(x, y)
                # Basic bounds check
                if 0 <= row < self.dem_array.shape[0] and 0 <= col < self.dem_array.shape[1]:
                    return self.dem_array[row, col]
            except IndexError:  # Point outside raster bounds
                pass
        return 0.0  # Default elevation if no DEM or out of bounds
    
    def is_line_of_sight_clear(self, pos1, pos2, observer_height=2.0, target_height=1.0):
        """
        Check if there's a clear line of sight between two positions.
        
        Args:
            pos1 (tuple): First position (x, y)
            pos2 (tuple): Second position (x, y)
            observer_height (float): Height of observer above terrain
            target_height (float): Height of target above terrain
            
        Returns:
            bool: True if line of sight is clear, False otherwise
        """
        if not self.dem_dataset:
            return True  # No terrain to block
        
        # Very basic check: elevation at midpoint vs straight line
        # A real implementation needs to sample elevations along the line
        # and account for Earth's curvature and refraction for long distances.
        try:
            mid_x, mid_y = (pos1[0] + pos2[0]) / 2, (pos1[1] + pos2[1]) / 2
            elevation_midpoint_terrain = self.get_elevation(mid_x, mid_y)
            
            elevation_p1_terrain = self.get_elevation(pos1[0], pos1[1])
            elevation_p2_terrain = self.get_elevation(pos2[0], pos2[1])
            
            # Elevation of the line-of-sight at the midpoint
            elevation_los_at_mid = ((elevation_p1_terrain + observer_height) + 
                                   (elevation_p2_terrain + target_height)) / 2
            
            # If terrain at midpoint is higher than the LOS line, it's blocked
            return elevation_midpoint_terrain < elevation_los_at_mid
        except:
            return True  # Error during check, assume clear
    
    def get_slope(self, x, y):
        """
        Calculate terrain slope at a position (simple implementation).
        
        Args:
            x (float): X coordinate
            y (float): Y coordinate
            
        Returns:
            float: Slope value in degrees
        """
        if not self.dem_dataset:
            return 0.0
        
        try:
            # Simple 4-point slope calculation
            elev_center = self.get_elevation(x, y)
            elev_north = self.get_elevation(x, y + 1)
            elev_east = self.get_elevation(x + 1, y)
            elev_south = self.get_elevation(x, y - 1)
            elev_west = self.get_elevation(x - 1, y)
            
            # Max slope in any direction
            max_gradient = max(
                abs(elev_north - elev_center),
                abs(elev_east - elev_center),
                abs(elev_south - elev_center),
                abs(elev_west - elev_center)
            )
            
            # Approximate slope in degrees
            return np.degrees(np.arctan(max_gradient))
        except:
            return 0.0
