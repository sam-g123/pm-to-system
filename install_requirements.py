import subprocess

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

def parse_requirements(file_path):
    """Read requirements.txt lines while ignoring comments."""
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def write_dev_requirements(reqs):
    """Write modified requirements to a new file."""
    with open(OUTPUT_FILE, "w") as f:
        for req in reqs:
            f.write(req + "\n")

def install_requirements(reqs):
    """Install dependencies safely."""
    for req in reqs:
        pkg_name = req.split("==")[0].lower()
        if pkg_name in SKIP_DEP_PACKAGES:
            print(f"⚠️ Installing {pkg_name} without dependencies (--no-deps)")
            subprocess.run(["pip", "install", "--no-deps", req], check=True)
        else:
            print(f"▶️ Installing {pkg_name} normally")
            subprocess.run(["pip", "install", req], check=True)

def main():
    reqs = parse_requirements(INPUT_FILE)
    write_dev_requirements(reqs)
    install_requirements(reqs)
    print("\n✅ Installation completed! Happy coding 🚀")

if __name__ == "__main__":
    main()
