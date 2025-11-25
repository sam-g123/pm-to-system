# Quick Start Guide: Schedule UI with Gemini Integration

## Setup

### 1. Install Required Packages

```bash
pip install google-generativeai PyQt5 psutil pygetwindow
```

### 2. Set Environment Variable

```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

### 3. Verify Linux Prerequisites (if on Linux)

```bash
# wmctrl is required for app detection on Linux
sudo apt install wmctrl
```

## Basic Usage

### Launch the Schedule Widget

```python
from PyQt5.QtWidgets import QApplication
from src.ui.widgets.schedule_widget_new import ScheduleWidgetNew

app = QApplication([])
widget = ScheduleWidgetNew()
widget.show()
app.exec_()
```

### Add a Task

1. **Enter Task Name**: "Write quarterly report"
2. **Enter Task Description**: "Compile data from all departments, create executive summary, finalize presentation"
3. **Enter Attached Apps** (optional): "word, excel, powerpoint"
4. **Click "Add Task & Estimate Duration"**

→ Gemini AI estimates the task duration (e.g., "2.5 hours")

### Start Working on a Task

1. **Click "Start Task"**
2. **System automatically checks for distractions**
3. **If distractions found**: Warning dialog appears
   - Shows which apps are distracting
   - Explains why they're distracting
   - Suggests actions

### Monitor Focus

- **Duration Display**: Shows estimated vs. elapsed time
- **Break Recommendations**: Updated every 10 seconds based on focus metrics
- **Distraction Alerts**: Can be manually triggered with "Check for Distractions" button

## Common Scenarios

### Scenario 1: Writing a Document

```
Task: "Write blog post on Python decorators"
Description: "Introduction, basic syntax, practical examples, advanced usage, conclusion"
Attached Apps: "vscode, google-docs, browser"

Result:
- Estimated: 2 hours
- Safe Apps: VSCode, Google Docs, Browser (for research)
- Potential Distractions: YouTube, Reddit, Twitter (if open)
```

### Scenario 2: Code Review

```
Task: "Review feature PR"
Description: "Check implementation, verify tests, review docs, test locally"
Attached Apps: "vscode, github, terminal, slack"

Result:
- Estimated: 1.5 hours
- Safe Apps: VSCode, GitHub, Terminal, Slack (for code discussion)
- Potential Distractions: Social media, streaming apps, games
```

### Scenario 3: Data Analysis

```
Task: "Analyze Q3 sales data"
Description: "Load dataset, create pivot tables, generate charts, write insights"
Attached Apps: "excel, python, jupyter"

Result:
- Estimated: 3 hours
- Safe Apps: Excel, Python IDE, Jupyter
- Potential Distractions: Email, chat, news websites
```

## Troubleshooting

### "Gemini API Key not found"

```bash
# Verify environment variable
echo $GEMINI_API_KEY

# If empty, set it again
export GEMINI_API_KEY="your-key"
```

### "Duration estimation timeout"

- Check internet connection
- Verify API key is valid
- Check Gemini API quota in Google Cloud Console

### "App detection not working on Linux"

```bash
# Install wmctrl
sudo apt install wmctrl

# Verify installation
which wmctrl
```

### "Distraction detection empty on macOS/Windows"

- Ensure `pygetwindow` is installed
- Make sure at least one window is visible
- Try minimizing/maximizing windows to refresh detection

## Tips for Better Results

### Duration Estimation

- ✅ Be specific about deliverables
- ✅ Include file names, quantities, dependencies
- ✅ Mention any research or learning needed
- ❌ Avoid vague descriptions ("do stuff")
- ❌ Don't include "fix bugs" without details

### Example Good Description

```
"Write quarterly report:
- Compile sales data from Q3_data.csv
- Create charts for revenue, profit, growth
- Write executive summary (2-3 paragraphs)
- Prepare 10-slide PowerPoint presentation
- Get approval from CFO"
```

### Distraction Detection

- Keep your actual working apps open
- Close unused apps before starting
- Add commonly-needed apps to "Attached Apps" field
- Trust Gemini's judgment but override if needed

## Keyboard Shortcuts (Future)

| Shortcut | Action             |
| -------- | ------------------ |
| `Ctrl+N` | New task           |
| `Ctrl+S` | Start task         |
| `Ctrl+D` | Check distractions |
| `Ctrl+C` | Complete task      |

## Understanding the Output

### Duration Format

- Under 1 hour: "45 minutes"
- 1-8 hours: "2.5 hours"
- Full days: "1 day, 3 hours"

### Distraction Alert Example

```
⚠️ POTENTIAL DISTRACTIONS DETECTED:

