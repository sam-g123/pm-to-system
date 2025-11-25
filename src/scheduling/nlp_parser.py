# src/scheduling/nlp_parser.py
from .gemini_mcp import GeminiMCP
from .data_structures import Task

class DurationEstimator:
    def __init__(self):
        self.mcp = GeminiMCP()

    def estimate_task_duration(self, task: Task) -> float:
        if task.estimated_minutes is not None:
            return task.estimated_minutes

        minutes = self.mcp.estimate_duration(task.name, task.description)
        task.estimated_minutes = minutes
        return minutes