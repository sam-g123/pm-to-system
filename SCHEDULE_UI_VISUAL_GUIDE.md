# Schedule UI Visual Flow & Examples

## UI Layout

```
┌────────────────────────────────────────────────────────────────┐
│  Task Scheduler with AI-Powered Insights                       │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─ Add New Task ─────────────────────────────────────────────┐ │
│ │                                                             │ │
│ │ Task Name:                                                  │ │
│ │ [Write report on Q3 sales__________________________]        │ │
│ │                                                             │ │
│ │ Task Description:                                           │ │
│ │ [Draft sections for executive summary, analyze...          │ │
│ │  data from Q3_data.csv, create 5 slides...____]            │ │
│ │                                                             │ │
│ │ Attached Applications (comma-separated):                    │ │
│ │ [word, excel, powerpoint________________]                  │ │
│ │                                                             │ │
│ │ Manual Duration Override (minutes, optional):               │ │
│ │ [_____]  ← Leave as 0 to use Gemini estimation            │ │
│ │                                                             │ │
│ │ [Add Task & Estimate Duration] ◄─ GREEN BUTTON            │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─ 📊 Task Duration Estimation ──────────────────────────────┐ │
│ │                                                             │ │
│ │ Estimated Duration: 2.5 hours (150 minutes)                │ │
│ │ [Green text, bold]                                          │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─ ⚠️  Distraction Warning System ──────────────────────────┐ │
│ │                                                             │ │
│ │ Start a task to monitor for distractions.                  │ │
│ │ Gemini will analyze your open apps and alert you to        │ │
│ │ potential focus killers.                                    │ │
│ │ [Gray/italic text]                                          │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─ ☕ Break Recommendations ─────────────────────────────────┐ │
│ │                                                             │ │
│ │ No session data yet. Start focus detection to get           │ │
│ │ recommendations.                                            │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─ 💡 Personalized Feedback ────────────────────────────────┐ │
│ │                                                             │ │
│ │ [Auto-updating feedback from productivity scoring]          │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─ 🎯 Currently Active Task ───────────────────────────────┐ │
│ │                                                             │ │
│ │ Task: Write report on Q3 sales                              │ │
│ │                                                             │ │
│ │ Description: Draft sections for executive summary,          │ │
│ │ analyze data from Q3_data.csv, create 5 slides              │ │
│ │                                                             │ │
│ │ Attached Apps: word, excel, powerpoint                      │ │
│ │                                                             │ │
│ │ Duration: 2.5 hours                                         │ │
│ │                                                             │ │
│ │ [Start Task]  [Check for Distractions]                     │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Workflow Sequence Diagrams

### Scenario 1: Task Creation & Duration Estimation

```
User                          UI                    Worker Thread              Gemini API
 │                            │                           │                        │
 ├─ Input task info ─────────>│                           │                        │
 │                            │                           │                        │
 ├─ Click "Add Task" ────────>│                           │                        │
 │                            │                           │                        │
 │                            ├─ Create Task ─────────>  │                        │
 │                            │                           │                        │
 │                            ├─ Show "⏳ Estimating..." │                        │
 │                            │                           │                        │
 │                            ├─ Start Worker ─────────>  │                        │
 │                            │                           │                        │
 │                            │ (No blocking)             ├─ estimate_duration() ->│
 │                            │                           │                        │
 │                            │                           │ (2-3 seconds)          │
 │                            │                           │<─ JSON response ──────│
 │                            │                           │                        │
 │                            │<─ duration_ready signal ──│                        │
 │                            │                           │                        │
 │<─ Display "2.5 hours" ────│                           │                        │
 │  [Green, bold]             │                           │                        │
 │                            │                           │                        │
 └─ Continue working ────────>│                           │                        │
```

### Scenario 2: Start Task & Distraction Check

```
User                          UI                    Worker Thread              Gemini API
 │                            │                           │                        │
 ├─ Click "Start Task" ─────> │                           │                        │
 │                            │                           │                        │
 │                            ├─ Update Task Status ──────┤                        │
 │                            │ (IN_PROGRESS)             │                        │
 │                            │                           │                        │
 │                            ├─ Start Distraction ──────>│                        │
 │                            │   Worker Thread           │                        │
 │                            │                           │                        │
 │                            ├─ Show "🔍 Analyzing..." │                        │
 │                            │                           │                        │
 │                            │ (No blocking)             ├─ get_open_apps() ────│
 │                            │                           │  (Linux: wmctrl)      │
 │                            │                           │                        │
 │                            │                           ├─ detect_distractions()→
 │                            │                           │                        │
 │                            │                           │ (1-2 seconds)          │
 │                            │                           │<─ JSON response ──────│
 │                            │                           │                        │
 │                            │<─ check_complete signal ──│                        │
 │                            │                           │                        │
 │ (Distractions found)       │                           │                        │
 │<─ Dialog: "⚠️ Distractions"│                           │                        │
 │  - YouTube                 │                           │                        │
 │  - VLC                      │                           │                        │
 │  [Rationale]               │                           │                        │
 │  [Suggestion]              │                           │                        │
 │                            │                           │                        │
 ├─ Click OK ────────────────>│                           │                        │
 │                            │                           │                        │
 └─ Continue working ────────>│                           │                        │
