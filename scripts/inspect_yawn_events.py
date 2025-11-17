#!/usr/bin/env python3
"""
inspect_yawn_events.py

Summarize yawn-related events from /tmp/focus_events.csv and /tmp/focus_debug_verbose.log.

Produces a per-state (detection id) report with:
 - total rows
 - detected mouth-open starts
 - detected yawn evaluations (mouth closed after open)
 - actual yawn increments (from CSV yawn_count increases)
 - pending flags seen
 - missed yawn evaluations (eval happened but no increment)

Also prints some representative verbose-log lines (YAWN_START / YAWN_EVAL / YAWN_PENDING_CLEARED / YAWN_INC) for manual inspection.
"""
import csv
import os
import sys
import re
from collections import defaultdict

CSV_PATH = "/tmp/focus_events.csv"
VERBOSE_LOG = "/tmp/focus_debug_verbose.log"
CONCISE_LOG = "/tmp/focus_debug.log"


def read_csv_rows(path):
    with open(path, newline='') as f:
        r = csv.DictReader(f)
        return list(r)


def group_by_state(rows):
    groups = defaultdict(list)
    for r in rows:
        # detection_idx stored as int or -1
        key = r.get('detection_idx')
        groups[key].append(r)
    return groups


def analyze_group(rs):
    # rs is list of rows (dict) ordered by time
    prev_mouth = rs[0].get('mouth_open', 'False') == 'True'
    prev_pending = rs[0].get('pending_yawn', 'False') == 'True'
    prev_yawn = int(rs[0].get('yawn_count', 0))

    mouth_starts = 0
    evals = 0
    increments = 0
    pending_at_start = 0
    pending_cleared = 0
    examples = []

    # We'll also collect frame indices where events happened
    for i, r in enumerate(rs[1:], start=1):
        mouth = r.get('mouth_open', 'False') == 'True'
        pending = r.get('pending_yawn', 'False') == 'True'
        yawn = int(r.get('yawn_count', 0))

        # mouth just opened
        if (not prev_mouth) and mouth:
            mouth_starts += 1
            if pending:
                pending_at_start += 1
            examples.append((r.get('frame_id'), 'START', r.get('timestamp'), pending, r.get('mar')))

        # mouth just closed
        if prev_mouth and (not mouth):
            evals += 1
            # did increment occur at this row?
            if yawn > prev_yawn:
                increments += (yawn - prev_yawn)
                examples.append((r.get('frame_id'), 'INCREMENT', r.get('timestamp'), yawn - prev_yawn, r.get('mar')))
            else:
                examples.append((r.get('frame_id'), 'EVAL_NO_INC', r.get('timestamp'), pending, r.get('mar')))
            # If pending was False when it opened, this was a missed candidate
            if not prev_pending:
                pending_cleared += 1

        prev_mouth = mouth
        prev_pending = pending
        prev_yawn = yawn
    return {
        'rows': len(rs),
        'mouth_starts': mouth_starts,
        'evals': evals,
        'increments': increments,
        'pending_at_start': pending_at_start,
        'pending_cleared': pending_cleared,
        'examples': examples[:10]
    }


def parse_verbose_log(path):
    # collect yawn-related lines with frame and ts
    if not os.path.exists(path):
        return []
    pats = []
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            if ln.startswith('YAWN_'):
                pats.append(ln)
    return pats


def main():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found: {CSV_PATH}")
        sys.exit(2)
    rows = read_csv_rows(CSV_PATH)
    if not rows:
        print("No CSV rows")
        sys.exit(1)

    groups = group_by_state(rows)

    print(f"Found {len(groups)} state groups in {CSV_PATH}")

    overall = {
        'total_rows': len(rows),
        'total_mouth_starts': 0,
        'total_evals': 0,
        'total_increments': 0,
        'total_pending_at_start': 0,
        'total_pending_cleared': 0,
    }

    for sid, rs in sorted(groups.items(), key=lambda x: int(x[0]) if x[0].lstrip('-').isdigit() else x[0]):
        # ensure chronological order by frame_id (csv should already be ordered)
        try:
            rs_sorted = sorted(rs, key=lambda r: int(r.get('frame_id', 0)))
        except Exception:
            rs_sorted = rs
        stats = analyze_group(rs_sorted)
        overall['total_mouth_starts'] += stats['mouth_starts']
        overall['total_evals'] += stats['evals']
        overall['total_increments'] += stats['increments']
        overall['total_pending_at_start'] += stats['pending_at_start']
        overall['total_pending_cleared'] += stats['pending_cleared']

        print('\n--- State id:', sid, '| rows:', stats['rows'], '---')
        print(f"mouth_starts={stats['mouth_starts']} evals={stats['evals']} increments={stats['increments']} pending_at_start={stats['pending_at_start']} pending_cleared={stats['pending_cleared']}")
        if stats['examples']:
            print('Examples (up to 10):')
            for ex in stats['examples']:
                print(' ', ex)

    print('\n--- Overall ---')
    print(f"rows={overall['total_rows']} mouth_starts={overall['total_mouth_starts']} evals={overall['total_evals']} increments={overall['total_increments']} pending_at_start={overall['total_pending_at_start']} pending_cleared={overall['total_pending_cleared']}")

    # print last 200 lines of verbose log YAWN_* events for context
    v = parse_verbose_log(VERBOSE_LOG)
    if v:
        print('\nLast verbose yawn events:')
        for ln in v[-200:]:
            print(' ', ln)
    else:
        print('\nNo verbose yawn events found (', VERBOSE_LOG, ')')

    # print concise log increments for YAWN_INC
    if os.path.exists(CONCISE_LOG):
        print('\nYAWN increments in concise log (last 100 lines with YAWN_INC):')
        with open(CONCISE_LOG) as f:
            lines = [l.strip() for l in f if 'YAWN_INC' in l]
            for l in lines[-100:]:
                print(' ', l)
    else:
        print('\nNo concise log found (', CONCISE_LOG, ')')


if __name__ == '__main__':
    main()
