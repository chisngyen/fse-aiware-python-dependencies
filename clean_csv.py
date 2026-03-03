import csv
import sys
import os
from pathlib import Path

# Support: python clean_csv.py [run_number]
# Default: latest run folder
output_dir = Path(r'D:\fse-aiware-python-dependencies\output\ablation_no_level1')
if len(sys.argv) > 1:
    run_dir = output_dir / f'run_{sys.argv[1]}'
else:
    runs = sorted([d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith('run_')],
                  key=lambda d: int(d.name.split('_')[1]) if d.name.split('_')[1].isdigit() else 0)
    run_dir = runs[-1] if runs else output_dir

f = str(run_dir / 'results.csv')
logs_dir = run_dir / 'logs'
print(f'Cleaning: {f}')
with open(f) as fh:
    rows = list(csv.DictReader(fh))

# Remove duration=0 failures
kept = [r for r in rows if not (r['passed'] == 'False' and float(r['duration']) == 0)]
removed_unknown = len(rows) - len(kept)

# Remove entries without corresponding log file
if logs_dir.is_dir():
    before = len(kept)
    kept = [r for r in kept if (logs_dir / f"{r['name']}.log").exists()]
    removed_nolog = before - len(kept)
else:
    removed_nolog = 0

with open(f, 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=['name', 'file', 'result', 'python_modules', 'duration', 'passed'])
    w.writeheader()
    w.writerows(kept)
print(f'Removed {removed_unknown} Unknown rows, {removed_nolog} entries without logs. Kept {len(kept)} rows.')
