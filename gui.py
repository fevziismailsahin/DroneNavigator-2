"""
GUI components for the drone swarm simulation.
"""

import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QFrame,
    QFileDialog, QMessageBox, QStatusBar, QSizePolicy, QGroupBox,
    QFormLayout, QCheckBox, QComboBox, QTabWidget, QProgressBar,
    QSlider
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIntValidator, QDoubleValidator

from config import DEFAULT_CONFIG
from mpl_canvas import SimulationCanvas, SimulationToolbar
from simulation_core import Simulation
from gis_utils import GISData

class SimulationControl(QWidget):
    """Controls for managing the simulation."""
    
    def __init__(self, parent, simulation, config):
        """
        Initialize simulation control panel.
        
        Args:
            parent: Parent widget
            simulation: Simulation object to control
            config: Configuration dictionary
        """
        super().__init__(parent)
        self.simulation = simulation
        self.config = config
        self.initialize_ui()
    
    def initialize_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Simulation control buttons
        control_group = QGroupBox("Simulation Control")
        control_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_simulation)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_simulation)
        self.pause_button.setEnabled(False)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_simulation)
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.reset_button)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Simulation speed control
        speed_group = QGroupBox("Simulation Speed")
        speed_layout = QVBoxLayout()
        
        speed_slider_layout = QHBoxLayout()
        speed_slider_layout.addWidget(QLabel("Slow"))
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(10)
        self.speed_slider.setValue(1)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(1)
        self.speed_slider.valueChanged.connect(self.update_speed)
        
        speed_slider_layout.addWidget(self.speed_slider)
        speed_slider_layout.addWidget(QLabel("Fast"))
        
        speed_layout.addLayout(speed_slider_layout)
        
        self.interval_label = QLabel(f"Update interval: {self.config['SIMULATION_INTERVAL_MS']} ms")
        speed_layout.addWidget(self.interval_label)
        
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)
        
        # Progress indicator
        progress_group = QGroupBox("Simulation Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(self.config["MAX_SIMULATION_STEPS"])
        self.progress_bar.setValue(0)
        
        progress_layout.addWidget(self.progress_bar)
        
        self.stats_label = QLabel("Simulation not started")
        progress_layout.addWidget(self.stats_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Visualization options
        vis_group = QGroupBox("Visualization Options")
        vis_layout = QVBoxLayout()
        
        self.show_trajectories = QCheckBox("Show drone trajectories")
        self.show_trajectories.setChecked(True)
        
        vis_layout.addWidget(self.show_trajectories)
        
        vis_group.setLayout(vis_layout)
        layout.addWidget(vis_group)
        
        self.setLayout(layout)
    
    def start_simulation(self):
        """Start or resume the simulation."""
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.parent().start_simulation_timer()
    
    def pause_simulation(self):
        """Pause the simulation."""
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.parent().pause_simulation_timer()
    
    def reset_simulation(self):
        """Reset the simulation."""
        self.parent().reset_simulation()
        self.progress_bar.setValue(0)
        self.stats_label.setText("Simulation reset")
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
    
    def update_speed(self):
        """Update simulation speed based on slider."""
        # Smaller interval = faster simulation
        speed_factor = self.speed_slider.value()
        new_interval = int(DEFAULT_CONFIG["SIMULATION_INTERVAL_MS"] / speed_factor)
        self.config["SIMULATION_INTERVAL_MS"] = new_interval
        self.interval_label.setText(f"Update interval: {new_interval} ms")
        self.parent().update_simulation_timer()
    
    def update_progress(self, step_count, stats):
        """
        Update progress indicators.
        
        Args:
            step_count (int): Current step count
            stats (dict): Simulation statistics
        """
        self.progress_bar.setValue(step_count)
        
        # Format statistics string
        stats_text = (
            f"Step: {stats['step_count']} | "
            f"Drones: {stats['drones_alive']}/{len(self.simulation.drones)} | "
            f"Active: {stats['drones_active']} | "
            f"Targets: {stats['targets_remaining']}/{len(self.simulation.targets)}"
        )
        
        self.stats_label.setText(stats_text)
        
        # If simulation is complete, update UI accordingly
        if self.simulation.is_complete():
            self.pause_simulation()
            
            # Calculate success ratio
            targets_destroyed = stats['targets_destroyed']
            total_targets = len(self.simulation.targets)
            drones_alive = stats['drones_alive']
            total_drones = len(self.simulation.drones)
            
            completion_status = (
                f"Mission Complete!\n"
                f"Targets destroyed: {targets_destroyed}/{total_targets} "
                f"({targets_destroyed/total_targets*100:.1f}%)\n"
                f"Drones remaining: {drones_alive}/{total_drones} "
                f"({drones_alive/total_drones*100:.1f}%)"
            )
            
            self.stats_label.setText(completion_status)


class ConfigPanel(QWidget):
    """Panel for configuring simulation parameters."""
    
    def __init__(self, parent, config):
        """
        Initialize the configuration panel.
        
        Args:
            parent: Parent widget
            config (dict): Configuration dictionary
        """
        super().__init__(parent)
        self.config = config
        self.config_widgets = {}
        self.initialize_ui()
    
    def initialize_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout()
        
        # Create tabs for better organization
        tabs = QTabWidget()
        
        # Basic settings tab
        basic_tab = QWidget()
        basic_layout = QFormLayout()
        
        # Field size
        field_size_spin = QDoubleSpinBox()
        field_size_spin.setRange(10, 1000)
        field_size_spin.setValue(self.config["FIELD_SIZE"])
        field_size_spin.setSingleStep(10)
        field_size_spin.valueChanged.connect(lambda v: self.update_config("FIELD_SIZE", v))
        basic_layout.addRow("Field Size:", field_size_spin)
        self.config_widgets["FIELD_SIZE"] = field_size_spin
        
        # Entity counts
        for param in ["NUM_DRONES", "NUM_TARGETS", "NUM_TURRETS", "NUM_OBSTACLES"]:
            spin = QSpinBox()
            spin.setRange(0, 100)
            spin.setValue(self.config[param])
            spin.valueChanged.connect(lambda v, p=param: self.update_config(p, v))
            basic_layout.addRow(f"{param.replace('_', ' ').title()}:", spin)
            self.config_widgets[param] = spin
        
        # Max simulation steps
        max_steps_spin = QSpinBox()
        max_steps_spin.setRange(100, 10000)
        max_steps_spin.setValue(self.config["MAX_SIMULATION_STEPS"])
        max_steps_spin.setSingleStep(100)
        max_steps_spin.valueChanged.connect(lambda v: self.update_config("MAX_SIMULATION_STEPS", v))
        basic_layout.addRow("Max Simulation Steps:", max_steps_spin)
        self.config_widgets["MAX_SIMULATION_STEPS"] = max_steps_spin
        
        basic_tab.setLayout(basic_layout)
        
        # Drone settings tab
        drone_tab = QWidget()
        drone_layout = QFormLayout()
        
        drone_params = [
            "DRONE_MAX_SPEED", "DRONE_MAX_FUEL", "DRONE_FUEL_CONSUMPTION_RATE", 
            "DRONE_SENSOR_RANGE", "DRONE_ATTACK_RANGE", "DRONE_RADIUS",
            "LOW_FUEL_THRESHOLD"
        ]
        
        for param in drone_params:
            spin = QDoubleSpinBox()
            spin.setDecimals(2)
            
            # Set appropriate ranges based on parameter
            if param == "DRONE_MAX_SPEED":
                spin.setRange(0.1, 20.0)
                spin.setSingleStep(0.1)
            elif param == "DRONE_MAX_FUEL":
                spin.setRange(1, 2000)
                spin.setSingleStep(100)
            elif param == "DRONE_SENSOR_RANGE":
                spin.setRange(1, 100)
                spin.setSingleStep(1)
            elif param == "LOW_FUEL_THRESHOLD":
                spin.setRange(0.01, 0.99)
                spin.setSingleStep(0.05)
            else:
                spin.setRange(0.1, 100)
                spin.setSingleStep(0.1)
                
            spin.setValue(self.config[param])
            spin.valueChanged.connect(lambda v, p=param: self.update_config(p, v))
            drone_layout.addRow(f"{param.replace('_', ' ').title()}:", spin)
            self.config_widgets[param] = spin
        
        drone_tab.setLayout(drone_layout)
        
        # Flocking behavior tab
        flocking_tab = QWidget()
        flocking_layout = QFormLayout()
        
        flocking_params = [
            "WEIGHT_COHESION", "WEIGHT_SEPARATION", "WEIGHT_ALIGNMENT", 
            "WEIGHT_TARGET_SEEKING", "WEIGHT_OBSTACLE_AVOIDANCE", "WEIGHT_TURRET_AVOIDANCE"
        ]
        
        for param in flocking_params:
            spin = QDoubleSpinBox()
            spin.setDecimals(2)
            spin.setRange(0, 10)
            spin.setSingleStep(0.05)
            spin.setValue(self.config[param])
            spin.valueChanged.connect(lambda v, p=param: self.update_config(p, v))
            flocking_layout.addRow(f"{param.replace('_', ' ').title()}:", spin)
            self.config_widgets[param] = spin
        
        flocking_tab.setLayout(flocking_layout)
        
        # Add tabs to tab widget
        tabs.addTab(basic_tab, "Basic")
        tabs.addTab(drone_tab, "Drones")
        tabs.addTab(flocking_tab, "Flocking")
        
        # Add tab widget to main layout
        main_layout.addWidget(tabs)
        
        # Apply and reset buttons
        button_layout = QHBoxLayout()
        
        apply_button = QPushButton("Apply Changes")
        apply_button.clicked.connect(self.apply_changes)
        
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)
        
        button_layout.addWidget(apply_button)
        button_layout.addWidget(reset_button)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def update_config(self, key, value):
        """
        Update a configuration parameter.
        
        Args:
            key (str): Configuration key
            value: New value
        """
        self.config[key] = value
    
    def apply_changes(self):
        """Apply configuration changes and reset simulation."""
        # No need to explicitly apply since values are updated continuously
        self.parent().parent().reset_simulation()
        QMessageBox.information(self, "Configuration Applied", 
                              "Configuration applied. Simulation has been reset.")
    
    def reset_to_defaults(self):
        """Reset all configuration values to defaults."""
        for key, value in DEFAULT_CONFIG.items():
            if key in self.config_widgets:
                self.config_widgets[key].setValue(value)
                self.config[key] = value
        
        QMessageBox.information(self, "Defaults Restored", 
                              "Default configuration values have been restored.")


class GISPanel(QWidget):
    """Panel for handling GIS data."""
    
    def __init__(self, parent, gis_data):
        """
        Initialize the GIS panel.
        
        Args:
            parent: Parent widget
            gis_data: GIS data handler
        """
        super().__init__(parent)
        self.gis_data = gis_data
        self.initialize_ui()
    
    def initialize_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # DEM Import
        dem_group = QGroupBox("Digital Elevation Model (DEM)")
        dem_layout = QVBoxLayout()
        
        dem_status_layout = QHBoxLayout()
        dem_status_layout.addWidget(QLabel("Status:"))
        self.dem_status = QLabel("Not loaded")
        dem_status_layout.addWidget(self.dem_status)
        dem_layout.addLayout(dem_status_layout)
        
        dem_button_layout = QHBoxLayout()
        self.load_dem_button = QPushButton("Load DEM")
        self.load_dem_button.clicked.connect(self.load_dem)
        dem_button_layout.addWidget(self.load_dem_button)
        dem_layout.addLayout(dem_button_layout)
        
        dem_group.setLayout(dem_layout)
        layout.addWidget(dem_group)
        
        # Vector Data Import
        vector_group = QGroupBox("Vector Data")
        vector_layout = QVBoxLayout()
        
        vector_status_layout = QHBoxLayout()
        vector_status_layout.addWidget(QLabel("Status:"))
        self.vector_status = QLabel("Not loaded")
        vector_status_layout.addWidget(self.vector_status)
        vector_layout.addLayout(vector_status_layout)
        
        vector_button_layout = QHBoxLayout()
        self.load_vector_button = QPushButton("Load Vector Data")
        self.load_vector_button.clicked.connect(self.load_vector)
        vector_button_layout.addWidget(self.load_vector_button)
        vector_layout.addLayout(vector_button_layout)
        
        vector_group.setLayout(vector_layout)
        layout.addWidget(vector_group)
        
        # Terrain Options
        terrain_group = QGroupBox("Terrain Options")
        terrain_layout = QVBoxLayout()
        
        self.enable_terrain_checkbox = QCheckBox("Enable Terrain Effects")
        self.enable_terrain_checkbox.setChecked(True)
        terrain_layout.addWidget(self.enable_terrain_checkbox)
        
        self.visualize_terrain_checkbox = QCheckBox("Visualize Terrain")
        self.visualize_terrain_checkbox.setChecked(True)
        terrain_layout.addWidget(self.visualize_terrain_checkbox)
        
        terrain_group.setLayout(terrain_layout)
        layout.addWidget(terrain_group)
        
        # Information/Help
        info_group = QGroupBox("GIS Information")
        info_layout = QVBoxLayout()
        
        info_text = (
            "GIS Integration allows loading terrain data to affect:\n"
            "• Drone movement speed (slower uphill)\n"
            "• Line of sight for turrets\n"
            "• Realistic terrain visualization\n\n"
            "Supported formats: GeoTIFF for DEM, Shapefiles for vectors"
        )
        
        info_label = QLabel(info_text)
        info_layout.addWidget(info_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        self.setLayout(layout)
    
    def load_dem(self):
        """Load a Digital Elevation Model (DEM) file."""
        try:
            file_dialog = QFileDialog()
            filepath, _ = file_dialog.getOpenFileName(
                self, "Open DEM File", "", "GeoTIFF Files (*.tif *.tiff);;All Files (*)"
            )
            
            if filepath:
                success, message = self.gis_data.load_dem(filepath)
                if success:
                    self.dem_status.setText("Loaded: " + os.path.basename(filepath))
                    self.dem_status.setStyleSheet("color: green;")
                    
                    # Update the simulation with GIS data
                    self.parent().parent().simulation.set_gis(self.gis_data)
                    # Trigger visualization update
                    self.parent().parent().update_visualization()
                else:
                    self.dem_status.setText("Error: " + message)
                    self.dem_status.setStyleSheet("color: red;")
        except Exception as e:
            error_message = str(e)
            self.dem_status.setText("Error: " + error_message)
            self.dem_status.setStyleSheet("color: red;")
            QMessageBox.critical(self, "Error", f"Failed to load DEM: {error_message}")
    
    def load_vector(self):
        """Load vector data file."""
        try:
            file_dialog = QFileDialog()
            filepath, _ = file_dialog.getOpenFileName(
                self, "Open Vector File", "", "Shapefile (*.shp);;GeoJSON (*.geojson);;All Files (*)"
            )
            
            if filepath:
                success, message = self.gis_data.load_vector(filepath)
                if success:
                    self.vector_status.setText("Loaded: " + os.path.basename(filepath))
                    self.vector_status.setStyleSheet("color: green;")
                    
                    # Update the visualization
                    self.parent().parent().update_visualization()
                else:
                    self.vector_status.setText("Error: " + message)
                    self.vector_status.setStyleSheet("color: red;")
        except Exception as e:
            error_message = str(e)
            self.vector_status.setText("Error: " + error_message)
            self.vector_status.setStyleSheet("color: red;")
            QMessageBox.critical(self, "Error", f"Failed to load vector data: {error_message}")


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Create a deep copy of config to avoid modifying the defaults
        self.config = DEFAULT_CONFIG.copy()
        self.simulation = Simulation(self.config)
        self.gis_data = GISData()
        self.simulation.set_gis(self.gis_data)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        
        self.initialize_ui()
        self.setWindowTitle("Military-Grade Drone Swarm Simulation")
        self.setGeometry(100, 100, 1200, 800)
    
    def initialize_ui(self):
        """Set up the user interface."""
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # Left panel for controls
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Create tabbed control panels
        control_tabs = QTabWidget()
        
        # Simulation control panel
        self.simulation_control = SimulationControl(self, self.simulation, self.config)
        control_tabs.addTab(self.simulation_control, "Simulation Control")
        
        # Configuration panel
        self.config_panel = ConfigPanel(control_tabs, self.config)
        control_tabs.addTab(self.config_panel, "Configuration")
        
        # GIS panel
        self.gis_panel = GISPanel(control_tabs, self.gis_data)
        control_tabs.addTab(self.gis_panel, "GIS")
        
        left_layout.addWidget(control_tabs)
        left_panel.setLayout(left_layout)
        
        # Set a maximum width for the left panel
        left_panel.setMaximumWidth(400)
        
        # Right panel for visualization
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Matplotlib canvas for visualization
        self.canvas = SimulationCanvas(right_panel, width=5, height=4, dpi=100)
        self.update_visualization()
        
        # Add matplotlib toolbar
        self.toolbar = SimulationToolbar(self.canvas, right_panel)
        
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)
        right_panel.setLayout(right_layout)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
    
    def start_simulation_timer(self):
        """Start the simulation timer."""
        if not self.timer.isActive():
            self.timer.start(self.config["SIMULATION_INTERVAL_MS"])
            self.statusBar.showMessage("Simulation running")
    
    def pause_simulation_timer(self):
        """Pause the simulation timer."""
        if self.timer.isActive():
            self.timer.stop()
            self.statusBar.showMessage("Simulation paused")
    
    def update_simulation_timer(self):
        """Update the simulation timer interval."""
        if self.timer.isActive():
            self.timer.stop()
            self.timer.start(self.config["SIMULATION_INTERVAL_MS"])
    
    def update_simulation(self):
        """Update the simulation state and visualization."""
        if not self.simulation.is_complete():
            self.simulation.step()
            self.update_visualization()
            
            # Update progress indicators
            stats = self.simulation.get_statistics()
            self.simulation_control.update_progress(self.simulation.step_count, stats)
        else:
            self.pause_simulation_timer()
    
    def update_visualization(self):
        """Update the visualization canvas."""
        show_trajectories = self.simulation_control.show_trajectories.isChecked()
        self.canvas.update_plot(self.simulation, self.config["FIELD_SIZE"], show_trajectories)
    
    def reset_simulation(self):
        """Reset the simulation to initial state."""
        self.pause_simulation_timer()
        self.simulation.initialize()
        self.update_visualization()
        self.statusBar.showMessage("Simulation reset")
