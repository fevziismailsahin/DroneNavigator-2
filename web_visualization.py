"""
Web-based visualization for the NATO Military Drone Swarm Simulation.

This module creates a Flask web server that provides an interactive
real-time visualization of the drone swarm simulation.
"""

import os
import json
import time
import threading
import base64
from io import BytesIO
from flask import Flask, render_template, jsonify, send_from_directory

import matplotlib
matplotlib.use('Agg')
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
    
    while sim_running and sim_step < max_steps and not simulation.is_complete():
        with sim_lock:
            simulation.step()
            sim_step += 1
            sim_stats = simulation.get_statistics()
            
            # Generate plot for current state every 5 steps
            if sim_step % 5 == 0 or sim_step == 1:
                current_plot_data = generate_plot_data()
        
        # Add delay to control simulation speed
        time.sleep(step_delay)
    
    # Final statistics when complete
    sim_running = False
    with sim_lock:
        sim_stats = simulation.get_statistics()
        current_plot_data = generate_plot_data()

def generate_plot_data():
    """Generate plot of current simulation state and return as base64 image"""
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Set plot limits and labels
    field_size = simulation.config["FIELD_SIZE"]
    ax.set_xlim(0, field_size)
    ax.set_ylim(0, field_size)
    ax.set_title(f"Drone Swarm Simulation - Step {sim_step}")
    ax.set_xlabel("X Position")
    ax.set_ylabel("Y Position")
    
    # Plot obstacles
    for obstacle in simulation.obstacles:
        circle = plt.Circle(
            obstacle.pos, 
            obstacle.radius, 
            color='brown', 
            alpha=0.7
        )
        ax.add_patch(circle)
    
    # Plot turrets
    for turret in simulation.turrets:
        circle = plt.Circle(
            turret.pos, 
            1.5, 
            color='red', 
            alpha=0.9
        )
        range_circle = plt.Circle(
            turret.pos, 
            turret.range, 
            color='red', 
            alpha=0.1,
            linestyle='--'
        )
        ax.add_patch(circle)
        ax.add_patch(range_circle)
    
    # Plot targets
    for target in simulation.targets:
        if target.alive:
            square = plt.Rectangle(
                (target.pos[0] - 2.0, target.pos[1] - 2.0), 
                4, 4, 
                color='green', 
                alpha=0.8
            )
            ax.add_patch(square)
    
    # Plot drones with color based on status
    for drone in simulation.drones:
        if drone.alive:
            from config import STATUS_COLORS, DEFAULT_COLOR
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
            
            # Draw trajectory
            if len(drone.trajectory) > 1:
                traj_x = [pos[0] for pos in drone.trajectory[-10:]]  # Last 10 positions
                traj_y = [pos[1] for pos in drone.trajectory[-10:]]
                ax.plot(traj_x, traj_y, color=color, alpha=0.5, linewidth=1)
        else:
            # X for destroyed drones
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
    
    # Add legend for drone status
    from config import STATUS_COLORS
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor=color, markersize=10, label=status)
        for status, color in STATUS_COLORS.items()
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    # Save the plot to a BytesIO object
    img_data = BytesIO()
    plt.savefig(img_data, format='png', dpi=100)
    img_data.seek(0)
    plt.close(fig)
    
    # Convert to base64 for embedding in HTML
    img_base64 = base64.b64encode(img_data.getvalue()).decode('utf-8')
    return img_base64

# Create HTML template
@app.route('/')
def index():
    """Main page route"""
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/api/start_simulation', methods=['POST'])
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

@app.route('/api/stop_simulation', methods=['POST'])
def stop_simulation():
    """Stop the current simulation"""
    global sim_running
    
    if not sim_running:
        return jsonify({'status': 'error', 'message': 'No simulation running'})
    
    sim_running = False
    return jsonify({'status': 'success', 'message': 'Simulation stopped'})

@app.route('/api/reset_simulation', methods=['POST'])
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

