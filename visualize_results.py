"""
NATO Military Drone Swarm Visualization Viewer

This simple script displays the generated tactical visualizations
from the drone swarm simulation.
"""

import os
import sys
import glob
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider
from PIL import Image

class TacticalViewer:
    def __init__(self):
        self.output_dir = 'output'
        self.current_index = 0
        self.files = self.get_image_files()
        
        if not self.files:
            print("No tactical visualization images found in the output directory.")
            print("Please run the simulation first using 'python direct_simulation.py'")
            sys.exit(1)
        
        self.setup_viewer()
    
    def get_image_files(self):
        # Get all tactical view images, sorted by step number
        tactical_files = sorted(
            glob.glob(os.path.join(self.output_dir, 'tactical_view_*.png')),
            key=lambda x: int(x.split('_')[-1].split('.')[0])
        )
        
        if not tactical_files and os.path.exists(os.path.join(self.output_dir)):
            # If no tactical views but there are step files, use those instead
            tactical_files = sorted(
                glob.glob(os.path.join(self.output_dir, 'step_*.png')),
                key=lambda x: int(x.split('_')[-1].split('.')[0])
            )
        
        return tactical_files
    
    def setup_viewer(self):
        # Set up the figure and axis for display
        self.fig, self.ax = plt.subplots(figsize=(12, 10))
        plt.subplots_adjust(bottom=0.15)
        
        # Add title with military styling
        self.fig.canvas.manager.set_window_title('NATO Military Drone Swarm Tactical Viewer')
        
        # Display the first image
        self.display_current_image()
        
        # Add navigation buttons
        ax_prev = plt.axes([0.2, 0.05, 0.1, 0.075])
        ax_next = plt.axes([0.7, 0.05, 0.1, 0.075])
        self.btn_prev = Button(ax_prev, 'Previous', color='0.85', hovercolor='0.95')
        self.btn_next = Button(ax_next, 'Next', color='0.85', hovercolor='0.95')
        self.btn_prev.on_clicked(self.prev_image)
        self.btn_next.on_clicked(self.next_image)
        
        # Add a slider for direct navigation
        ax_slider = plt.axes([0.35, 0.05, 0.3, 0.03])
        self.slider = Slider(ax_slider, 'Frame', 0, len(self.files)-1, 
                            valinit=0, valstep=1)
        self.slider.on_changed(self.slider_update)
        
        # Show the viewer
        plt.show()
    
    def display_current_image(self):
        # Clear previous image
        self.ax.clear()
        
        # Load and display current image
        img = Image.open(self.files[self.current_index])
        self.ax.imshow(img)
        
        # Remove axis ticks for cleaner display
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        # Set title showing current frame
        frame_num = os.path.basename(self.files[self.current_index]).split('_')[-1].split('.')[0]
        self.ax.set_title(f"NATO Tactical View - Frame {frame_num} of {len(self.files)}", 
                         fontsize=14, color='blue')
        
        # Update the figure
        self.fig.canvas.draw_idle()
    
    def prev_image(self, event):
        # Show previous image
        if self.current_index > 0:
            self.current_index -= 1
            self.display_current_image()
            self.slider.set_val(self.current_index)
    
    def next_image(self, event):
        # Show next image
        if self.current_index < len(self.files) - 1:
            self.current_index += 1
            self.display_current_image()
            self.slider.set_val(self.current_index)
    
    def slider_update(self, val):
        # Update image based on slider position
        self.current_index = int(val)
        self.display_current_image()

if __name__ == "__main__":
    print("\nNATO MILITARY DRONE SWARM TACTICAL VIEWER")
    print("==========================================")
    print("Use the slider and buttons to navigate through the tactical visualizations.")
    print("Close the window to exit the viewer.\n")
    
    viewer = TacticalViewer()