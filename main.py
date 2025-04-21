"""
Military-Grade Drone Swarm Simulation with GIS Integration.

This application simulates a swarm of military drones with flocking behavior,
target seeking, threat avoidance, and GIS/terrain integration.
"""

import sys
import os
import platform

# Check if running in a headless environment
def is_headless():
    """Check if running in a headless environment like Replit."""
    # Check for common cloud/container environments
    if os.environ.get('REPLIT_DB_URL') or os.environ.get('REPL_ID'):
        return True
    
    # Check if running in a Docker container
    if os.path.exists('/.dockerenv'):
        return True
    
    # Check for display availability
    if not os.environ.get('DISPLAY') and platform.system() != 'Windows':
        return True
    
    # If QT_QPA_PLATFORM is set to offscreen, it's likely headless
    if os.environ.get('QT_QPA_PLATFORM') == 'offscreen':
        return True
    
    return False

# Main execution entry point
if __name__ == "__main__":
    if is_headless():
        print("Running in headless environment, launching command-line version...")
        try:
            from headless_simulation import run_demo
            run_demo(num_steps=200)
        except Exception as e:
            print(f"Error running headless simulation: {e}")
            sys.exit(1)
    else:
        # GUI version for desktop environments
        try:
            import matplotlib
            from PyQt5.QtWidgets import QApplication
            from gui import MainWindow
            
            app = QApplication(sys.argv)
            window = MainWindow()
            window.show()
            sys.exit(app.exec_())
        except Exception as e:
            print(f"Critical error: {e}")
            sys.exit(1)
