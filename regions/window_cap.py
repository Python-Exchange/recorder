import subprocess
import threading
import time
import sys
from pynput import keyboard
import os

def capture_region(region, stop_event, fps=30, audio_device="/dev/dsp10"):
    """Capture the specified region using ffmpeg."""
    x, y, width, height = region
    output_file = f"region_{x}_{y}.mkv"
    print(f"Recording region at ({x},{y}) with dimensions {width}x{height}")

    ffmpeg_command = [
        'ffmpeg', '-y', '-f', 'x11grab', '-r', str(fps), '-s', f'{width}x{height}', 
        '-i', f':0.0+{x},{y}', '-f', 'oss', '-i', audio_device, 
        '-vcodec', 'libx264', '-preset', 'ultrafast', '-crf', '0', '-pix_fmt', 'yuv420p', 
        '-acodec', 'aac', '-b:a', '192k', output_file
    ]
    
    process = subprocess.Popen(ffmpeg_command)
    
    while not stop_event.is_set():
        time.sleep(1)
    
    process.terminate()
    process.wait()
    
    print(f"Recording stopped for region ({x},{y}) with dimensions {width}x{height}")

class Recorder:
    def __init__(self):
        self.processes = []
        self.regions = []
        self.recording = False
        self.listener = None
        self.stop_events = []

    def on_activate(self):
        if self.recording:
            for stop_event, process in zip(self.stop_events, self.processes):
                stop_event.set()
                process.join()
            self.recording = False
            print("Recording stopped.")
        else:
            self.stop_events = [threading.Event() for _ in self.regions]
            self.processes = [
                threading.Thread(target=capture_region, args=(region, stop_event))
                for region, stop_event in zip(self.regions, self.stop_events)
            ]
            for process in self.processes:
                process.start()
            self.recording = True
            print("Recording started.")

    def start_listener(self):
        with keyboard.GlobalHotKeys({
            '<cmd>+s': self.on_activate,
        }) as self.listener:
            self.listener.join()

def main():
    if len(sys.argv) < 2:
        print("Usage: python record_windows.py <config_file>")
        return

    config_file = sys.argv[1]
    
    if not os.path.isfile(config_file):
        print(f"Config file not found: {config_file}")
        return

    with open(config_file, 'r') as f:
        regions = []
        for line in f:
            if line.strip():
                x, y, width, height = map(int, line.strip().split(','))
                regions.append((x, y, width, height))

    if not regions:
        print("No regions found in the config file.")
        return

    recorder = Recorder()
    recorder.regions = regions

    print("Press Cmd+S to start and stop recording.")
    
    listener_thread = threading.Thread(target=recorder.start_listener)
    listener_thread.start()
    listener_thread.join()

if __name__ == "__main__":
    main()
