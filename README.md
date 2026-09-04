# NOC Roster Generator

Python roster generator that implements the rules in the master specification document:

- `NOC_Roster_Master_Specification_v2.0.md`

It uses Google OR-Tools CP-SAT to generate a full-year base roster from 2026-08-01 to 2027-07-31.

## Features

- Hard constraints fully enforced from specification sections on:
  - Daily assignment and staffing counts
  - Group A/B operational pairing
  - Standby split by group
  - Maximum 3 consecutive nights
  - Night-to-morning prohibition
  - Exactly 219 operational shifts per employee
  - Designated weekend owner rotation and full weekend off assignment
  - Ten-week weekend ownership limit
- Soft-constraint optimization objective stack aligned to the defined optimization hierarchy
- Full validation pass (hard + soft)
- Workbook generation with required sheets
- Cover model utility for post-generation leave/sickness support

## Quick Start

1. Create environment and install dependencies.
2. Run generation.

```bash
pip install -r requirements.txt
python -m noc_roster.cli generate --output outputs/NOC_Roster_2026_2027.xlsx --time-limit 120
```

## CLI

Generate roster:

```bash
python -m noc_roster.cli generate --output outputs/NOC_Roster_2026_2027.xlsx --time-limit 120
```

For long runs, enable visible solver progress:

```bash
python -m noc_roster.cli generate \
  --output outputs/NOC_Roster_2026_2027.xlsx \
  --time-limit 600 \
  --progress \
  --progress-interval 10
```

Progress output includes:

- Whether a feasible solution has been found
- Current objective and best bound
- Fairness Index and rating
- Roster Quality Score and rating
- Hard-constraint pass status and violation count

In progress mode, you can stop early by pressing `q` then Enter.

For deeper troubleshooting, include native CP-SAT search logs:

```bash
python -m noc_roster.cli generate \
  --time-limit 600 \
  --progress \
  --cp-sat-logs
```

Stop immediately on first feasible solution:

```bash
python -m noc_roster.cli generate \
  --time-limit 600 \
  --progress \
  --stop-on-first-feasible
```

Validate a previously exported CSV:

```bash
python -m noc_roster.cli validate --csv outputs/roster_assignments.csv
```

## Output

Generation writes:

- Workbook at the path given with `--output`
- Assignment CSV at `outputs/roster_assignments.csv`

## Notes

- The base roster excludes dynamic cover events by design.
- Cover shifts are handled by the cover model helper and recorded separately.
