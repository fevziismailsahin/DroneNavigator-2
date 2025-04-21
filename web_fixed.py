"""
Web-based visualization for the NATO Military Drone Swarm Simulation.

This is a fixed version of the web visualization that properly creates
all necessary files and templates, and ensures compatibility with Replit.
"""

import os
import json
import time
import threading
import base64
from io import BytesIO
from flask import Flask, render_template, jsonify, send_from_directory, Response

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

from config import DEFAULT_CONFIG
from simulation_core import Simulation
from gis_utils import GISData

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'nato-military-simulation-key'

# Global simulation state
simulation = None
sim_thread = None
sim_running = False
sim_step = 0
sim_stats = {}
current_plot_data = None
sim_lock = threading.Lock()
output_dir = "static/output"

# Ensure output directories exist
os.makedirs(output_dir, exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

def initialize_simulation(config=None):
    """Initialize the simulation with provided config"""
    global simulation, sim_step
    if config is None:
        config = DEFAULT_CONFIG.copy()
    
    gis = GISData()
    simulation = Simulation(config)
    simulation.set_gis(gis)
    sim_step = 0
    return simulation

def simulation_thread_func(max_steps=200, step_delay=0.1):
    """Background thread to run the simulation"""
    global sim_running, sim_step, sim_stats, current_plot_data
    
    # Military-grade simulation runs faster with multi-step processing
    STEPS_PER_CYCLE = 2  # Process multiple simulation steps per visual update
    
    last_time = time.time()
    steps_this_second = 0
    fps_counter = 0
    
    while sim_running and sim_step < max_steps and not simulation.is_complete():
        current_time = time.time()
        elapsed = current_time - last_time
        
        # Track simulation performance metrics
        if elapsed >= 1.0:
            fps_counter = steps_this_second
            steps_this_second = 0
            last_time = current_time
        
        # Process multiple simulation steps for performance
        for _ in range(STEPS_PER_CYCLE):
            if sim_running and sim_step < max_steps and not simulation.is_complete():
                with sim_lock:
                    try:
                        simulation.step()
                        sim_step += 1
                        sim_stats = simulation.get_statistics()
                        
                        # Add performance metrics
                        if 'performance' not in sim_stats:
                            sim_stats['performance'] = {}
                        sim_stats['performance']['fps'] = fps_counter
                        
                        steps_this_second += 1
                    except Exception as e:
                        print(f"Error in simulation step: {e}")
                        sim_running = False
                        break
        
        # Generate plot for visualization - more frequently for real-time feel
        with sim_lock:
            if sim_step % 2 == 0 or sim_step == 1:
                try:
                    current_plot_data = generate_plot_data()
                except Exception as e:
                    print(f"Error generating plot: {e}")
        
        # Minimal delay for CPU management but maintain fast simulation
        time.sleep(step_delay)
    
    # Final statistics when complete
    sim_running = False
    with sim_lock:
        sim_stats = simulation.get_statistics()
        current_plot_data = generate_plot_data()

def generate_plot_data():
    """Generate plot of current simulation state and return as base64 image"""
    fig, ax = plt.subplots(figsize=(10, 8), facecolor='#0a1929')
    ax.set_facecolor('#132f4c')
    
    # Grid and border styling for military look
    ax.grid(color='#1e4976', linestyle='--', linewidth=0.5, alpha=0.5)
    
    # Set plot limits and labels with military styling
    field_size = simulation.config["FIELD_SIZE"]
    ax.set_xlim(0, field_size)
    ax.set_ylim(0, field_size)
    
    # Title and axis labels in military style
    ax.set_title(f"NATO MILITARY SWARM OPERATION - Step {sim_step}", 
                 color='#66b2ff', fontsize=14, fontweight='bold')
    
    # Coordinate axes in military style
    ax.set_xlabel("X Position (km)", color='#66b2ff')
    ax.set_ylabel("Y Position (km)", color='#66b2ff')
    ax.tick_params(colors='#66b2ff', which='both')
    
    # Military grid squares with coordinates
    for spine in ax.spines.values():
        spine.set_color('#173a5e')
        spine.set_linewidth(2)
    
    # Plot terrain features (obstacles)
    for obstacle in simulation.obstacles:
        circle = plt.Circle(
            obstacle.pos, 
            obstacle.radius, 
            color='#654321', 
            alpha=0.8
        )
        ax.add_patch(circle)
    
    # Plot defensive turrets
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
        scan_angle = (sim_step * 5) % 360
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
    
    # Plot drones
    from config import STATUS_COLORS, DEFAULT_COLOR
    
    for i, drone in enumerate(simulation.drones):
        if drone.alive:
            color = STATUS_COLORS.get(drone.status, DEFAULT_COLOR)
            
            circle = plt.Circle(
                drone.pos, 
                0.7, 
                color=color, 
                alpha=0.9
            )
            ax.add_patch(circle)
            
            # Draw velocity vector
            if np.linalg.norm(drone.velocity) > 0.1:
                velocity = drone.velocity / np.linalg.norm(drone.velocity) * 2
                ax.arrow(
                    drone.pos[0], 
                    drone.pos[1], 
                    velocity[0], 
                    velocity[1], 
                    head_width=0.4, 
                    head_length=0.7, 
                    fc=color, 
                    ec=color
                )
            
            ax.text(drone.pos[0], drone.pos[1], f"{i+1}", 
                    ha='center', va='center', color='white', 
                    fontweight='bold', fontsize=8)
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
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor=color, markersize=10, label=status)
        for status, color in STATUS_COLORS.items()
    ]
    
    # Add standard elements
    legend_elements.extend([
        plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='#00aa00', 
                  markersize=10, label='Target'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#ff2a2a', 
                  markersize=10, label='Turret'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#654321', 
                  markersize=10, label='Terrain')
    ])
    
    legend = ax.legend(handles=legend_elements, loc='upper right', 
                      title="NATO ELEMENTS", framealpha=0.7,
                      facecolor='#173a5e', edgecolor='#66b2ff')
    legend.get_title().set_color('#66b2ff')
    for text in legend.get_texts():
        text.set_color('#e0e0e0')
    
    # Add mission time
    mission_time = f"T+{sim_step:03d}"
    ax.text(0.02, 0.98, f"MISSION TIME: {mission_time}", 
           transform=ax.transAxes, color='#66b2ff', 
           fontsize=10, verticalalignment='top',
           bbox=dict(boxstyle="round,pad=0.3", fc='#173a5e', ec='#66b2ff', alpha=0.7))
    
    # Save the plot to a BytesIO object
    img_data = BytesIO()
    plt.savefig(img_data, format='png', dpi=100, facecolor='#0a1929', bbox_inches='tight')
    img_data.seek(0)
    plt.close(fig)
    
    # Convert to base64 for embedding in HTML
    img_base64 = base64.b64encode(img_data.getvalue()).decode('utf-8')
    return img_base64

