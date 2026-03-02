"""
Enhanced log analyzer for MEMRES - Reviewer 1 requested statistics.
Extracts: root-cause breakdown, per-level timing, LLM call distribution.
"""
import os, glob, re, statistics

def parse_log(path):
    """Parse a single log file and return structured data."""
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    info = {
        'gist': '', 'result': '', 'python': '', 'result_type': '',
        'modules': '', 'duration': 0.0, 'error': '',
        # Resolution pathway
        'oracle_hit': False, 'oracle_success': False,
        'shortcut_hit': False, 'shortcut_success': False,
        'llm_called': False, 'py2_skip': False,
        'runtime_pass': False,
        # Root cause (for failures)
        'root_cause': '',
        # System deps
        'apt_installed': False,
        # Timing
        'timestamps': [],
    }
    
    lines = content.split('\n')
    # Parse header
    for line in lines[:10]:
        if line.startswith('Gist: '): info['gist'] = line[6:].strip()
        elif line.startswith('Result: '): info['result'] = line[8:].strip()
        elif line.startswith('Python: '): info['python'] = line[8:].strip()
        elif line.startswith('Result Type: '): info['result_type'] = line[13:].strip()
        elif line.startswith('Modules: '): info['modules'] = line[9:].strip()
        elif line.startswith('Duration: '): 
            try: info['duration'] = float(line[10:].strip().rstrip('s'))
            except: pass
        elif line.startswith('Error: '): info['error'] = line[7:].strip()
    
    # Parse body for markers
    if 'Oracle HIT' in content or 'Oracle SUCCESS' in content:
        info['oracle_hit'] = True
    if 'Oracle SUCCESS!' in content or 'Oracle RUNTIME PASS' in content:
        info['oracle_success'] = True
    if 'SHORTCUT SUCCESS!' in content or 'SHORTCUT RUNTIME PASS' in content:
        info['shortcut_success'] = True
    if 'Calling LLM evaluate_file' in content:
        info['llm_called'] = True
    if 'Skipping LLM: Python 2' in content:
        info['py2_skip'] = True
    if 'RUNTIME PASS' in content:
        info['runtime_pass'] = True
    if 'apt-get install' in content:
        info['apt_installed'] = True
    
    # Root cause classification (for failures)
    if info['result'] == 'FAILED':
        if 'SyntaxError' in info['result_type'] or 'SyntaxError' in info['error']:
            info['root_cause'] = 'SyntaxError'
        elif 'Timeout' in info['error'] or 'Build Timeout' in content:
            info['root_cause'] = 'Timeout'
        elif 'is heavy and failed' in content or 'marking as unfixable' in content:
            info['root_cause'] = 'Build/C-extension'
        elif info['result_type'] == 'ImportError':
            if 'system-only' in content:
                info['root_cause'] = 'System/Platform'
            else:
                info['root_cause'] = 'ImportError'
        elif 'NonZeroCode' in info['result_type'] or 'NonZeroCode' in content:
            info['root_cause'] = 'Build/C-extension'
        else:
            info['root_cause'] = 'Other'
    
    return info

