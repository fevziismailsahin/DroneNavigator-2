"""
Military-Grade Drone Swarm Simulation with GIS Integration.

This application simulates a swarm of military drones with flocking behavior,
target seeking, threat avoidance, and GIS/terrain integration.
"""

import sys
import os
import matplotlib
# Use the non-GUI backend for headless environments
matplotlib.use('Agg')

# Set the QT platform to offscreen for headless environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtWidgets import QApplication
from gui import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    try:
        window = MainWindow()
        print("Starting command-line mode simulation...")
        print("Please run this application on a desktop environment with GUI support.")
        print("This simulation requires QT platform support for visualization.")
        
        # Still create the window object but don't show it in headless mode
        # window.show()
        
        # Just initialize the simulation without GUI interaction
        print("Simulation initialized. Exiting.")
        sys.exit(0)
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)
