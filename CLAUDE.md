# Tool-ethtool

## Purpose
Crucible tool for collecting per-queue NIC statistics via `ethtool -S` during benchmark runs. Periodically samples ethtool counters on specified interfaces and converts them to per-second rates.

## Language
- Bash for collection scripts (`ethtool-start`, `ethtool-stop`, `ethtool-collect`)
- Python for post-processing (`ethtool-post-process.py`)

## Key Files
| File | Purpose |
|------|---------|
| `rickshaw.json` | Rickshaw integration: collector scripts, blacklist/whitelist |
| `workshop.json` | Engine image build requirements |
| `ethtool-start` | Entry point: parses `--interval` and `--interfaces`, launches `ethtool-collect` |
| `ethtool-stop` | Kills collector, compresses output with xz |
| `ethtool-collect` | Collection loop: runs `ethtool -S` per interface, writes timestamped output |
| `ethtool-post-process.py` | Parses raw output, classifies counters, computes rates, logs via CDMMetrics |

## Post-Processing
`ethtool-post-process.py` reads timestamped `ethtool -S` output from `ethtool-data/<iface>.txt[.xz]` files. For each counter, it computes the per-second rate between consecutive samples. Counters are classified by pattern into metric types with breakout dimensions (direction, queue number, priority).

## Conventions
- Primary branch is `main`
- Standard Bash modelines and 4-space indentation
- Python code follows 4-space indentation with standard modelines