```

### Scenario 3: Manual Distraction Check (On-Demand)

```
User                          UI                    Worker Thread              Gemini API
 │                            │                           │                        │
 ├─ Click "Check for ────────>│                           │                        │
 │  Distractions"             │                           │                        │
 │                            │                           │                        │
 │                            ├─ Show "🔍 Analyzing..." │                        │
 │                            │                           │                        │
 │                            ├─ Start Worker ─────────>  │                        │
 │                            │                           │                        │
 │                            │ (No blocking)             ├─ check_distractions() →
 │                            │                           │                        │
 │                            │                           │ (1-2 seconds)          │
 │                            │                           │<─ JSON response ──────│
 │                            │                           │                        │
 │                            │<─ check_complete signal ──│                        │
 │                            │                           │                        │
 │ (No distractions)          │                           │                        │
 │<─ Display "✅ No ─────────│                           │                        │
 │  distractions detected"    │                           │                        │
 │  [Green text]              │                           │                        │
 │                            │                           │                        │
 └─ Continue working ────────>│                           │                        │
```

---

## Example Dialogs & Messages

### Success: Duration Estimated

```
┌─────────────────────────────────────────┐
│                                         │
│  📊 Task Duration Estimation            │
│                                         │
│  Estimated Duration: 2.5 hours          │
│  (150 minutes)                          │
│                                         │
│  [Green text, bold]                     │
│                                         │
└─────────────────────────────────────────┘
```

### Success: No Distractions

```
┌──────────────────────────────────────────┐
│                                          │
│  ✅ Focus Check Complete                 │
│                                          │
│  ✅ No distractions detected!            │
│                                          │
│  Rationale: Your open apps (Code,       │
│  Documentation, terminal) are all       │
│  relevant to code review tasks.         │
│                                          │
│  Tip: Keep up the good work!            │
│                                          │
│  [Green background, positive tone]      │
│                                          │
└──────────────────────────────────────────┘
```

### Warning: Distractions Detected

```
┌────────────────────────────────────────────┐
│                                            │
│  ⚠️  Focus Alert                           │
│                                            │
│  Possible distractions detected:           │
│                                            │
│  • Firefox: youtube.com/watch?v=funnycats │
│  • VLC Player                              │
│                                            │
│  📝 Reason:                                │
│  YouTube and VLC are entertainment apps   │
│  not required for report writing.         │
│                                            │
│  💡 Suggestion:                            │
│  Close these apps or take a proper break  │
│  later.                                    │
│                                            │
│  [Red/orange background, urgent tone]     │
│                                            │
│                        [  OK  ]            │
│                                            │
└────────────────────────────────────────────┘
```

### Error: Duration Estimation Failed

```
┌─────────────────────────────────────────┐
│                                         │
│  ❌ Duration Estimation Failed          │
│                                         │
│  Error: Failed to parse response from   │
│  Gemini API                             │
│                                         │
│  Fix: Check internet connection or      │
│       verify GEMINI_API_KEY             │
│                                         │
│  You can still enter duration manually: │
│  [150] minutes                          │
│                                         │
│  [Red text, error tone]                 │
│                                         │
└─────────────────────────────────────────┘
```

### Info: Task Started

```
┌──────────────────────────────────────────┐
│                                          │
│  ✅ Task Started                         │
│                                          │
│  Task: "Write report on Q3 sales"       │
│                                          │
│  Estimated time: 150 minutes             │
│                                          │
│  Good luck! Stay focused.                │
│                                          │
│                        [  OK  ]          │
│                                          │
└──────────────────────────────────────────┘
```

---

## State Transitions

### Task Status Flow

```
        ┌───────────┐
        │    DUE    │
        │ (initial) │
        └─────┬─────┘
              │
              │ start_task()
              ▼
        ┌──────────────┐
        │ IN_PROGRESS  │
        └──┬─────────┬─┘
           │         │
           │         │ suspend_task()
           │         │
           │         ▼
           │    ┌─────────────┐
           │    │  SUSPENDED  │
           │    └─────────────┘
           │
           │ complete_task()
           │
           ▼
        ┌────────────┐
        │ COMPLETED  │
        │(with stats)│
        └────────────┘
