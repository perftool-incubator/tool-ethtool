# tool-ethtool

Crucible tool for collecting per-queue NIC statistics via `ethtool -S` during benchmark runs.

## Key Files

| File | Purpose |
|------|---------|
| `rickshaw.json` | Rickshaw integration configuration |
| `workshop.json` | Engine image build requirements |
| `ethtool-start` | Starts the ethtool statistics collector |
| `ethtool-stop` | Stops the collector and compresses output |
| `ethtool-collect` | Collection loop that periodically samples `ethtool -S` |
| `ethtool-post-process.py` | Converts raw ethtool output into crucible metrics |
| `tool-metadata.json` | Machine-readable description and CDM-indexed status |
| `multiplex.json` | Parameter validation rules for multiplex |

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--interval` | 3 | Collection interval in seconds |
| `--interfaces` | auto-detect | Comma-separated list of interfaces to monitor |

## Metrics

Per-interface NIC statistics are collected and converted to per-second rates. Counters are automatically classified by pattern:

- **Per-queue**: `rx0_packets`, `tx3_bytes`, `rx_queue_0_packets` (breakout by direction + queue number)
- **Per-channel**: `ch0_events`, `ch5_poll` (breakout by channel number)
- **Per-priority**: `rx_prio3_packets`, `tx_prio0_bytes` (breakout by direction + priority)
- **Aggregate**: `rx_packets`, `tx_bytes` (breakout by direction)
