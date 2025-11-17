#!/usr/bin/env python3
import csv
import sys
from collections import defaultdict, deque

CSV_PATH = "/tmp/focus_events.csv"

def read_rows(path):
    with open(path, newline='') as f:
        r = csv.DictReader(f)
        return list(r)


def summarize(rows):
    # Group by detection_idx (str in CSV)
    groups = defaultdict(list)
    for row in rows:
        groups[row['detection_idx']].append(row)

    for det_idx, rs in groups.items():
        print(f"\n--- Detection idx: {det_idx} | rows: {len(rs)} ---")
        prev_blink = int(rs[0].get('blink_count', 0))
        prev_pending = rs[0].get('pending_blink', 'False')
        prev_attention = rs[0].get('attention', '')
        prev_eyes_left = rs[0].get('eyes_open_left', 'False')
        prev_eyes_right = rs[0].get('eyes_open_right', 'False')

        blink_events = []
        missed_blinks = 0
        # keep a small window buffer for context
        buf = deque(maxlen=10)
        for i, r in enumerate(rs):
            buf.append(r)
            bcount = int(r.get('blink_count', 0))
            pending = r.get('pending_blink', 'False') == 'True'
            attention = r.get('attention', '')
            left_open = r.get('eyes_open_left', 'False') == 'True'
            right_open = r.get('eyes_open_right', 'False') == 'True'

            if bcount > prev_blink:
                # found increment
                print(f"Blink incremented: {prev_blink} -> {bcount} at row idx {i} (frame {r.get('frame_id')})")
                # show preceding context
                print("Context (prev rows):")
                for x in list(buf)[:-1][-6:]:
                    print(f"  frame={x.get('frame_id')} att={x.get('attention')} left_ear={x.get('left_ear')} right_ear={x.get('right_ear')} pending={x.get('pending_blink')} blink_count={x.get('blink_count')}")
                blink_events.append((i, r))
            # detect closed but never led to blink when opened
            if not prev_eyes_left and not prev_eyes_right and (left_open or right_open):
                # previous was closed, now open
                # if prev_pending was False and blink didn't increment, count as missed
                if prev_pending == 'False':
                    missed_blinks += 1
            prev_blink = bcount
            prev_pending = r.get('pending_blink', 'False')
            prev_attention = attention
            prev_eyes_left = left_open
            prev_eyes_right = right_open

        print(f"Total blink increments detected: {len(blink_events)}")
        print(f"Estimated missed blink openings (closed->open without pending): {missed_blinks}")


if __name__ == '__main__':
    try:
        rows = read_rows(CSV_PATH)
    except FileNotFoundError:
        print(f"CSV file not found: {CSV_PATH}", file=sys.stderr)
        sys.exit(2)
    if not rows:
        print("No rows found in CSV", file=sys.stderr)
        sys.exit(1)
    summarize(rows)
