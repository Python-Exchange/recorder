import subprocess

def list_windows():
    """List all visible windows with their IDs and names."""
    result = subprocess.run(['xdotool', 'search', '--onlyvisible', '--name', '.*'], capture_output=True, text=True)
    window_ids = result.stdout.split()
    
    windows = {}
    for win_id in window_ids:
        result = subprocess.run(['xdotool', 'getwindowname', win_id], capture_output=True, text=True)
        win_name = result.stdout.strip()
        windows[win_id] = win_name
        print(f"Window ID: {win_id}, Name: {win_name}")
    
    return windows

if __name__ == "__main__":
    list_windows()
