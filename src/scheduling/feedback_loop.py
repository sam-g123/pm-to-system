# src/scheduling/feedback_loop.py
import time
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from .gemini_mcp import GeminiMCP
from .open_apps import get_open_apps_and_tabs
from .data_structures import Task
from typing import Dict, Any, Optional, List


class DistractionWatcher:
    """
    Monitors open applications for distractions relevant to the current task.
    Can operate standalone or integrated with UI.
    """
    def __init__(self, parent_widget=None):
        self.mcp = GeminiMCP()
        self.parent = parent_widget
        self.last_check = 0
        self.check_interval = 60  # seconds

    def maybe_warn(self, current_task: Task) -> Optional[Dict[str, Any]]:
        """
        Check for distractions and show warning if needed.
        
        Args:
            current_task: The task currently being worked on
            
        Returns:
            Distraction detection result or None if check skipped
        """
        now = time.time()
        if now - self.last_check < self.check_interval:
            return None
        self.last_check = now

        open_items = get_open_apps_and_tabs()
        try:
            result = self.mcp.detect_distractions(
                task={"name": current_task.name, "attached_apps": current_task.attached_apps},
                open_items=open_items
            )
            
            # Show warning if distractions found and parent widget exists
            distractions = result.get("distractions", [])
            if distractions and self.parent:
                msg = QMessageBox(self.parent)
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Focus Alert")
                msg.setText(
                    f"Possible distractions detected:\n" +
                    "\n".join(distractions[:5]) +
                    f"\n\n{result.get('rationale', '')}\n\n{result.get('suggestion', '')}"
                )
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            
            return result
        except Exception as e:
            print(f"Distraction check failed: {e}")
            return None

    def check_distractions_sync(self, current_task: Task) -> Dict[str, Any]:
        """
        Synchronously check for distractions without time throttling.
        Useful for on-demand checks from the UI.
        
        Args:
            current_task: The task currently being worked on
            
        Returns:
            Distraction detection result with distractions, rationale, and suggestion
        """
        open_items = get_open_apps_and_tabs()
        result = self.mcp.detect_distractions(
            task={"name": current_task.name, "attached_apps": current_task.attached_apps},
            open_items=open_items
        )
        return result


class DistractionCheckThread(QThread):
    """
    Background thread for performing distraction checks without blocking the UI.
    """
    check_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, task: Task):
        super().__init__()
        self.task = task
        self.watcher = DistractionWatcher()
    
    def run(self):
        """Execute distraction check in background thread."""
        try:
            result = self.watcher.check_distractions_sync(self.task)
            self.check_complete.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))