import platform
import time
import subprocess
import shlex
import psutil

# --- 1. UTILITY FUNCTIONS ---

def clean_app_name(raw_name):
    """Cleans the executable/process name for user display."""
    raw_name = raw_name.lower().strip()
    
    # Remove common extensions (e.g., .exe, .app, -bin)
    if raw_name.endswith(('.exe', '.app')):
        raw_name = raw_name[:-4]
    if raw_name.endswith(('-bin',)):
        raw_name = raw_name[:-4]
    
    # Specific translation/cleaning based on common executable names
    # This acts as our application map, derived from process names
    if raw_name == "google-chrome":
        return "Google Chrome"
    if raw_name == "code":
        return "Visual Studio Code"
    if raw_name == "gnome-terminal-server" or raw_name == "gnome-terminal":
        return "Terminal"
    if raw_name == "org.gnome.nautilus":
        return "Files (Nautilus)"
    if raw_name == "telegramdesktop":
        return "Telegram"
    if raw_name == "thunderbird":
        return "Mozilla Thunderbird"
        
    # Default: Capitalize and replace hyphens
    return raw_name.replace('-', ' ').title()


def get_app_name_from_pid(pid):
    """Uses psutil to get the clean application name from a Process ID (PID)."""
    try:
        proc = psutil.Process(pid)
        # Use the name (executable filename) as the basis
        raw_name = proc.name() 
        return clean_app_name(raw_name)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return "Unknown Application (No Access)"
    except Exception:
        return "Unknown Application"

# --- 2. PLATFORM HANDLERS ---

def list_open_apps_windows_macos():
    """Handler for Windows and macOS using pygetwindow + psutil."""
    import pygetwindow as gw
    results = {}
    try:
        for window in gw.getAllWindows():
            title = window.title.strip()
            
            # Use the window title to filter non-application windows early
            if not title or window.isMinimized or len(title) < 4 or "desktop" in title.lower():
                continue
            
            # --- PLATFORM-SPECIFIC PID RETRIEVAL ---
            pid = None
            if platform.system() == 'Darwin':
                # macOS: PID is generally available via pygetwindow's internal attributes
                if hasattr(window, '_kCGWindowOwnerPID'):
                    pid = window._kCGWindowOwnerPID
            # Windows PID retrieval is more complex and often fails via pygetwindow alone,
            # so the psutil approach is a reliable backup if the PID is exposed.

            if pid:
                app_name = get_app_name_from_pid(pid)
            else:
                # Fallback: Guess the app name from the process running the window handle (less reliable)
                # On Windows, psutil.Process.name() can sometimes be determined if the window handle is available.
                # Since that requires another library (pywin32), we use a title-based guess here.
                app_name = clean_app_name(title.split(' - ')[-1].split(' | ')[-1])

            # Store the data
            if app_name not in results:
                results[app_name] = set()
            results[app_name].add(title)
                
    except Exception as e:
        print(f"Error on {platform.system()}: {e}")
        
    return results


def list_open_apps_linux():
    """Handler for Linux using wmctrl -p + psutil."""
    results = {}
    
    try:
        # '-p' flag adds PID (Process ID)
        command = "wmctrl -l -x -p" 
        proc = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        
        # Format: <window_id> <desktop_id> <pid> <class_name> <host_name> <window_title>
        for line in proc.stdout.splitlines():
            parts = line.split(maxsplit=5)
            
            if len(parts) == 6:
                pid = int(parts[2])
                title = parts[5].strip()
                
                # Filter out system windows like desktop icons, task bars
                if "desktop" in title.lower() or "gnome-shell" in title.lower() or len(title) < 4:
                    continue
                
                # Get the clean application name using PID and psutil
                app_name = get_app_name_from_pid(pid)
                
                # Store the data
                if app_name not in results:
                    results[app_name] = set()
                results[app_name].add(title)

    except FileNotFoundError:
        print("Error: 'wmctrl' command not found. Please install it (e.g., 'sudo apt install wmctrl').")
    except Exception as e:
        print(f"Error on Linux: {e}")
        
    return results

# --- 3. MAIN EXECUTION LOOP ---

def get_open_apps_and_tabs():
    """
    Returns a list of open applications and tabs/windows for distraction detection.
    Format: ["AppName: window_title", "AnotherApp: another_window", ...]
    """
    current_os = platform.system()
    
    if current_os == "Linux":
        app_getter = list_open_apps_linux
    elif current_os in ["Windows", "Darwin"]:
        app_getter = list_open_apps_windows_macos
    else:
        print(f"OS {current_os} is not explicitly supported.")
        return []
    
    app_data = app_getter()
    result = []
    
    for app_name in app_data.keys():
        for title in app_data[app_name]:
            result.append(f"{app_name}: {title}")
    
    return result


def monitor_open_applications(interval_seconds=1.5):
    """Monitors open applications by running the appropriate function repeatedly."""
    
    current_os = platform.system()
    print(f"🎯 Detected OS: **{current_os}**")
    print(f"Monitoring open applications every {interval_seconds} seconds. Press Ctrl+C to stop.")
    
    if current_os == "Linux":
        app_getter = list_open_apps_linux
    elif current_os in ["Windows", "Darwin"]:
        app_getter = list_open_apps_windows_macos
    else:
        print(f"OS {current_os} is not explicitly supported.")
        return

    try:
        while True:
            # Result format: {App_Name: {Title1, Title2, ...}}
            app_data = app_getter()
            
            print(f"\n--- Open Applications ({time.strftime('%H:%M:%S', time.localtime())}) ---")
            
            if app_data:
                for app_name in sorted(app_data.keys()):
                    # Find the longest common prefix or just use the name for the app
                    print(f"App: **{app_name}**")
                    for title in sorted(list(app_data[app_name])):
                        # Truncate long titles for neatness
                        display_title = title if len(title) < 80 else title[:77] + "..."
                        print(f"    Tab/Window: {display_title}")
            else:
                print("No active application windows found.")
            
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

if __name__ == "__main__":
    monitor_open_applications(interval_seconds=1.5)