@app.route('/')
def index():
    """Main page route"""
    create_template_files()  # Always ensure template exists
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/ping')
def ping():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

@app.route('/api/start_simulation', methods=['GET', 'POST'])
def start_simulation():
    """Start a new simulation"""
    global simulation, sim_thread, sim_running, sim_step
    
    if sim_running:
        return jsonify({'status': 'error', 'message': 'Simulation already running'})
    
    # Initialize with default config
    initialize_simulation()
    
    # Start simulation thread
    sim_running = True
    sim_step = 0
    sim_thread = threading.Thread(target=simulation_thread_func)
    sim_thread.daemon = True
    sim_thread.start()
    
    return jsonify({'status': 'success', 'message': 'Simulation started'})

@app.route('/api/stop_simulation', methods=['GET', 'POST'])
def stop_simulation():
    """Stop the current simulation"""
    global sim_running
    
    if not sim_running:
        return jsonify({'status': 'error', 'message': 'No simulation running'})
    
    sim_running = False
    return jsonify({'status': 'success', 'message': 'Simulation stopped'})

@app.route('/api/reset_simulation', methods=['GET', 'POST'])
def reset_simulation():
    """Reset the simulation"""
    global sim_running, simulation, sim_step
    
    # Stop if running
    sim_running = False
    if sim_thread and sim_thread.is_alive():
        sim_thread.join(timeout=1.0)
    
    # Reinitialize
    initialize_simulation()
    sim_step = 0
    
    return jsonify({'status': 'success', 'message': 'Simulation reset'})

@app.route('/api/simulation_status')
def simulation_status():
    """Get current simulation status"""
    global sim_running, sim_step, sim_stats, current_plot_data
    
    with sim_lock:
        status = {
            'running': sim_running,
            'step': sim_step,
            'stats': sim_stats,
            'complete': simulation.is_complete() if simulation else False,
            'plot_data': current_plot_data
        }
    
    return jsonify(status)

@app.route('/current_image.png')
def get_current_image():
    """Return current simulation state as PNG image"""
    global current_plot_data
    
    if not current_plot_data:
        # Return a placeholder image
        with open('static/placeholder.png', 'rb') as f:
            image_data = f.read()
    else:
        # Decode base64 data to binary
        image_data = base64.b64decode(current_plot_data)
    
    return Response(image_data, mimetype='image/png')

