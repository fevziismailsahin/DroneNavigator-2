"""
Enhanced Web-based visualization for the NATO Military Drone Swarm Simulation.

This improved version incorporates real-world map data, terrain analysis,
and advanced tactical visualizations into the web interface.
"""

import os
import json
import time
import threading
import base64
from io import BytesIO
from flask import Flask, render_template, jsonify, send_from_directory, Response, request

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

from config import DEFAULT_CONFIG
from enhanced_simulation import EnhancedSimulation, generate_tactical_visualization
from geo_data_manager import GeoDataManager

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

def initialize_simulation(config=None, time_of_day="day", 
                         weather="clear", mission_type="strike", 
                         with_enemy_drones=True, num_enemies=3):
    """Initialize the enhanced simulation with provided config"""
    global simulation, sim_step
    if config is None:
        config = DEFAULT_CONFIG.copy()
    
    # Create the enhanced simulation
    simulation = EnhancedSimulation(config)
    simulation.time_of_day = time_of_day
    simulation.weather_condition = weather
    simulation.mission_type = mission_type
    
    # Create friendly drones
    simulation.create_drones(enhanced=True)
    
    # Add enemy drones if requested
    if with_enemy_drones:
        num_enemies = min(num_enemies, config["NUM_DRONES"] // 2)  # Cap enemies at half of friendly drones
        simulation.create_enemy_drones(num_enemies, enhanced=True)
    
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
                    current_plot_data = generate_plot_data(sim_step)
                except Exception as e:
                    print(f"Error generating plot: {e}")
        
        # Minimal delay for CPU management but maintain fast simulation
        time.sleep(step_delay)
    
    # Final statistics when complete
    sim_running = False
    with sim_lock:
        sim_stats = simulation.get_statistics()
        current_plot_data = generate_plot_data(sim_step, is_final=True)

def generate_plot_data(step, is_final=False):
    """Generate tactical visualization and return as base64 image"""
    # Create the tactical visualization
    fig = generate_tactical_visualization(simulation, step, is_final)
    
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
    
    # Get configuration parameters
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Extract simulation parameters with defaults
            time_of_day = data.get('time_of_day', 'day')
            weather = data.get('weather', 'clear')
            mission_type = data.get('mission_type', 'strike')
            num_drones = int(data.get('num_drones', 10))
            with_enemy_drones = data.get('with_enemy_drones', True)
            num_enemies = int(data.get('num_enemies', 3))
            
            # Update configuration
            config = DEFAULT_CONFIG.copy()
            config['NUM_DRONES'] = num_drones
            
            # Initialize with parameters
            initialize_simulation(
                config=config,
                time_of_day=time_of_day,
                weather=weather,
                mission_type=mission_type,
                with_enemy_drones=with_enemy_drones,
                num_enemies=num_enemies
            )
        except Exception as e:
            print(f"Error parsing simulation parameters: {e}")
            # Initialize with defaults
            initialize_simulation()
    else:
        # Initialize with defaults for GET requests
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
    
    # Reinitialize with default parameters
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

@app.route('/api/simulation_config', methods=['GET'])
def get_simulation_config():
    """Get available simulation configuration options"""
    config_options = {
        'time_of_day': ['day', 'dusk', 'night'],
        'weather': ['clear', 'cloudy', 'rain', 'fog'],
        'mission_type': ['strike', 'recon', 'defend', 'escort']
    }
    
    return jsonify(config_options)

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
            margin-bottom: 20px;
        }
        .config-panel {
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
        .form-label {
            color: #66b2ff;
        }
        .form-select, .form-control {
            background-color: #0f2540;
            border-color: #173a5e;
            color: #e0e0e0;
        }
        .form-select:focus, .form-control:focus {
            background-color: #173a5e;
            border-color: #2a6bc2;
            color: #e0e0e0;
            box-shadow: 0 0 0 0.25rem rgba(42, 107, 194, 0.25);
        }
        .small-label {
            font-size: 0.8rem;
            color: #b0b0b0;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="header">
            <h1 class="military-title">NATO Military Drone Swarm Simulation</h1>
            <p>Enhanced Tactical Visualization Interface with Real-World Map Integration</p>
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
                
                <div class="config-panel">
                    <h4 class="military-title mb-3">Mission Configuration</h4>
                    
                    <form id="configForm">
                        <div class="mb-3">
                            <label for="timeOfDay" class="form-label">Time of Day</label>
                            <select class="form-select" id="timeOfDay">
                                <option value="day">Day</option>
                                <option value="dusk">Dusk</option>
                                <option value="night">Night</option>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label for="weather" class="form-label">Weather Conditions</label>
                            <select class="form-select" id="weather">
                                <option value="clear">Clear</option>
                                <option value="cloudy">Cloudy</option>
                                <option value="rain">Rain</option>
                                <option value="fog">Fog</option>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label for="missionType" class="form-label">Mission Type</label>
                            <select class="form-select" id="missionType">
                                <option value="strike">Strike</option>
                                <option value="recon">Reconnaissance</option>
                                <option value="defend">Defensive</option>
                                <option value="escort">Escort</option>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label for="numDrones" class="form-label">Number of Drones</label>
                            <input type="number" class="form-control" id="numDrones" min="1" max="20" value="10">
                            <div class="small-label">Friendly drone count (1-20)</div>
                        </div>
                        
                        <div class="mb-3 form-check">
                            <input type="checkbox" class="form-check-input" id="enableEnemies" checked>
                            <label class="form-check-label" for="enableEnemies">Enable Enemy Drones</label>
                        </div>
                        
                        <div class="mb-3">
                            <label for="numEnemies" class="form-label">Number of Enemy Drones</label>
                            <input type="number" class="form-control" id="numEnemies" min="1" max="10" value="3">
                            <div class="small-label">Enemy drone count (1-10)</div>
                        </div>
                    </form>
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
        
        // Configuration form elements
        const configForm = document.getElementById('configForm');
        const timeOfDay = document.getElementById('timeOfDay');
        const weather = document.getElementById('weather');
        const missionType = document.getElementById('missionType');
        const numDrones = document.getElementById('numDrones');
        const enableEnemies = document.getElementById('enableEnemies');
        const numEnemies = document.getElementById('numEnemies');

        // Status polling
        let statusInterval;
        let fetchingStatus = false;
        const updateInterval = 500; // Update every 500ms

        // Start the simulation with current configuration
        startBtn.addEventListener('click', () => {
            // Get current configuration
            const config = {
                time_of_day: timeOfDay.value,
                weather: weather.value,
                mission_type: missionType.value,
                num_drones: parseInt(numDrones.value),
                with_enemy_drones: enableEnemies.checked,
                num_enemies: parseInt(numEnemies.value)
            };
            
            // Start simulation with configuration
            fetch('/api/start_simulation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            })
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

        // Enable/disable enemy count based on checkbox
        enableEnemies.addEventListener('change', function() {
            numEnemies.disabled = !this.checked;
        });
        
        // Initialize enemy count state
        numEnemies.disabled = !enableEnemies.checked;

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
        
        # Create GeoDataManager for initial map
        geo_manager = GeoDataManager()
        geo_manager.load_terrain_data()
        geo_manager.load_map_data()
        
        # Render terrain and map data
        geo_manager.render_terrain_map(ax=ax)
        geo_manager.render_map_data(ax=ax)
        
        # Add title and styling
        ax.set_title("NATO MILITARY DRONE SWARM SIMULATION\nConfigure and Start Mission", 
                    ha='center', color='#66b2ff', fontsize=14, fontweight='bold')
        
        # Set border color
        for spine in ax.spines.values():
            spine.set_color('#173a5e')
            spine.set_linewidth(2)
        
        # Add military grid
        ax.grid(color='#1e4976', linestyle='--', linewidth=0.5, alpha=0.5)
        
        plt.savefig(placeholder_path, dpi=100, facecolor='#0a1929', bbox_inches='tight')
        plt.close(fig)

def main(host='0.0.0.0', port=5000, debug=False):
    """Main entry point for running the web visualization"""
    # Create template files
    create_template_files()
    
    # Initialize GIS data
    print("Initializing geographic data...")
    geo_manager = GeoDataManager()
    geo_manager.load_terrain_data()
    geo_manager.load_map_data()
    
    print("\nNATO MILITARY DRONE SWARM ENHANCED WEB VISUALIZATION")
    print("====================================================")
    print(f"Starting web server on {host}:{port}")
    print("Open your browser to view the simulation")
    print("Configure mission parameters and start the simulation")
    print("Press Ctrl+C to stop the server\n")
    
    # Start the Flask app
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()