# Create index.html template
def create_template_files():
    """Create necessary template files"""
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NATO Military Drone Swarm Simulation</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {
            background-color: #0a1929;
            color: #e0e0e0;
            font-family: 'Roboto', sans-serif;
        }
        .simulation-container {
            position: relative;
            border-radius: 8px;
            background-color: #132f4c;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }
        .control-panel {
            background-color: #173a5e;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }
        .stats-panel {
            background-color: #173a5e;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }
        .btn-primary {
            background-color: #0059b2;
            border-color: #0059b2;
        }
        .btn-danger {
            background-color: #c70011;
            border-color: #c70011;
        }
        .btn-success {
            background-color: #087f5b;
            border-color: #087f5b;
        }
        h1, h2, h3 {
            color: #66b2ff;
        }
        .card {
            background-color: #1e4976;
            border: none;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            margin-bottom: 1rem;
        }
        .card-header {
            background-color: #173a5e;
            color: #66b2ff;
            font-weight: bold;
        }
        .progress {
            height: 20px;
            background-color: #0a1929;
        }
        .loading-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(10, 25, 41, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            border-radius: 8px;
        }
        .spinner-border {
            width: 3rem;
            height: 3rem;
        }
        .status-badge {
            font-size: 0.9rem;
            padding: 0.4rem 0.8rem;
        }
        .navbar {
            background-color: #173a5e;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        .navbar-brand {
            font-weight: bold;
            color: #66b2ff;
        }
        .sim-title {
            position: absolute;
            top: 10px;
            left: 10px;
            background-color: rgba(19, 47, 76, 0.8);
            padding: 5px 15px;
            border-radius: 4px;
            font-weight: bold;
            z-index: 900;
        }
        #simulation-view {
            min-height: 500px;
            border-radius: 8px;
            overflow: hidden;
        }
        .stat-value {
            font-weight: bold;
            font-size: 1.2rem;
            color: #fff;
        }
        .stat-label {
            color: #66b2ff;
            font-size: 0.9rem;
        }
        .metric-card {
            padding: 0.5rem;
            text-align: center;
            background-color: #132f4c;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark mb-4">
        <div class="container">
            <a class="navbar-brand" href="#">
                <i class="fas fa-drone-alt"></i> NATO MILITARY DRONE SWARM SIMULATION
            </a>
            <div class="ms-auto">
                <span id="simulation-status-badge" class="badge status-badge bg-secondary">
                    <i class="fas fa-circle-notch fa-spin me-1"></i> Initializing
                </span>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="row">
            <div class="col-md-8">
                <div class="simulation-container">
                    <div id="loading-overlay" class="loading-overlay">
                        <div class="spinner-border text-light" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                    <div class="sim-title">
                        <span id="step-counter">Step: 0</span>
                    </div>
                    <div id="simulation-view" class="text-center">
                        <img id="simulation-image" src="" class="img-fluid rounded" alt="Simulation Visualization">
                    </div>
                </div>
                
                <div class="control-panel">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h3 class="mb-0"><i class="fas fa-gamepad me-2"></i>Simulation Controls</h3>
                    </div>
                    <div class="row">
                        <div class="col-md-4 mb-2">
                            <button id="start-btn" class="btn btn-success w-100">
                                <i class="fas fa-play me-1"></i> Start Simulation
                            </button>
                        </div>
                        <div class="col-md-4 mb-2">
                            <button id="stop-btn" class="btn btn-warning w-100" disabled>
                                <i class="fas fa-pause me-1"></i> Pause
                            </button>
                        </div>
                        <div class="col-md-4 mb-2">
                            <button id="reset-btn" class="btn btn-danger w-100">
                                <i class="fas fa-redo me-1"></i> Reset
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="stats-panel">
                    <h3 class="mb-3"><i class="fas fa-chart-line me-2"></i>Simulation Statistics</h3>
                    
                    <div class="card mb-3">
                        <div class="card-header">
                            <i class="fas fa-drone me-2"></i>Drone Status
                        </div>
                        <div class="card-body">
                            <div class="row g-2">
                                <div class="col-6">
                                    <div class="metric-card">
                                        <div class="stat-value" id="drones-alive">0</div>
                                        <div class="stat-label">Drones Active</div>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="metric-card">
                                        <div class="stat-value" id="drones-total">0</div>
                                        <div class="stat-label">Total Drones</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-3">
                                <label class="form-label mb-1">Drone Survival Rate</label>
                                <div class="progress">
                                    <div id="drone-progress" class="progress-bar bg-info" role="progressbar" style="width: 0%">0%</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card mb-3">
                        <div class="card-header">
                            <i class="fas fa-crosshairs me-2"></i>Mission Status
                        </div>
                        <div class="card-body">
                            <div class="row g-2">
                                <div class="col-6">
                                    <div class="metric-card">
                                        <div class="stat-value" id="targets-destroyed">0</div>
                                        <div class="stat-label">Targets Destroyed</div>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="metric-card">
                                        <div class="stat-value" id="targets-total">0</div>
                                        <div class="stat-label">Total Targets</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-3">
                                <label class="form-label mb-1">Mission Completion</label>
                                <div class="progress">
                                    <div id="mission-progress" class="progress-bar bg-success" role="progressbar" style="width: 0%">0%</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-tachometer-alt me-2"></i>Performance Metrics
                        </div>
                        <div class="card-body">
                            <div class="row g-2">
                                <div class="col-6">
                                    <div class="metric-card">
                                        <div class="stat-value" id="exchange-ratio">0.0</div>
                                        <div class="stat-label">Exchange Ratio</div>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="metric-card">
                                        <div class="stat-value" id="time-steps">0</div>
                                        <div class="stat-label">Time Steps</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="mt-4 py-3 text-center text-muted">
        <div class="container">
            <small>NATO Military Drone Swarm Simulation &copy; 2025</small>
        </div>
    </footer>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        $(document).ready(function() {
            let updateInterval;
            const statusBadge = $('#simulation-status-badge');
            const loadingOverlay = $('#loading-overlay');
            
            // Initial update
            updateSimulationStatus();
            
            // Hide loading initially
            loadingOverlay.hide();
            
            // Start simulation
            $('#start-btn').click(function() {
                loadingOverlay.show();
                $.post('/api/start_simulation', function(data) {
                    if (data.status === 'success') {
                        $('#start-btn').prop('disabled', true);
                        $('#stop-btn').prop('disabled', false);
                        $('#reset-btn').prop('disabled', true);
                        
                        statusBadge.removeClass('bg-secondary bg-danger bg-success').addClass('bg-primary');
                        statusBadge.html('<i class="fas fa-running me-1"></i> Running');
                        
                        // Start regular updates
                        updateInterval = setInterval(updateSimulationStatus, 500);
                    }
                    loadingOverlay.hide();
                });
            });
            
            // Stop simulation
            $('#stop-btn').click(function() {
                loadingOverlay.show();
                $.post('/api/stop_simulation', function(data) {
                    if (data.status === 'success') {
                        $('#start-btn').prop('disabled', false);
                        $('#stop-btn').prop('disabled', true);
                        $('#reset-btn').prop('disabled', false);
                        
                        statusBadge.removeClass('bg-primary bg-secondary bg-success').addClass('bg-warning');
                        statusBadge.html('<i class="fas fa-pause me-1"></i> Paused');
                        
                        // Stop updates
                        clearInterval(updateInterval);
                        // But do one more update to get latest state
                        updateSimulationStatus();
                    }
                    loadingOverlay.hide();
                });
            });
            
            // Reset simulation
            $('#reset-btn').click(function() {
                loadingOverlay.show();
                $.post('/api/reset_simulation', function(data) {
                    if (data.status === 'success') {
                        $('#start-btn').prop('disabled', false);
                        $('#stop-btn').prop('disabled', true);
                        $('#reset-btn').prop('disabled', false);
                        
                        statusBadge.removeClass('bg-primary bg-warning bg-danger').addClass('bg-secondary');
                        statusBadge.html('<i class="fas fa-sync me-1"></i> Ready');
                        
                        // Stop updates
                        clearInterval(updateInterval);
                        // But do one more update to get latest state
                        updateSimulationStatus();
                    }
                    loadingOverlay.hide();
                });
            });
            
            // Function to update simulation status
            function updateSimulationStatus() {
                $.get('/api/simulation_status', function(data) {
                    // Update step counter
                    $('#step-counter').text('Step: ' + data.step);
                    
                    // Update statistics
                    if (data.stats) {
                        const stats = data.stats;
                        
                        // Drone stats
                        $('#drones-alive').text(stats.drones_alive || 0);
                        $('#drones-total').text(stats.total_drones || 0);
                        
                        const dronePercent = stats.total_drones ? 
                            Math.round((stats.drones_alive / stats.total_drones) * 100) : 0;
                        $('#drone-progress').css('width', dronePercent + '%').text(dronePercent + '%');
                        
                        // Target stats
                        const targetsDestroyed = stats.total_targets - (stats.targets_remaining || 0);
                        $('#targets-destroyed').text(targetsDestroyed);
                        $('#targets-total').text(stats.total_targets || 0);
                        
                        const missionPercent = stats.total_targets ? 
                            Math.round((targetsDestroyed / stats.total_targets) * 100) : 0;
                        $('#mission-progress').css('width', missionPercent + '%').text(missionPercent + '%');
                        
                        // Performance metrics
                        const dronesLost = stats.total_drones - stats.drones_alive;
                        const ratio = dronesLost > 0 ? (targetsDestroyed / dronesLost).toFixed(2) : "∞";
                        $('#exchange-ratio').text(ratio);
                        $('#time-steps').text(stats.step_count || data.step);
                    }
                    
                    // Update simulation visualization
                    if (data.plot_data) {
                        $('#simulation-image').attr('src', 'data:image/png;base64,' + data.plot_data);
                    }
                    
                    // Check if simulation is complete
                    if (data.complete) {
                        clearInterval(updateInterval);
                        $('#start-btn').prop('disabled', true);
                        $('#stop-btn').prop('disabled', true);
                        $('#reset-btn').prop('disabled', false);
                        
                        statusBadge.removeClass('bg-primary bg-warning bg-secondary').addClass('bg-success');
                        statusBadge.html('<i class="fas fa-check-circle me-1"></i> Complete');
                    }
                });
            }
        });
    </script>
</body>
</html>"""
    
    os.makedirs("templates", exist_ok=True)
    with open(os.path.join("templates", "index.html"), "w") as f:
        f.write(index_html)

def main(host='0.0.0.0', port=5000, debug=False):
    """Main entry point for running the web visualization"""
    # Create template files
    create_template_files()
    
    # Initialize simulation
    initialize_simulation()
    
    # Start the Flask app
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()