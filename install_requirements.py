import subprocess
import os

# List of packages known to cause dependency issues
SKIP_DEP_PACKAGES = {
    "deepface",
    "mediapipe",
    "retina-face",
    "ultralytics"
}

# Input and output files
INPUT_FILE = "requirements.txt"
OUTPUT_FILE = "requirements-dev.txt"

# Variable to store the find-links URL if present
FIND_LINKS_URL = None
FIND_LINKS_PREFIX = "--find-links "

def parse_requirements(file_path):
    """Read requirements.txt lines, ignoring comments and capturing --find-links."""
    global FIND_LINKS_URL
    requirements_list = []
    
    if not os.path.exists(file_path):
        print(f"Error: Input file '{file_path}' not found.")
        return []
        
    with open(file_path, "r") as f:
        for line in f:
            line_strip = line.strip()
            
            if not line_strip or line_strip.startswith("#"):
                continue

            if line_strip.startswith(FIND_LINKS_PREFIX):
                # Capture the URL but don't add the line to the package list
                FIND_LINKS_URL = line_strip[len(FIND_LINKS_PREFIX):].strip()
                print(f"🔗 Detected find-links URL: {FIND_LINKS_URL}")
                continue
            
            requirements_list.append(line_strip)
            
    return requirements_list

def write_dev_requirements(reqs):
    """Write modified requirements to a new file, including find-links if present."""
    with open(OUTPUT_FILE, "w") as f:
        if FIND_LINKS_URL:
            f.write(f"{FIND_LINKS_PREFIX}{FIND_LINKS_URL}\n")
        
        for req in reqs:
            f.write(req + "\n")

def install_requirements(reqs):
    """Install dependencies safely, applying find-links globally."""
    
    # 1. Build the list of extra arguments (options)
    global_options = []
    if FIND_LINKS_URL:
        # Append the option and its value as separate elements
        global_options.extend(["--find-links", FIND_LINKS_URL])

    # 2. Iterate and install packages
    for req in reqs:
        pkg_name = req.split("==")[0].split(">")[0].split("<")[0].lower() # Handles all specifiers
        
        # Base command: python3.10 -m pip install [GLOBAL_OPTIONS]
        command = ["python3.10", "-m", "pip", "install"] + global_options
        
        if pkg_name in SKIP_DEP_PACKAGES:
            print(f"⚠️ Installing {pkg_name} without dependencies (--no-deps)")
            command.append("--no-deps")
        else:
            print(f"▶️ Installing {pkg_name} normally")
            
        # Append the specific package requirement
        command.append(req)
        
        # Execute the command
        subprocess.run(command, check=True)

def main():
    print(f"Reading requirements from {INPUT_FILE}...")
    reqs = parse_requirements(INPUT_FILE)
    if not reqs and not FIND_LINKS_URL:
        print("No requirements found to process.")
        return
        
    write_dev_requirements(reqs)
    
    print("\nStarting installation process...")
    install_requirements(reqs)
    
    print("\n✅ Installation completed! Happy coding 🚀")

if __name__ == "__main__":
    main()
