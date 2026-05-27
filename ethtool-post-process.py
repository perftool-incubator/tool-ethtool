#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path

TOOLBOX_HOME = os.environ.get("TOOLBOX_HOME")
if TOOLBOX_HOME:
    sys.path.append(str(Path(TOOLBOX_HOME) / "python"))

from toolbox.cdm_metrics import CDMMetrics
from toolbox.fileio import open_read_text_file


def process_iface(iface, log_file):
    metrics = CDMMetrics()
    curr_timestamp_ms = None
    prev_timestamp_ms = None
    curr_counts = {}
    prev_counts = {}

    try:
        fh, _ = open_read_text_file(log_file)
    except FileNotFoundError:
        print(f"ERROR: could not open {log_file}")
        return

    for line in fh:
        line = line.rstrip("\n")

        m = re.match(r'^DATE:(\d+\.\d+)$', line)
        if m:
            if curr_timestamp_ms is not None:
                prev_timestamp_ms = curr_timestamp_ms
                prev_counts = curr_counts.copy()
            curr_timestamp_ms = int(float(m.group(1)) * 1000)
            curr_counts = {}
            continue

        m = re.match(r'^\s+(rx|tx)(\d+)_packets:\s+(\d+)', line)
        if m:
            direction = m.group(1)
            queue = int(m.group(2))
            count = int(m.group(3))
            key = (direction, queue)
            curr_counts[key] = count

            if prev_timestamp_ms is not None and key in prev_counts:
                time_diff_sec = (curr_timestamp_ms - prev_timestamp_ms) / 1000
                if time_diff_sec > 0:
                    pps = (count - prev_counts[key]) / time_diff_sec
                    desc = {
                        "class": "throughput",
                        "source": "ethtool",
                        "type": "packets-sec",
                    }
                    names = {
                        "interface": iface,
                        "num": queue,
                        "direction": direction,
                    }
                    sample = {"value": pps, "end": curr_timestamp_ms}
                    metrics.log_sample("0", desc, names, sample)

    fh.close()
    metrics.finish_samples()


def main():
    data_dir = "ethtool-data"

    if not os.path.isdir(data_dir):
        print(f"ERROR: {data_dir} directory not found")
        return

    for entry in sorted(os.listdir(data_dir)):
        m = re.match(r'^(.+)\.txt(\.xz)?$', entry)
        if m:
            iface = m.group(1)
            log_file = os.path.join(data_dir, entry)
            print(f"Processing {iface} from {log_file}")
            process_iface(iface, log_file)

    print("ethtool post-processing complete")


if __name__ == "__main__":
    main()
