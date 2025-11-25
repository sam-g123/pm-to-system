# Schedule UI Integration with Gemini AI

## Overview

The updated Schedule UI (`schedule_widget_new.py`) now integrates Gemini AI-powered features to enhance task planning and focus management:

1. **Task Duration Estimation** - Automatically estimates how long a task will take
2. **Distraction Warning System** - Detects and alerts you to potentially distracting applications
3. **Productivity Insights** - Provides personalized recommendations based on focus metrics

## Architecture

### Components

#### 1. `schedule_widget_new.py` (ScheduleWidgetNew)

The main PyQt5 widget that provides:

- Task input form (name, description, attached apps)
- Duration estimation display
- Distraction warning interface
- Active task tracking
- Integration with productivity scoring

**Key Classes:**

- `TaskEstimationWorker`: Background thread for duration estimation
- `DistractionCheckWorker`: Background thread for distraction detection
- `ScheduleWidgetNew`: Main UI widget

#### 2. `gemini_mcp.py` (GeminiMCP)

Handles all Gemini AI API calls:

**Methods:**

- `estimate_duration(task_name, description)` → Returns estimated minutes
- `detect_distractions(task, open_items)` → Returns dict with distractions, rationale, suggestion

**Features:**

- Forces JSON output for reliable parsing
- Uses Gemini 1.5 Flash for fast, cost-effective processing
- Few-shot examples in prompts for better accuracy

#### 3. `scheduler.py` (Scheduler)

Core scheduling logic that orchestrates the system:

**Methods:**

- `add_task(task)` - Add a task to tracking
- `estimate_task_duration(task)` - Estimate duration via Gemini
- `start_task(task)` - Begin task with duration estimation
- `complete_task(task)` - Mark task as done
- `check_distractions(task)` - Check for focus distractions
- `get_tasks_by_status(status)` - Filter tasks

#### 4. `feedback_loop.py` (DistractionWatcher)

Manages distraction detection and user alerts:

**Classes:**

- `DistractionWatcher`: Monitors and warns about distractions
- `DistractionCheckThread`: Background thread for checks

**Key Methods:**

- `maybe_warn(task)` - Time-throttled check (60 sec interval)
- `check_distractions_sync(task)` - On-demand immediate check

#### 5. `open_apps.py`

Detects open applications and windows:

**Main Function:**

- `get_open_apps_and_tabs()` - Returns list of open apps and window titles
  - Format: `["AppName: window_title", "Browser: [youtube.com/watch?v=xyz]", ...]`
  - Platform-aware (Linux, Windows, macOS)
  - Cross-platform app name normalization

**Platform Support:**

- **Linux**: Uses `wmctrl -l -x -p` + `psutil`
- **Windows/macOS**: Uses `pygetwindow` + `psutil`

## Workflow

### 1. Adding and Estimating a Task

```
User Input
    ↓
Create Task Object
    ↓
Manual Duration Override? → Yes → Skip Gemini
    ↓ No
TaskEstimationWorker Thread
    ↓
GeminiMCP.estimate_duration()
    ↓
Display Result
```

**Example:**

- Task: "Write report on Q3 sales"
- Description: "Draft sections for executive summary, analyze data from Q3_data.csv, create 5 slides"
- Attached Apps: "word, excel, powerpoint"
- Result: 2.5 hours (150 minutes)

### 2. Starting a Task and Checking Distractions

```
User Clicks "Start Task"
    ↓
Update Task Status → IN_PROGRESS
    ↓
DistractionCheckWorker Thread
    ↓
get_open_apps_and_tabs()
    ↓
GeminiMCP.detect_distractions()
    ↓
Parse Results
    ↓
Display Warnings
```

**Example:**

- Current Task: "Write report" with Attached Apps: [word, excel]
- Open Apps: [Firefox (youtube.com), VLC, Code, Word]
- Gemini Analysis: "YouTube and VLC are entertainment apps, not required for report writing"
- User Alert: Warning message with suggestions to close distractions

### 3. Continuous Monitoring

```
Every 10 Seconds
    ↓
Check Productivity Scoring
    ↓
Update Break Recommendations
    ↓
Update Feedback Messages
```