def main():
    log_dir = r"D:\fse-aiware-python-dependencies\output\run_1\logs"
    logs = []
    for path in glob.glob(os.path.join(log_dir, "*.log")):
        logs.append(parse_log(path))
    
    total = len(logs)
    successes = [l for l in logs if l['result'] == 'SUCCESS']
    failures = [l for l in logs if l['result'] == 'FAILED']
    
    print(f"=" * 60)
    print(f"MEMRES Log Analysis (run_1, {total} snippets)")
    print(f"=" * 60)
    print(f"Success: {len(successes)} ({len(successes)/total*100:.1f}%)")
    print(f"Failed:  {len(failures)} ({len(failures)/total*100:.1f}%)")
    
    # === 1. Resolution Pathway Breakdown (Successes) ===
    print(f"\n{'='*60}")
    print(f"1. RESOLUTION PATHWAY (Successes only)")
    print(f"{'='*60}")
    
    oracle_only = [s for s in successes if s['oracle_success'] and not s['llm_called']]
    shortcut_only = [s for s in successes if s['shortcut_success'] and not s['llm_called']]
    py2_deterministic = [s for s in successes if s['py2_skip'] and not s['llm_called'] and not s['oracle_success'] and not s['shortcut_success']]
    llm_resolved = [s for s in successes if s['llm_called']]
    other_deterministic = [s for s in successes if not s['oracle_success'] and not s['shortcut_success'] and not s['llm_called'] and not s['py2_skip']]
    
    pathways = {
        'Oracle/Session Memory (Level 1)': oracle_only,
        'Shortcut/Self-Evolving Memory': shortcut_only,
        'Python 2 Heuristic (No LLM)': py2_deterministic,
        'Other Deterministic (Levels 2-5)': other_deterministic,
        'LLM Fallback (Level 6)': llm_resolved,
    }
    
    for name, items in pathways.items():
        pct = len(items) / len(successes) * 100 if successes else 0
        print(f"  {name}: {len(items)} ({pct:.1f}%)")
    
    # === 2. Root Cause Breakdown (Failures) ===
    print(f"\n{'='*60}")
    print(f"2. ROOT CAUSE BREAKDOWN (Failures only)")
    print(f"{'='*60}")
    
    causes = {}
    for f in failures:
        rc = f['root_cause'] or 'Unknown'
        causes[rc] = causes.get(rc, 0) + 1
    
    for cause, count in sorted(causes.items(), key=lambda x: -x[1]):
        pct = count / len(failures) * 100 if failures else 0
        print(f"  {cause}: {count} ({pct:.1f}%)")
    
    # === 3. Timing Statistics ===
    print(f"\n{'='*60}")
    print(f"3. TIMING STATISTICS (seconds)")
    print(f"{'='*60}")
    
    for label, group in [("All", logs), ("Successes", successes), ("Failures", failures)]:
        durations = [l['duration'] for l in group if l['duration'] > 0]
        if durations:
            med = statistics.median(durations)
            p90 = sorted(durations)[int(len(durations)*0.9)]
            p99 = sorted(durations)[min(int(len(durations)*0.99), len(durations)-1)]
            avg = statistics.mean(durations)
            print(f"  {label}: mean={avg:.1f}s, median={med:.1f}s, p90={p90:.1f}s, p99={p99:.1f}s (n={len(durations)})")
    
    # Per-pathway timing
    print(f"\n  --- Per Pathway ---")
    for name, items in pathways.items():
        durations = [l['duration'] for l in items if l['duration'] > 0]
        if durations:
            med = statistics.median(durations)
            avg = statistics.mean(durations)
            p90 = sorted(durations)[int(len(durations)*0.9)]
            print(f"  {name}: mean={avg:.1f}s, median={med:.1f}s, p90={p90:.1f}s (n={len(durations)})")
    
    # === 4. LLM Call Statistics ===
    print(f"\n{'='*60}")
    print(f"4. LLM CALL STATISTICS")
    print(f"{'='*60}")
    
    llm_total = sum(1 for l in logs if l['llm_called'])
    llm_success = sum(1 for l in successes if l['llm_called'])
    llm_fail = sum(1 for l in failures if l['llm_called'])
    no_llm_success = sum(1 for l in successes if not l['llm_called'])
    
    print(f"  Total snippets with LLM call: {llm_total} ({llm_total/total*100:.1f}%)")
    print(f"  LLM called → Success: {llm_success}")
    print(f"  LLM called → Failed: {llm_fail}")
    print(f"  No LLM → Success: {no_llm_success} ({no_llm_success/len(successes)*100:.1f}% of successes)")
    print(f"  LLM calls per snippet (avg): {llm_total/total:.2f}")
    
    # === 5. System Dependency Stats ===
    print(f"\n{'='*60}")
    print(f"5. SYSTEM DEPENDENCY (apt-get) STATS")
    print(f"{'='*60}")
    
    apt_total = sum(1 for l in logs if l['apt_installed'])
    apt_success = sum(1 for l in successes if l['apt_installed'])
    print(f"  Snippets with apt-get injection: {apt_total}")
    print(f"  Of which succeeded: {apt_success}")
    
    # === 6. Python Version Distribution ===
    print(f"\n{'='*60}")
    print(f"6. PYTHON VERSION DISTRIBUTION")
    print(f"{'='*60}")
    
    py_versions = {}
    for l in successes:
        v = l['python'] or 'Unknown'
        py_versions[v] = py_versions.get(v, 0) + 1
    for v, c in sorted(py_versions.items(), key=lambda x: -x[1]):
        print(f"  Python {v}: {c} ({c/len(successes)*100:.1f}%)")

if __name__ == '__main__':
    main()
