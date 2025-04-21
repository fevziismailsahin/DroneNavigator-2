"""
Spatial Audio System for NATO Military Drone Swarm Simulation

This module provides realistic military sound effects with spatial audio positioning
based on the simulation state. It uses PyDub for sound processing and pygame for playback.

Note: In headless environments like Replit, the audio system will operate in a "silent mode"
where all the sound generation and spatial positioning code still runs but no actual
sound is played. This allows the simulation to work in environments without audio devices.
"""

import os
import math
import numpy as np
import pygame
from pydub import AudioSegment
from pydub.generators import Sine, WhiteNoise

# Global flag to track if audio is available
AUDIO_AVAILABLE = False

# Try to initialize the sound system, but don't crash if it fails
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    AUDIO_AVAILABLE = True
    print("Audio system initialized successfully.")
except pygame.error:
    print("Warning: Audio device not available. Running in silent mode.")
    # Create a mock pygame.mixer to prevent crashes
    class MockMixer:
        class Sound:
            def __init__(self, *args, **kwargs):
                pass
            def play(self, *args, **kwargs):
                pass
            def stop(self, *args, **kwargs):
                pass
        
        class Channel:
            def __init__(self, *args, **kwargs):
                pass
            def play(self, *args, **kwargs):
                pass
            def stop(self, *args, **kwargs):
                pass
            def get_busy(self, *args, **kwargs):
                return False
            def set_volume(self, *args, **kwargs):
                pass
        
        @staticmethod
        def find_channel(*args, **kwargs):
            return MockMixer.Channel()
        
        @staticmethod
        def Sound(*args, **kwargs):
            return MockMixer.Sound()
        
        class music:
            @staticmethod
            def set_volume(*args, **kwargs):
                pass
    
    # Replace pygame.mixer with our mock if it's not available
    if not hasattr(pygame, 'mixer') or pygame.mixer is None:
        pygame.mixer = MockMixer()