## Configuration

### Environment Variables

Required:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

### Duration Estimation Settings

In `gemini_mcp.py`:

```python
generation_config={
    "temperature": 0.2,  # Lower = more deterministic
    "response_mime_type": "application/json",  # Forces JSON output
}
```

### Distraction Check Interval

In `feedback_loop.py`:

```python
self.check_interval = 60  # seconds between checks when using maybe_warn()
```

## Usage Examples

### Basic Task Creation and Estimation

```python
from src.ui.widgets.schedule_widget_new import ScheduleWidgetNew

# Create widget
widget = ScheduleWidgetNew()

# User inputs task via UI:
# Name: "Write report on Q3 sales"
# Description: "Draft sections for executive summary, analyze data..."
# Apps: "word, excel, powerpoint"

# Click "Add Task & Estimate Duration"
# → Gemini estimates: 2.5 hours
# → Display result
```

### Programmatic Task Creation

```python
from src.scheduling.data_structures import Task
from src.scheduling.scheduler import Scheduler

scheduler = Scheduler(db_path=":memory:")

# Create task
task = Task(
    id=1,
    name="Write report on Q3 sales",
    description="Draft sections for executive summary, analyze data from Q3_data.csv, create 5 slides",
    attached_apps=["word", "excel", "powerpoint"]
)

# Add and estimate
scheduler.add_task(task)
duration = scheduler.estimate_task_duration(task)
print(f"Estimated: {duration} minutes")

# Start task
result = scheduler.start_task(task)

# Check for distractions
distractions = scheduler.check_distractions(task)
if distractions["distractions"]:
    print(f"Watch out: {distractions['distractions']}")
    print(f"Suggestion: {distractions['suggestion']}")
```

### Distraction Detection Example

```python
from src.scheduling.feedback_loop import DistractionWatcher
from src.scheduling.data_structures import Task

task = Task(
    id=1,
    name="Code review",
    description="Review PR for feature X. Check logic, run tests, confirm documentation.",
    attached_apps=["vscode", "github"]
)

watcher = DistractionWatcher()
result = watcher.check_distractions_sync(task)

# Result format:
# {
#   "distractions": ["Firefox: youtube.com/watch?v=...", "VLC Player"],
#   "rationale": "YouTube and VLC are entertainment platforms not required for code review.",
#   "suggestion": "Close these tabs/apps or take a proper break later."
# }
```

## Features Breakdown

### 1. Task Duration Estimation

**Input:**

- Task name and description
- Professional project manager expertise prompt

**Process:**

- Gemini analyzes task complexity
- Uses few-shot examples to calibrate estimates
- Returns JSON with estimated minutes

**Output:**

- Estimated duration in minutes/hours
- Displayed in UI with human-readable format

**Accuracy Tips:**

- Provide detailed descriptions
- Include specific deliverables
- Mention any dependencies or blockers

### 2. Distraction Warning System

**Input:**

- Current task and attached applications
- List of open apps and window titles
- Gemini reasoning about relevance

**Process:**

- Gemini compares task requirements against open apps
- Identifies entertainment, social media, unrelated tools
- Ignores IDEs, terminals, browsers with documentation

**Output:**

- List of identified distractions
- Rationale for why they're distracting
- Actionable suggestions

**Distraction Categories Detected:**

- Entertainment (YouTube, Netflix, games)
- Social media (Facebook, Twitter, Reddit)
- Streaming (VLC, Spotify)
- Chat unrelated to task (Discord, Slack)
- News sites if not relevant to task

**Safe Apps (Not Flagged):**

- VS Code, IDEs
- Terminals/Command Prompt
- Documentation browsers
- Task-specific apps (Word for writing, Excel for data analysis)
- GitHub, Jira (for development tasks)

### 3. Productivity Scoring Integration

The widget integrates with `ProductivityScoring` to provide:

- Break recommendations based on focus metrics
- Personalized feedback on productivity patterns
- Real-time updates every 10 seconds

## Error Handling

### Duration Estimation Errors

If Gemini API fails:

