"""
Recover results.csv from per-snippet log files after the CSV was wiped.

Reads each <id>.log in logs/ for the final 'Result: ...' line plus the YML in
hard-gists/<id>/output_data_X.Y.yml for python_version, modules, and total_time.
"""

import csv
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # YML parsing optional; recovery still works without it

LOGS_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/output/logs')
GISTS_DIR = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('/gists')
CSV_OUT = Path(sys.argv[3]) if len(sys.argv) > 3 else Path('/output/results.csv')

RESULT_RE = re.compile(r'^Result:\s*(\S+)', re.MULTILINE)
ERROR_RE = re.compile(r'^Result:.*?\((.+?)\)', re.MULTILINE)

rows = []
for log_path in sorted(LOGS_DIR.glob('*.log')):
    snippet_id = log_path.stem
    text = log_path.read_text(encoding='utf-8', errors='ignore')

    m = RESULT_RE.search(text)
    if not m:
        passed = 'False'
        result = 'Unknown'
    else:
        verdict = m.group(1).upper()
        passed = 'True' if verdict == 'SUCCESS' else 'False'
        em = ERROR_RE.search(text)
        result = em.group(1) if em else ('OtherPass' if passed == 'True' else 'Unknown')

    # Pull metadata from YML (latest one if multiple)
    file_name = ''
    py_modules = ''
    duration = '0'
    yml_files = sorted(
        (GISTS_DIR / snippet_id).glob('output_data_*.yml'),
        key=lambda p: p.stat().st_mtime, reverse=True
    )
    if yml_files:
        file_name = yml_files[0].name
        if yaml:
            try:
                data = yaml.safe_load(yml_files[0].read_text(encoding='utf-8'))
                duration = f"{data.get('total_time', 0):.3f}"
                iters = data.get('iterations', {})
                if iters:
                    last_iter_key = sorted(iters.keys())[-1]
                    last_iter = iters[last_iter_key]
                    for entry in last_iter:
                        if isinstance(entry, dict) and 'python_module' in entry:
                            py_modules = ';'.join(sorted(entry['python_module'].keys()))
                            break
            except Exception:
                pass

    rows.append({
        'name': snippet_id,
        'file': file_name,
        'result': result,
        'python_modules': py_modules,
        'duration': duration,
        'passed': passed,
    })

with open(CSV_OUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['name', 'file', 'result',
                                           'python_modules', 'duration', 'passed'])
    writer.writeheader()
    writer.writerows(rows)

passed = sum(1 for r in rows if r['passed'] == 'True')
print(f"Recovered {len(rows)} rows → {CSV_OUT}")
print(f"Passed: {passed}/{len(rows)} = {passed/len(rows)*100:.2f}%")
