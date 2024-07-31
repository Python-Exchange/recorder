import subprocess
import threading
import time
import sys
from pynput import keyboard
import os

def get_window_geometry(window_id):
    """Get the geometry of the specified window."""
    result = subprocess.run(['xdotool', 'getwindowgeometry', '--shell', window_id], capture_output=True, text=True)
    geometry = {}
    for line in result.stdout.splitlines():
        if '=' in line:
            key, value = line.split('=')
            geometry[key] = int(value)
    return geometry

def capture_window(window_id, stop_event, fps=30):
    """Capture the specified window using ffmpeg."""
    segment_index = 0
    output_dir = f"{window_id}_segments"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Recording window {window_id}")

    while not stop_event.is_set():
        geometry = get_window_geometry(window_id)
        width = (geometry['WIDTH'] // 2) * 2
        height = (geometry['HEIGHT'] // 2) * 2
        x = geometry['X']
        y = geometry['Y']
        
        segment_file = os.path.join(output_dir, f"segment_{segment_index:04d}.mkv")
        segment_index += 1
        print(f"Recording segment {segment_file} with dimensions {width}x{height} at position {x},{y}")
        
        ffmpeg_command = [
            'ffmpeg', '-y', '-f', 'x11grab', '-r', str(fps), '-s', f'{width}x{height}', 
            '-i', f':0.0+{x},{y}', '-vcodec', 'libx264', '-preset', 'ultrafast', '-crf', '0', 
            '-pix_fmt', 'yuv420p', segment_file
        ]
        
        process = subprocess.Popen(ffmpeg_command)
        
        while not stop_event.is_set():
            time.sleep(1)
            new_geometry = get_window_geometry(window_id)
            new_width = (new_geometry['WIDTH'] // 2) * 2
            new_height = (new_geometry['HEIGHT'] // 2) * 2
            new_x = new_geometry['X']
            new_y = new_geometry['Y']
            
            if (width != new_width) or (height != new_height) or (x != new_x) or (y != new_y):
                width, height, x, y = new_width, new_height, new_x, new_y
                break

        process.terminate()
        process.wait()
        
    print("Recording stopped.")
    concatenate_segments(output_dir, f"{window_id}_output.mkv")

def concatenate_segments(segment_dir, output_file):
    """Concatenate all segments into a single output file."""
    filelist_path = os.path.join(segment_dir, "filelist.txt")
    with open(filelist_path, 'w') as filelist:
        for segment in sorted(os.listdir(segment_dir)):
            if segment.endswith(".mkv"):
                filelist.write(f"file '{os.path.abspath(os.path.join(segment_dir, segment))}'\n")
    
    concat_command = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', filelist_path,
        '-c', 'copy', output_file
    ]
    
    subprocess.run(concat_command)
    print(f"Output file created: {output_file}")

class Recorder:
    def __init__(self):
        self.processes = []
        self.window_ids = []
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
            self.stop_events = [threading.Event() for _ in self.window_ids]
            self.processes = [
                threading.Thread(target=capture_window, args=(window_id, stop_event))
                for window_id, stop_event in zip(self.window_ids, self.stop_events)
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
        window_ids = [line.strip() for line in f if line.strip()]

    if not window_ids:
        print("No window IDs found in the config file.")
        return

    recorder = Recorder()
    recorder.window_ids = window_ids

    print("Press Cmd+S to start and stop recording.")
    
    listener_thread = threading.Thread(target=recorder.start_listener)
    listener_thread.start()
    listener_thread.join()

if __name__ == "__main__":
    main()