class SpatialAudioSystem:
    """Handles spatial audio for the military drone swarm simulation."""
    
    def __init__(self, output_dir="audio_cache"):
        """
        Initialize the spatial audio system.
        
        Args:
            output_dir (str): Directory for cached audio files
        """
        # Create output directory if it doesn't exist
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Dictionary to store sound effects
        self.sounds = {}
        
        # Generate and load sound effects
        self.generate_sound_effects()
        
        # Dictionary to track currently playing sounds
        self.active_sounds = {}
        
        # Set master volume
        pygame.mixer.music.set_volume(0.8)
        
        # Initialize listener position at center
        self.listener_pos = (50, 50)
        
        # Flag to track if audio system is enabled
        self.enabled = True
        
    def generate_sound_effects(self):
        """Generate various military sound effects."""
        # Generate drone buzzing sound
        self._generate_drone_sound()
        
        # Generate turret alert/firing sounds
        self._generate_turret_sounds()
        
        # Generate explosion sounds
        self._generate_explosion_sounds()
        
        # Generate alert sounds
        self._generate_alert_sounds()
        
        # Generate ambient background
        self._generate_ambient_background()
        
    def _generate_drone_sound(self):
        """Generate realistic drone buzzing sound."""
        # Create a base drone buzz using a combination of sine waves
        base_freq = 100
        duration_ms = 2000
        
        # Start with a base sine wave
        drone_sound = Sine(base_freq).to_audio_segment(duration=duration_ms)
        
        # Add harmonics for more realistic drone sound
        harmonics = [1.5, 2, 3, 4.5]
        for harmonic in harmonics:
            harmonic_sound = Sine(base_freq * harmonic).to_audio_segment(duration=duration_ms)
            drone_sound = drone_sound.overlay(harmonic_sound - 12)  # Reduce volume of harmonics
            
        # Add some noise for texture
        noise = WhiteNoise().to_audio_segment(duration=duration_ms) - 20
        drone_sound = drone_sound.overlay(noise)
        
        # Apply some effects to make it sound more mechanical
        drone_sound = drone_sound.compress_dynamic_range()
        
        # Loop the sound by crossfading
        drone_sound = drone_sound.append(drone_sound, crossfade=100).append(drone_sound, crossfade=100)
        
        # Export to file
        drone_path = os.path.join(self.output_dir, "drone_buzz.wav")
        drone_sound.export(drone_path, format="wav")
        
        # Load into pygame
        self.sounds["drone"] = pygame.mixer.Sound(drone_path)
        
    def _generate_turret_sounds(self):
        """Generate turret detection and firing sounds."""
        # Turret alert sound (radar-like ping)
        ping_duration = 500
        ping = Sine(1200).to_audio_segment(duration=ping_duration)
        ping = ping.fade_in(50).fade_out(400)
        
        ping_path = os.path.join(self.output_dir, "turret_ping.wav")
        ping.export(ping_path, format="wav")
        self.sounds["turret_alert"] = pygame.mixer.Sound(ping_path)
        
        # Turret firing sound
        shot_duration = 300
        shot = WhiteNoise().to_audio_segment(duration=shot_duration) - 5
        
        # Add a lower frequency boom
        boom = Sine(80).to_audio_segment(duration=shot_duration) - 5
        shot = shot.overlay(boom)
        
        # Shape the sound with fades
        shot = shot.fade_in(10).fade_out(200)
        
        shot_path = os.path.join(self.output_dir, "turret_fire.wav")
        shot.export(shot_path, format="wav")
        self.sounds["turret_fire"] = pygame.mixer.Sound(shot_path)
        
    def _generate_explosion_sounds(self):
        """Generate explosion sounds for drone/target destruction."""
        # Drone destruction (small explosion)
        drone_exp_duration = 1000
        drone_exp = WhiteNoise().to_audio_segment(duration=drone_exp_duration) - 5
        
        # Add low frequency for boom effect
        boom = Sine(60).to_audio_segment(duration=drone_exp_duration)
        drone_exp = drone_exp.overlay(boom)
        
        # Shape the explosion
        drone_exp = drone_exp.fade_in(20).fade_out(800)
        
        drone_exp_path = os.path.join(self.output_dir, "drone_explosion.wav")
        drone_exp.export(drone_exp_path, format="wav")
        self.sounds["drone_destroyed"] = pygame.mixer.Sound(drone_exp_path)
        
        # Target destruction (larger explosion)
        target_exp_duration = 2000
        target_exp = WhiteNoise().to_audio_segment(duration=target_exp_duration)
        
        # Add multiple frequency layers for a more complex explosion
        freqs = [40, 60, 90, 120]
        for freq in freqs:
            bass = Sine(freq).to_audio_segment(duration=target_exp_duration) - 5
            target_exp = target_exp.overlay(bass)
        
        # Shape the explosion with longer tail
        target_exp = target_exp.fade_in(10).fade_out(1500)
        
        target_exp_path = os.path.join(self.output_dir, "target_explosion.wav")
        target_exp.export(target_exp_path, format="wav")
        self.sounds["target_destroyed"] = pygame.mixer.Sound(target_exp_path)
        
    def _generate_alert_sounds(self):
        """Generate alert and notification sounds."""
        # Mission start alert
        start_alert = Sine(440).to_audio_segment(duration=200)  # A4
        start_alert = start_alert.append(Sine(587.33).to_audio_segment(duration=200))  # D5
        start_alert = start_alert.append(Sine(659.25).to_audio_segment(duration=400))  # E5
        
        start_alert_path = os.path.join(self.output_dir, "mission_start.wav")
        start_alert.export(start_alert_path, format="wav")
        self.sounds["mission_start"] = pygame.mixer.Sound(start_alert_path)
        
        # Mission complete alert
        complete_alert = Sine(659.25).to_audio_segment(duration=200)  # E5
        complete_alert = complete_alert.append(Sine(587.33).to_audio_segment(duration=200))  # D5
        complete_alert = complete_alert.append(Sine(440).to_audio_segment(duration=200))  # A4
        complete_alert = complete_alert.append(Sine(659.25).to_audio_segment(duration=400))  # E5
        
        complete_alert_path = os.path.join(self.output_dir, "mission_complete.wav")
        complete_alert.export(complete_alert_path, format="wav")
        self.sounds["mission_complete"] = pygame.mixer.Sound(complete_alert_path)
        
        # Warning alert
        warning_alert = Sine(880).to_audio_segment(duration=200)  # A5
        warning_alert = warning_alert.append(Sine(830.61).to_audio_segment(duration=200))  # G#5
        warning_alert = warning_alert.append(Sine(880).to_audio_segment(duration=200))  # A5
        
        warning_alert_path = os.path.join(self.output_dir, "warning.wav")
        warning_alert.export(warning_alert_path, format="wav")
        self.sounds["warning"] = pygame.mixer.Sound(warning_alert_path)
        
    def _generate_ambient_background(self):
        """Generate ambient background sound for mission environment."""
        # Create 10-second ambient background
        duration_ms = 10000
        
        # Base layer of white noise (reduced volume for background)
        ambient = WhiteNoise().to_audio_segment(duration=duration_ms) - 30
        
        # Add low drone hum
        hum = Sine(40).to_audio_segment(duration=duration_ms) - 20
        ambient = ambient.overlay(hum)
        
        # Add occasional high-frequency "beeps" for command center feel
        for pos in [2000, 5000, 8000]:
            beep = Sine(2400).to_audio_segment(duration=100) - 25
            ambient = ambient.overlay(beep, position=pos)
        
        # Export ambient background
        ambient_path = os.path.join(self.output_dir, "ambient_background.wav")
        ambient.export(ambient_path, format="wav")
        self.sounds["ambient"] = pygame.mixer.Sound(ambient_path)
    
    def set_listener_position(self, x, y):
        """
        Set the listener position for spatial audio calculation.
        
        Args:
            x (float): X-coordinate of listener
            y (float): Y-coordinate of listener 
        """
        self.listener_pos = (x, y)
    
    def calculate_spatial_params(self, x, y):
        """
        Calculate volume and stereo balance based on position.
        
        Args:
            x (float): X-coordinate of sound source
            y (float): Y-coordinate of sound source
            
        Returns:
            tuple: (volume, pan) where:
                  volume is 0.0-1.0 for distance attenuation
                  pan is -1.0 (left) to 1.0 (right)
        """
        # Calculate distance from listener
        dx = x - self.listener_pos[0]
        dy = y - self.listener_pos[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Volume based on distance (inverse square law with some limits)
        max_distance = 100.0  # Maximum distance at which sounds are audible
        if distance > max_distance:
            volume = 0.0
        else:
            # Inverse square law with minimum volume
            volume = max(0.05, min(1.0, 1.0 / (1.0 + distance/20.0)))
        
        # Pan based on relative position to listener
        # Convert angle to pan value (-1 to 1)
        if dx == 0:
            pan = 0  # Sound is centered
        else:
            angle = math.atan2(dy, dx)
            # Map angle (-pi to pi) to pan (-1 to 1)
            pan = math.sin(angle)
            
        return volume, pan
    
    def play_sound(self, sound_name, x, y, loop=False):
        """
        Play a sound with appropriate spatial positioning.
        
        Args:
            sound_name (str): Name of sound to play
            x (float): X-coordinate of sound source
            y (float): Y-coordinate of sound source
            loop (bool): Whether to loop the sound
        
        Returns:
            pygame.mixer.Channel: The channel on which the sound is playing
        """
        if not self.enabled or sound_name not in self.sounds:
            return None
            
        # Calculate spatial parameters
        volume, pan = self.calculate_spatial_params(x, y)
        
        # Find a free channel
        channel = pygame.mixer.find_channel()
        if channel is None:
            # If no free channel, try to stop the oldest sound
            if len(self.active_sounds) > 0:
                oldest_sound = list(self.active_sounds.keys())[0]
                self.stop_sound(oldest_sound)
                channel = pygame.mixer.find_channel()
            
            # If still no free channel, give up
            if channel is None:
                return None
        
        # Set volume and pan
        channel.set_volume(volume * 0.8, volume * 0.8)
        if pan < 0:
            # Pan left - reduce right channel
            channel.set_volume(volume, volume * (1 + pan))
        else:
            # Pan right - reduce left channel
            channel.set_volume(volume * (1 - pan), volume)
            
        # Play the sound
        sound = self.sounds[sound_name]
        channel.play(sound, loops=-1 if loop else 0)
        
        # Store active sound reference
        sound_id = f"{sound_name}_{id(channel)}"
        self.active_sounds[sound_id] = {
            "channel": channel,
            "name": sound_name,
            "position": (x, y),
            "loop": loop
        }
        
        return sound_id
        
    def update_sound_position(self, sound_id, x, y):
        """
        Update the position of a currently playing sound.
        
        Args:
            sound_id (str): ID of the sound to update
            x (float): New X-coordinate 
            y (float): New Y-coordinate
        """
        if not self.enabled or sound_id not in self.active_sounds:
            return
            
        # Calculate new spatial parameters
        volume, pan = self.calculate_spatial_params(x, y)
        
        # Update channel settings
        channel = self.active_sounds[sound_id]["channel"]
        
        # Set volume and pan
        if pan < 0:
            # Pan left - reduce right channel
            channel.set_volume(volume, volume * (1 + pan))
        else:
            # Pan right - reduce left channel
            channel.set_volume(volume * (1 - pan), volume)
            
        # Update stored position
        self.active_sounds[sound_id]["position"] = (x, y)
    
    def stop_sound(self, sound_id):
        """
        Stop a currently playing sound.
        
        Args:
            sound_id (str): ID of the sound to stop
        """
        if sound_id in self.active_sounds:
            self.active_sounds[sound_id]["channel"].stop()
            del self.active_sounds[sound_id]
    
    def play_drone_sound(self, drone_id, x, y):
        """
        Play drone buzzing sound at the specified position.
        
        Args:
            drone_id (int): Unique identifier for the drone
            x (float): X-coordinate of the drone
            y (float): Y-coordinate of the drone
            
        Returns:
            str: Sound ID for updating position
        """
        sound_id = f"drone_{drone_id}"
        # Stop previous sound for this drone if it exists
        if sound_id in self.active_sounds:
            self.stop_sound(sound_id)
        
        # Play new sound
        return self.play_sound("drone", x, y, loop=True)
    
    def play_turret_alert(self, turret_id, x, y):
        """Play turret alert/ping sound."""
        return self.play_sound("turret_alert", x, y)
    
    def play_turret_fire(self, turret_id, x, y):
        """Play turret firing sound."""
        return self.play_sound("turret_fire", x, y)
    
    def play_drone_destroyed(self, x, y):
        """Play drone destruction sound."""
        return self.play_sound("drone_destroyed", x, y)
    
    def play_target_destroyed(self, x, y):
        """Play target destruction sound."""
        return self.play_sound("target_destroyed", x, y)
    
    def play_mission_start(self):
        """Play mission start sound (centered)."""
        return self.play_sound("mission_start", self.listener_pos[0], self.listener_pos[1])
    
    def play_mission_complete(self):
        """Play mission complete sound (centered)."""
        return self.play_sound("mission_complete", self.listener_pos[0], self.listener_pos[1])
    
    def play_warning(self, x, y):
        """Play warning alert sound."""
        return self.play_sound("warning", x, y)
    
    def play_ambient(self):
        """Play ambient background sound (centered and looped)."""
        return self.play_sound("ambient", self.listener_pos[0], self.listener_pos[1], loop=True)
    
    def update_active_sounds(self):
        """
        Update all active sound parameters.
        Call this periodically to refresh spatial audio.
        """
        # Make a copy of keys to avoid dictionary size change during iteration
        for sound_id in list(self.active_sounds.keys()):
            if sound_id in self.active_sounds:  # Check again in case it was removed
                sound_info = self.active_sounds[sound_id]
                if not sound_info["channel"].get_busy():
                    # Sound finished playing
                    del self.active_sounds[sound_id]
                else:
                    # Update position based on current data
                    x, y = sound_info["position"]
                    volume, pan = self.calculate_spatial_params(x, y)
                    
                    channel = sound_info["channel"]
                    if pan < 0:
                        channel.set_volume(volume, volume * (1 + pan))
                    else:
                        channel.set_volume(volume * (1 - pan), volume)
    
    def enable(self):
        """Enable the audio system."""
        self.enabled = True
        
    def disable(self):
        """Disable the audio system and stop all sounds."""
        self.enabled = False
        self.stop_all()
    
    def stop_all(self):
        """Stop all currently playing sounds."""
        for sound_id in list(self.active_sounds.keys()):
            self.stop_sound(sound_id)
        
    def cleanup(self):
        """Clean up resources when done."""
        self.stop_all()
        pygame.mixer.quit()


# Example usage
if __name__ == "__main__":
    import time
    
    # Create audio system
    audio = SpatialAudioSystem()
    
    # Play mission start sound
    audio.play_mission_start()
    time.sleep(1)
    
    # Play drone sounds at different positions
    drone1 = audio.play_drone_sound(1, 10, 10)
    drone2 = audio.play_drone_sound(2, 90, 90)
    
    # Move drones around
    for i in range(20):
        audio.update_sound_position(drone1, 10 + i*4, 10)
        audio.update_sound_position(drone2, 90 - i*4, 90)
        time.sleep(0.2)
    
    # Play a turret alert and fire
    audio.play_turret_alert(1, 50, 50)
    time.sleep(0.5)
    audio.play_turret_fire(1, 50, 50)
    time.sleep(0.2)
    
    # Play explosion sound
    audio.play_drone_destroyed(50, 20)
    time.sleep(1)
    
    # Play target destroyed
    audio.play_target_destroyed(70, 70)
    time.sleep(2)
    
    # Clean up
    audio.cleanup()
    print("Audio demonstration complete")