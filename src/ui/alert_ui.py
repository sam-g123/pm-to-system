# src/ui/alert_ui.py

from PyQt5.QtWidgets import QMessageBox
import pygame.mixer # Import only the mixer part of pygame

# --- Configuration ---
ALERT_SOUND_FILE = "beep.wav"

# --- Initialization ---
try:
    # 1. Initialize the pygame mixer once
    pygame.mixer.init()
    # 2. Load the sound file immediately upon import for quick playback later
    ALERT_SOUND = pygame.mixer.Sound(ALERT_SOUND_FILE)
    IS_SOUND_READY = True
except Exception as e:
    print(f"Failed to initialize Pygame mixer or load sound file: {e}")
    print(f"Ensure '{ALERT_SOUND_FILE}' is a valid WAV/MP3 file and accessible.")
    IS_SOUND_READY = False

def show_popup_alert():
    """Creates a simple message box alert and triggers the beep sound."""
    
    # 1. Play the sound (no need for a separate thread, as pygame's play() is non-blocking)
    if IS_SOUND_READY:
        # play() starts playback and returns immediately
        ALERT_SOUND.play() 
    
    # 2. Display the QMessageBox (which blocks until the user clicks OK)
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("⚠️ Focus Warning!")
    msg.setText("5 SECONDS OF NON-CONCENTRATION DETECTED!")
    msg.setStandardButtons(QMessageBox.Ok)
    
    msg.exec_()