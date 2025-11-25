from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class TaskStatus(str, Enum):
    DUE = "due"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SUSPENDED = "suspended"

@dataclass
class Task:
    id: int
    name: str
    description: str = ""
    attached_apps: List[str] = field(default_factory=list)  # e.g. ["word", "excel"]
    status: TaskStatus = TaskStatus.DUE
    estimated_minutes: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None