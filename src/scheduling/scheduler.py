# src/scheduling/scheduler.py
from datetime import datetime
from typing import Optional, List, Dict, Any
from .data_structures import Task, TaskStatus
from .nlp_parser import DurationEstimator
from .feedback_loop import DistractionWatcher


class Scheduler:
    """
    Task scheduling system with Gemini-powered features.
    
    Features:
    1. Task Duration Estimation - Uses Gemini to estimate how long tasks take
    2. Distraction Monitoring - Detects and alerts on potentially distracting apps
    3. Task Status Management - Tracks task lifecycle (due, in progress, completed)
    """
    
    def __init__(self, db_path: str = ":memory:", parent_widget=None):
        """
        Initialize the scheduler.
        
        Args:
            db_path: Path to SQLite database (":memory:" for in-memory)
            parent_widget: PyQt5 widget for displaying dialogs (optional)
        """
        self.tasks: List[Task] = []
        self.estimator = DurationEstimator()
        self.watcher = DistractionWatcher(parent_widget)
        self.parent_widget = parent_widget
        self.current_task: Optional[Task] = None

    def add_task(self, task: Task) -> Task:
        """
        Add a task to the scheduler.
        
        Args:
            task: Task object to add
            
        Returns:
            The added task
        """
        self.tasks.append(task)
        return task

    def estimate_task_duration(self, task: Task) -> float:
        """
        Estimate the duration of a task using Gemini.
        Updates the task object with the estimate.
        
        Args:
            task: Task to estimate
            
        Returns:
            Estimated duration in minutes
        """
        if task.estimated_minutes is not None:
            return task.estimated_minutes
        
        minutes = self.estimator.estimate_task_duration(task)
        task.estimated_minutes = minutes
        return minutes

    def start_task(self, task: Task) -> Dict[str, Any]:
        """
        Start working on a task.
        
        1. Update task status to IN_PROGRESS
        2. Estimate duration if not already done
        3. Set started_at timestamp
        4. Start distraction monitoring
        
        Args:
            task: Task to start
            
        Returns:
            Dictionary with task info and any status messages
        """
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        self.current_task = task
        
        result = {
            "status": "started",
            "task_name": task.name,
            "task_id": task.id,
            "messages": []
        }

        # 1. Estimate duration if missing
        if task.estimated_minutes is None:
            try:
                duration = self.estimate_task_duration(task)
                msg = f"Gemini estimated '{task.name}': {duration:.0f} minutes"
                result["messages"].append(msg)
                result["estimated_minutes"] = duration
                print(msg)
            except Exception as e:
                error_msg = f"Duration estimation failed: {e}"
                result["messages"].append(error_msg)
                print(error_msg)

        # 2. Start distraction monitoring (optional - can be called separately)
        # This is now called on-demand from the UI
        
        return result

    def complete_task(self, task: Task) -> Dict[str, Any]:
        """
        Mark a task as completed.
        
        Args:
            task: Task to complete
            
        Returns:
            Dictionary with completion info
        """
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        
        if self.current_task == task:
            self.current_task = None
        
        # Calculate actual duration
        actual_duration = None
        if task.started_at and task.completed_at:
            duration_seconds = (task.completed_at - task.started_at).total_seconds()
            actual_duration = duration_seconds / 60
        
        return {
            "status": "completed",
            "task_name": task.name,
            "task_id": task.id,
            "estimated_minutes": task.estimated_minutes,
            "actual_minutes": actual_duration
        }

    def suspend_task(self, task: Task) -> Dict[str, Any]:
        """
        Suspend a task without completing it.
        
        Args:
            task: Task to suspend
            
        Returns:
            Dictionary with suspension info
        """
        task.status = TaskStatus.SUSPENDED
        
        return {
            "status": "suspended",
            "task_name": task.name,
            "task_id": task.id
        }

    def check_distractions(self, task: Task) -> Dict[str, Any]:
        """
        Check for distractions for a given task.
        Uses Gemini to analyze open apps/tabs.
        
        Args:
            task: Task to check distractions for
            
        Returns:
            Dictionary with distractions, rationale, and suggestions
        """
        return self.watcher.check_distractions_sync(task)

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Get a task by its ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return self.tasks

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status."""
        return [task for task in self.tasks if task.status == status]