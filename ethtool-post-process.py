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


def classify_counter(counter_name):
    """Classify an ethtool -S counter name into type and breakout names.

    Returns (metric_type, names_dict) where names_dict contains
    breakout dimensions like direction, num, etc.
    """
    # Per-queue: rx0_packets, tx3_bytes, rx12_csum_none, etc.
    m = re.match(r'^(rx|tx)(\d+)_(.+)$', counter_name)
    if m:
        return (
            f"{m.group(3)}-sec",
            {"direction": m.group(1), "num": int(m.group(2))},
        )

    # Per-channel: ch0_events, ch5_poll, etc.
    m = re.match(r'^ch(\d+)_(.+)$', counter_name)
    if m:
        return (
            f"ch_{m.group(2)}-sec",
            {"num": int(m.group(1))},
        )

    # Per-priority with direction: rx_prio3_packets, tx_prio0_bytes, etc.
    m = re.match(r'^(rx|tx)_prio(\d+)_(.+)$', counter_name)
    if m:
        return (
            f"prio_{m.group(3)}-sec",
            {"direction": m.group(1), "num": int(m.group(2))},
        )

    # Aggregate with direction: rx_packets, tx_bytes, rx_vport_unicast_packets, etc.
    m = re.match(r'^(rx|tx)_(.+)$', counter_name)
    if m:
        return (
            f"{m.group(2)}-sec",
            {"direction": m.group(1)},
        )

    # Channel aggregate: ch_events, ch_poll, etc.
    m = re.match(r'^ch_(.+)$', counter_name)
    if m:
        return (f"ch_{m.group(1)}-sec", {})

    # Everything else: no direction, no queue
    return (f"{counter_name}-sec", {})


def process_iface(iface, log_file, file_id):
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

        if "NIC statistics:" in line:
            continue

        m = re.match(r'^\s+(\S+):\s+(\d+)$', line)
        if not m:
            continue

        counter_name = m.group(1)
        count = int(m.group(2))
        curr_counts[counter_name] = count

        if prev_timestamp_ms is None or counter_name not in prev_counts:
            continue

        time_diff_sec = (curr_timestamp_ms - prev_timestamp_ms) / 1000
        if time_diff_sec <= 0:
            continue

        rate = (count - prev_counts[counter_name]) / time_diff_sec

        metric_type, extra_names = classify_counter(counter_name)

        desc = {
            "class": "throughput",
            "source": "ethtool",
            "type": metric_type,
        }
        names = {"interface": iface}
        names.update(extra_names)

        sample = {"value": rate, "end": curr_timestamp_ms}
        metrics.log_sample(file_id, desc, names, sample)

    fh.close()
    metrics.finish_samples()


def main():
    data_dir = "ethtool-data"

    if not os.path.isdir(data_dir):
        print(f"ERROR: {data_dir} directory not found")
        return

    file_idx = 0
    for entry in sorted(os.listdir(data_dir)):
        m = re.match(r'^(.+)\.txt(\.xz)?$', entry)
        if m:
            iface = m.group(1)
            log_file = os.path.join(data_dir, entry)
            print(f"Processing {iface} from {log_file} (file_id={file_idx})")
            process_iface(iface, log_file, str(file_idx))
            file_idx += 1

    print("ethtool post-processing complete")


if __name__ == "__main__":
    main()