def create_template_files():
    """Create necessary template files"""
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NATO Military Drone Swarm Simulation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #0a1929;
            color: #e0e0e0;
            font-family: 'Arial', sans-serif;
        }
        .header {
            background-color: #132f4c;
            border-bottom: 2px solid #173a5e;
            padding: 1rem;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        .simulation-container {
            background-color: #132f4c;
            border-radius: 8px;
            border: 1px solid #173a5e;
            padding: 15px;
            margin-bottom: 20px;
        }
        .mission-info {
            border-left: 3px solid #66b2ff;
            padding-left: 15px;
            margin-top: 15px;
        }
        .control-panel {
            background-color: #0f2540;
            border-radius: 8px;
            padding: 15px;
            border: 1px solid #173a5e;
        }
        .btn-primary {
            background-color: #2a6bc2;
            border-color: #173a5e;
        }
        .btn-primary:hover {
            background-color: #1e4976;
            border-color: #173a5e;
        }
        .progress {
            background-color: #0f2540;
        }
        .military-title {
            color: #66b2ff;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .status-active {
            background-color: #00aa00;
        }
        .status-inactive {
            background-color: #ff2a2a;
        }
        .img-fluid {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            border: 1px solid #173a5e;
        }
        #visualization {
            text-align: center;
        }
        .status-label {
            font-size: 0.8rem;
            margin-top: 5px;
            color: #b0b0b0;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="header">
            <h1 class="military-title">NATO Military Drone Swarm Simulation</h1>
            <p>Real-Time Tactical Visualization Interface</p>
        </div>
        
        <div class="row">
            <div class="col-md-9">
                <div class="simulation-container">
                    <div id="visualization">
                        <img id="sim-image" src="/current_image.png" class="img-fluid" alt="Simulation Visualization">
                    </div>
                    <div class="text-center mt-2">
                        <div class="status-label">
                            <span id="status-indicator" class="status-indicator status-inactive"></span>
                            <span id="status-text">Simulation Inactive</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="control-panel">
                    <h4 class="military-title mb-3">Control Panel</h4>
                    
                    <div class="d-grid gap-2 mb-4">
                        <button id="startBtn" class="btn btn-primary">Start Simulation</button>
                        <button id="stopBtn" class="btn btn-warning" disabled>Stop Simulation</button>
                        <button id="resetBtn" class="btn btn-danger">Reset Simulation</button>
                    </div>
                    
                    <div class="mission-info">
                        <h5 class="military-title">Mission Status</h5>
                        <div class="mb-2">
                            <strong>Step:</strong> <span id="step-counter">0</span>
                        </div>
                        <div class="mb-2">
                            <strong>Drones Active:</strong> <span id="drones-active">0</span>
                        </div>
                        <div class="mb-2">
                            <strong>Targets Remaining:</strong> <span id="targets-remaining">0</span>
                        </div>
                        <div class="mb-2">
                            <strong>Simulation Rate:</strong> <span id="sim-fps">0</span> steps/s
                        </div>
                        <div class="mt-3">
                            <h6 class="military-title">Mission Progress</h6>
                            <div class="progress">
                                <div id="mission-progress" class="progress-bar bg-info" role="progressbar" style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // DOM elements
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const resetBtn = document.getElementById('resetBtn');
        const simImage = document.getElementById('sim-image');
        const stepCounter = document.getElementById('step-counter');
        const dronesActive = document.getElementById('drones-active');
        const targetsRemaining = document.getElementById('targets-remaining');
        const simFps = document.getElementById('sim-fps');
        const missionProgress = document.getElementById('mission-progress');
        const statusIndicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');

        // Status polling
        let statusInterval;
        let fetchingStatus = false;
        const updateInterval = 500; // Update every 500ms

        // Start the simulation
        startBtn.addEventListener('click', () => {
            fetch('/api/start_simulation')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        startStatusPolling();
                        updateControlState(true);
                    }
                })
                .catch(error => console.error('Error starting simulation:', error));
        });

        // Stop the simulation
        stopBtn.addEventListener('click', () => {
            fetch('/api/stop_simulation')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        updateControlState(false);
                    }
                })
                .catch(error => console.error('Error stopping simulation:', error));
        });

        // Reset the simulation
        resetBtn.addEventListener('click', () => {
            fetch('/api/reset_simulation')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        updateControlState(false);
                        updateStats({
                            step: 0,
                            stats: {},
                            running: false,
                            complete: false
                        });
                        // Force reload the image
                        reloadImage();
                    }
                })
                .catch(error => console.error('Error resetting simulation:', error));
        });

        // Update UI for current control state
        function updateControlState(running) {
            startBtn.disabled = running;
            stopBtn.disabled = !running;
            
            if (running) {
                statusIndicator.classList.remove('status-inactive');
                statusIndicator.classList.add('status-active');
                statusText.textContent = 'Simulation Active';
            } else {
                statusIndicator.classList.remove('status-active');
                statusIndicator.classList.add('status-inactive');
                statusText.textContent = 'Simulation Inactive';
                
                // Stop polling if not running
                if (statusInterval) {
                    clearInterval(statusInterval);
                    statusInterval = null;
                }
            }
        }

        // Update stats display
        function updateStats(data) {
            stepCounter.textContent = data.step;
            
            // Only update if stats are available
            if (data.stats) {
                // Handle empty or missing stats gracefully
                if (!data.stats.total_drones) data.stats.total_drones = 10;
                if (!data.stats.drones_alive) data.stats.drones_alive = 0;
                if (!data.stats.total_targets) data.stats.total_targets = 5;
                if (!data.stats.targets_remaining) data.stats.targets_remaining = 5;
                
                dronesActive.textContent = `${data.stats.drones_alive}/${data.stats.total_drones}`;
                targetsRemaining.textContent = `${data.stats.targets_remaining}/${data.stats.total_targets}`;
                
                // Calculate mission progress
                const targetsDestroyed = data.stats.total_targets - data.stats.targets_remaining;
                const progressPercent = (targetsDestroyed / data.stats.total_targets) * 100;
                missionProgress.style.width = `${progressPercent}%`;
                missionProgress.setAttribute('aria-valuenow', progressPercent);
                
                // Update FPS if available
                if (data.stats.performance && data.stats.performance.fps) {
                    simFps.textContent = data.stats.performance.fps;
                }
            }
            
            // If simulation is complete, stop polling
            if (data.complete) {
                updateControlState(false);
                statusText.textContent = 'Mission Complete';
            }
        }

        // Reload the visualization image
        function reloadImage() {
            // Add timestamp to prevent caching
            simImage.src = `/current_image.png?t=${Date.now()}`;
        }

        // Poll for simulation status
        function startStatusPolling() {
            if (statusInterval) {
                clearInterval(statusInterval);
            }
            
            // Poll immediately
            pollStatus();
            
            // Then set up regular polling
            statusInterval = setInterval(pollStatus, updateInterval);
        }

        // Get current simulation status
        function pollStatus() {
            if (fetchingStatus) return;
            
            fetchingStatus = true;
            fetch('/api/simulation_status')
                .then(response => response.json())
                .then(data => {
                    updateStats(data);
                    
                    // Update image if plot data is available
                    if (data.plot_data) {
                        reloadImage();
                    }
                    
                    // Update control state
                    if (!data.running && statusInterval) {
                        updateControlState(false);
                    }
                })
                .catch(error => console.error('Error polling status:', error))
                .finally(() => {
                    fetchingStatus = false;
                });
        }

        // Initialize with a status check
        fetch('/api/simulation_status')
            .then(response => response.json())
            .then(data => {
                updateControlState(data.running);
                updateStats(data);
                
                if (data.running) {
                    startStatusPolling();
                }
            })
            .catch(error => console.error('Error checking status:', error));
    </script>
</body>
</html>
"""

    # Create the template file
    with open('templates/index.html', 'w') as f:
        f.write(index_html)
    
    # Create placeholder image
    placeholder_path = 'static/placeholder.png'
    if not os.path.exists(placeholder_path):
        fig, ax = plt.subplots(figsize=(10, 8), facecolor='#0a1929')
        ax.set_facecolor('#132f4c')
        ax.text(0.5, 0.5, "NATO MILITARY DRONE SWARM SIMULATION\nPress Start to Begin", 
               ha='center', va='center', fontsize=14, color='#66b2ff',
               transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        plt.savefig(placeholder_path, dpi=100, facecolor='#0a1929', bbox_inches='tight')
        plt.close(fig)

def main(host='0.0.0.0', port=5000, debug=False):
    """Main entry point for running the web visualization"""
    # Create template files
    create_template_files()
    
    # Initialize simulation
    initialize_simulation()
    
    print("\nNATO MILITARY DRONE SWARM WEB VISUALIZATION")
    print("===========================================")
    print(f"Starting web server on {host}:{port}")
    print("Open your browser to view the simulation")
    print("Press Ctrl+C to stop the server\n")
    
    # Start the Flask app
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()