```
UI Display: "❌ Duration estimation failed: [error details]"
Fallback: User can manually enter duration
```

### Distraction Detection Errors

If app detection fails:

```
UI Display: "❌ Distraction check failed: [error details]"
Fallback: Manual review recommended
```

### Missing Environment Variables

If `GEMINI_API_KEY` not set:

```
Error: ValueError("Set GEMINI_API_KEY environment variable")
Fix: Export API key and restart application
```

## Threading Model

The UI uses worker threads to avoid blocking:

```
Main UI Thread
    ↓
    └─→ TaskEstimationWorker (background)
        └─→ Emits duration_ready signal

    └─→ DistractionCheckWorker (background)
        └─→ Emits check_complete signal

    └─→ Update Timer (every 10s)
        └─→ Update recommendations
```

Benefits:

- Responsive UI during long operations
- Non-blocking Gemini API calls
- Smooth user experience

## Integration with Existing Modules

### With Focus Detection (`src/focus_detection/`)

- UI receives `pipeline_output` from frame processor
- Passes to `ProductivityScoring` via `add_frame_data()`
- Updates break recommendations

### With Scoring (`src/scoring/`)

- Displays productivity insights
- Shows fatigue analysis
- Provides personalized feedback

## Testing

### Unit Tests Location

```
tests/scheduling/
tests/ui/
```

### Manual Testing Checklist

- [ ] Task creation and duration estimation
- [ ] Distraction detection on running task
- [ ] Break recommendations display
- [ ] Manual duration override
- [ ] Task status transitions (due → in progress → completed)
- [ ] Error handling for API failures
- [ ] Cross-platform app detection (test on Linux/Windows/macOS)

## Troubleshooting

### Issue: "Distraction detection returns empty"

**Solution:** Ensure at least one window/tab is open in an application

### Issue: "Duration estimation times out"

**Solution:** Check `GEMINI_API_KEY`, ensure network connection, verify API quota

### Issue: "App names not recognized correctly"

**Solution:** Check `clean_app_name()` function in `open_apps.py`, add custom mappings as needed

### Issue: "UI freezes during estimation"

**Solution:** Worker threads should prevent this. Check logs for exceptions in worker.run()

## Future Enhancements

1. **Task History & Analytics**

   - Compare estimated vs. actual duration
   - Build personalized estimation models
   - Trending and productivity insights

2. **Smarter Distraction Detection**

   - ML model for context-aware relevance
   - Learning from user overrides
   - Multi-task distraction analysis

3. **Proactive Interventions**

   - Auto-block distracting apps during focus time
   - Smart notification management
   - Focus mode enforcement

4. **Integration with Calendar**

   - Schedule tasks based on available time
   - Calendar conflict detection
   - Deadline-driven prioritization

5. **Team Collaboration**
   - Shared task scheduling
   - Collaborative distraction detection
   - Team productivity metrics

## API Reference

### GeminiMCP

```python
class GeminiMCP:
    def estimate_duration(self, task_name: str, description: str) -> float:
        """Returns estimated minutes"""

    def detect_distractions(self, task: Dict[str, Any], open_items: List[str]) -> Dict[str, Any]:
        """Returns {"distractions": [...], "rationale": "...", "suggestion": "..."}"""
```

### Scheduler

```python
class Scheduler:
    def add_task(self, task: Task) -> Task
    def estimate_task_duration(self, task: Task) -> float
    def start_task(self, task: Task) -> Dict[str, Any]
    def complete_task(self, task: Task) -> Dict[str, Any]
    def suspend_task(self, task: Task) -> Dict[str, Any]
    def check_distractions(self, task: Task) -> Dict[str, Any]
    def get_task_by_id(self, task_id: int) -> Optional[Task]
    def get_all_tasks(self) -> List[Task]
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]
```

### Task Data Structure

```python
@dataclass
class Task:
    id: int
    name: str
    description: str = ""
    attached_apps: List[str] = []
    status: TaskStatus = TaskStatus.DUE
    estimated_minutes: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
```

---

**Last Updated:** November 2025
**Version:** 1.0