• Firefox: youtube.com/watch?v=...
• VLC Player
• Discord

📝 Reason:
YouTube and VLC are entertainment platforms not required for report writing.
Discord is a communication tool that can interrupt focus.

💡 Suggestion:
Close YouTube and VLC. Mute Discord or set to "do not disturb".
```

### Break Recommendation Example

```
☕ Break Recommendations

Type: Quick Eye Rest
Recommended in: 45 seconds
Reason: Based on continuous focus time and eye strain metrics
```

## Data Stored

The widget keeps track of:

1. **Task List** (in-memory during session)

   - Task name, description, attached apps
   - Estimated and actual duration
   - Status (due, in progress, completed)
   - Timestamps

2. **Focus Metrics** (from integration with scoring module)

   - Eye closure patterns
   - Head pose stability
   - Focus continuity
   - Fatigue level

3. **Distraction History** (session-only)
   - Apps detected
   - Time of checks
   - User responses

**Note:** All data is session-based. Save important tasks externally if needed.

## Integration with Focus Detection

The Schedule Widget automatically integrates with the focus detection pipeline:

```
Focus Detection Pipeline
    ↓ (every frame)
Frame Data (eye status, head pose, etc.)
    ↓
ProductivityScoring
    ↓
ScheduleWidget.add_frame_data()
    ↓
Updated Metrics
    ↓
Updated Break Recommendations
```

To feed data from the pipeline:

```python
# In your main application
pipeline_output = focus_pipeline.process_frame(frame)
schedule_widget.add_frame_data(pipeline_output)
```

## Advanced: Programmatic Access

### Check Task Durations Without UI

```python
from src.scheduling.scheduler import Scheduler
from src.scheduling.data_structures import Task

scheduler = Scheduler(db_path=":memory:")

task = Task(
    id=1,
    name="Write report",
    description="...",
    attached_apps=["word", "excel"]
)

duration_minutes = scheduler.estimate_task_duration(task)
print(f"Task will take: {duration_minutes / 60:.1f} hours")
```

### Check Distractions Without UI

```python
result = scheduler.check_distractions(task)
for distraction in result["distractions"]:
    print(f"⚠️ {distraction}")
```

### Get Task Statistics

```python
tasks = scheduler.get_all_tasks()
completed = scheduler.get_tasks_by_status(TaskStatus.COMPLETED)

estimated_total = sum(t.estimated_minutes for t in tasks)
actual_total = sum((t.completed_at - t.started_at).total_seconds() / 60
                  for t in completed if t.completed_at)

print(f"Tasks estimated to take: {estimated_total / 60:.1f} hours")
print(f"Actually took: {actual_total / 60:.1f} hours")
```

## Privacy & Security

- **API Keys**: Never commit GEMINI_API_KEY to version control
- **Task Data**: Sent to Gemini API for analysis (you control sensitive info)
- **Open Apps**: Only analyzed by Gemini, not stored locally
- **No Tracking**: This tool doesn't track you, only helps you track yourself

## Performance

- **Duration Estimation**: ~2-3 seconds per task
- **Distraction Detection**: ~1-2 seconds per check
- **UI Responsiveness**: Background threads prevent blocking
- **API Costs**: Gemini 1.5 Flash is very cost-effective (~$0.001 per task)

---

**Questions?** Check `SCHEDULE_UI_INTEGRATION.md` for detailed documentation.