```

### UI Update Flow (Every 10 Seconds)

```
Timer Tick (10s)
      │
      ▼
┌──────────────────────┐
│ ProductivityScoring  │
│  .get_insights()     │
└──────────┬───────────┘
           │
      ┌────┴──────┬──────────┐
      │            │          │
      ▼            ▼          ▼
┌───────────┐ ┌────────┐ ┌────────┐
│  Break    │ │ Feed-  │ │Fatigue │
│  Recom.   │ │ back   │ │Analysis│
└─────┬─────┘ └───┬────┘ └───┬────┘
      │           │          │
      └───────────┴──────────┘
              │
              ▼
      ┌──────────────────┐
      │  Update UI       │
      │  Widgets         │
      │ (no blocking)    │
      └──────────────────┘
```

---

## Data Structure Examples

### Task Object (in-memory)

```python
Task(
    id=1,
    name="Write quarterly report",
    description="Compile sales data from Q3_data.csv, create executive summary, prepare 10-slide deck",
    attached_apps=["word", "excel", "powerpoint"],
    status=TaskStatus.IN_PROGRESS,
    estimated_minutes=150.0,
    created_at=2025-11-25 14:30:00,
    started_at=2025-11-25 14:35:15,
    completed_at=None
)
```

### Gemini Duration Response

```json
{
  "estimated_minutes": 150
}
```

### Gemini Distraction Response

```json
{
  "distractions": ["Firefox: youtube.com/watch?v=funnycats", "VLC Player"],
  "rationale": "YouTube and VLC are entertainment platforms not required for report writing.",
  "suggestion": "Close these apps or take a proper break later."
}
```

### Open Apps List (from `get_open_apps_and_tabs()`)

```python
[
    "Google Chrome: Gmail - Inbox",
    "Google Chrome: [YouTube] funnycats",
    "Visual Studio Code: project.py",
    "Mozilla Firefox: Google Search",
    "VLC Media Player: Video.mp4",
    "Terminal: ~/project",
    "Microsoft Word: report.docx"
]
```

### Productivity Insights (from scoring)

```python
{
    "break_recommendation": {
        "break_type_description": "Quick Eye Rest",
        "next_break_in_seconds": 45,
        "rationale": "Continuous focus time exceeded"
    },
    "personalized_feedback": [
        "Maintain current pace",
        "Blink rate is healthy",
        "Head position is good"
    ],
    "fatigue_analysis": {
        "fatigue_level": 0.32,
        "fatigue_description": "Low",
        "recommendation": "✅ Low fatigue. Keep up the good work!"
    }
}
```

---

## Keyboard Navigation (Future Enhancement)

```
Tab            → Move between fields/buttons
Shift+Tab      → Move backward between fields
Enter          → Activate focused button
Escape         → Close dialogs
Ctrl+N         → New task
Ctrl+S         → Start task
Ctrl+D         → Check distractions
Ctrl+C         → Complete task
Ctrl+Q         → Quit
```

---

## Color Scheme

| Element    | Color                   | Usage                               |
| ---------- | ----------------------- | ----------------------------------- |
| Success    | Green (#4CAF50)         | Estimated duration, no distractions |
| Warning    | Orange/Yellow (#FF9800) | Loading states                      |
| Error      | Red (#f44336)           | Errors, critical alerts             |
| Info       | Blue (#2196F3)          | General information                 |
| Background | Light Gray (#f9f9f9)    | Input sections                      |
| Border     | Light Gray (#ddd)       | Frames and sections                 |

---

## Accessibility Features

- **High Contrast**: Important text uses bold fonts
- **Clear Icons**: ✅ ⚠️ ❌ 📊 provide visual cues
- **Readable Fonts**: Default system font, size 10-12pt
- **Tooltips**: Hover over fields for help
- **Keyboard Navigation**: Tab through fields
- **Screen Reader Support**: Qt accessibility built-in

---

## Performance Indicators

The UI is designed to be responsive:

```
Action                     Time      Responsive?
─────────────────────────────────────────────────
Task creation             <100ms    ✅ Yes (immediate)
Duration estimation       2-3s      ✅ Yes (worker thread)
Distraction detection     1-2s      ✅ Yes (worker thread)
UI update                 <10ms     ✅ Yes (signal/slot)
Productivity update       <1s       ✅ Yes (async timer)
Dialog display            <50ms     ✅ Yes (native)
```

**No blocking operations** = Smooth user experience

---

**Visual Documentation Complete** ✅
