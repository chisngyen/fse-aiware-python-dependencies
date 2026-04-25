#!/usr/bin/env python3
"""
CGAR — Constraint-Guided Agentic Resolution
Entry point. CLI identical to MEMRES for drop-in compatibility.
"""

import argparse
import csv
import json
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure MEMRES src is available (mounted at /memres_src in Docker)
_MEMRES_SRC = os.environ.get('MEMRES_SRC_PATH', '/memres_src')
if os.path.exists(_MEMRES_SRC) and _MEMRES_SRC not in sys.path:
    sys.path.insert(0, _MEMRES_SRC)

from src.cgar_resolver import CGARResolver
from src.enhanced_resolver_patched import EnhancedResolver


class FullCGARResolver(CGARResolver, EnhancedResolver):
    """
    Full CGAR resolver combining CGARResolver hooks with EnhancedResolver pipeline.
    MRO: FullCGARResolver → CGARResolver → EnhancedResolver
    CGARResolver.__init__ sets up CGAR components.
    EnhancedResolver.__init__ sets up MEMRES pipeline.
    """

    def __init__(self, *args, **kwargs):
        # Initialize CGAR components first
        CGARResolver.__init__(self)
        # Initialize MEMRES pipeline
        EnhancedResolver.__init__(self, *args, **kwargs)


def _write_output_yaml(gist_dir: str, result: dict, py_ver: str):
    if not py_ver:
        py_ver = '3.7'
    yaml_path = os.path.join(gist_dir, f'output_data_{py_ver}.yml')
    start_time = result.get('start_time', time.time() - result.get('duration', 0))
    end_time = start_time + result.get('duration', 0)
    modules = result.get('modules', {})
    result_type = result.get('result_type', 'None' if result.get('success') else 'Unknown')
    error = result.get('error', '')
    try:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write('---\n')
            f.write(f'python_version: {py_ver}\n')
            f.write(f'start_time: {start_time}\n')
            f.write('iterations:\n')
            f.write('  iteration_1:\n')
            f.write(f'    - python_module: {modules}\n')
            f.write(f'    - error_type: {result_type}\n')
            f.write(f'    - error: |\n')
            if error:
                for line in str(error).split('\n')[:50]:
                    f.write(f'        {line}\n')
            else:
                f.write('        No error\n')
            f.write(f'end_time: {end_time}\n')
            f.write(f'total_time: {result.get("duration", 0)}\n')
    except Exception as e:
        print(f"  Warning: failed to write YAML: {e}", flush=True)


def _make_resolver(args) -> FullCGARResolver:
    return FullCGARResolver(
        base_url=args.base,
        model=args.model,
        temp=args.temp,
        results_dir=args.data,
        logging=True,
        use_llm=not args.no_llm,
        use_level1=not getattr(args, 'no_level1', False),
        build_timeout=args.timeout,
    )


def resolve_single(args):
    resolver = _make_resolver(args)
    result = resolver.resolve(
        snippet_path=args.file,
        max_loops=args.loop,
        search_range=args.range,
    )
    print(f"\n{'='*60}")
    print(f"Result: {'SUCCESS' if result['success'] else 'FAILED'}")
    print(f"Python: {result['python_version']}")
    print(f"Modules: {json.dumps(result['modules'], indent=2)}")
    print(f"Duration: {result['duration']:.1f}s")
    if result['error']:
        print(f"Error: {result['error']}")
    print(f"{'='*60}")
    snippet_dir = os.path.dirname(args.file)
    _write_output_yaml(snippet_dir, result, result.get('python_version', '3.7'))
    return result


def _get_run_dir(output_dir: Path, resume: bool) -> Path:
    existing = sorted(
        [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith('run_')],
        key=lambda d: int(d.name.split('_')[1]) if d.name.split('_')[1].isdigit() else 0
    ) if output_dir.exists() else []
    if resume and existing:
        run_dir = existing[-1]
        print(f"Resuming in {run_dir.name}", flush=True)
    else:
        next_num = (int(existing[-1].name.split('_')[1]) + 1) if existing else 1
        run_dir = output_dir / f'run_{next_num}'
        print(f"Starting new run: {run_dir.name}", flush=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def resolve_folder(args):
    folder = Path(args.folder)
    output_dir = Path(args.output or '/output')
    output_dir.mkdir(parents=True, exist_ok=True)

    if getattr(args, 'exact_output', False):
        run_dir = output_dir
    else:
        run_dir = _get_run_dir(output_dir, args.resume or args.retry_failed)

    resolver = _make_resolver(args)
    snippets = sorted(folder.glob('*/snippet.py'))

    # Filter by gist list (file path or comma-separated IDs)
    if args.gist_list:
        if os.path.isfile(args.gist_list):
            with open(args.gist_list) as f:
                gist_ids = set(line.strip() for line in f if line.strip())
        else:
            gist_ids = set(args.gist_list.split(','))
        snippets = [s for s in snippets if s.parent.name in gist_ids]
        print(f"Filtered to {len(snippets)} specified gists", flush=True)

    if args.max_snippets > 0:
        snippets = snippets[:args.max_snippets]

    csv_path = run_dir / 'results.csv'
    csv_fields = ['name', 'file', 'result', 'python_modules', 'duration', 'passed']

    already_done = set()
    if args.resume and csv_path.exists():
        with open(csv_path, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                already_done.add(row['name'])
        snippets = [s for s in snippets if s.parent.name not in already_done]
        print(f"Resume: {len(snippets)} remaining", flush=True)

    if not already_done:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=csv_fields).writeheader()

    logs_dir = run_dir / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)

    total = len(snippets)
    workers = getattr(args, 'workers', 1) or 1
    _lock = threading.Lock()
    _counter = {'done': 0, 'success': 0}
    results = []

    def _resolve_one(snippet_path):
        snippet_id = snippet_path.parent.name
        gist_dir = str(snippet_path.parent)
        try:
            result = resolver.resolve(
                snippet_path=str(snippet_path),
                max_loops=args.loop,
                search_range=args.range,
            )
        except Exception as e:
            result = {
                'success': False, 'python_version': '', 'modules': {},
                'duration': 0, 'error': f'Exception: {e}',
                'result_type': 'Unknown', 'start_time': time.time(),
            }

        log_lines = resolver.get_logs()
        result['snippet_id'] = snippet_id
        py_ver = result.get('python_version', '') or '3.7'
        output_file = f'output_data_{py_ver}.yml'
        result_type = result.get('result_type', 'None' if result['success'] else 'Unknown')
        modules = result.get('modules', {})
        python_modules = ';'.join(sorted(modules.keys())) if isinstance(modules, dict) and modules else ''
        passed = result['success']

        _write_output_yaml(gist_dir, result, py_ver)

        with _lock:
            _counter['done'] += 1
            if passed:
                _counter['success'] += 1
            done, succ = _counter['done'], _counter['success']
            status = "SUCCESS" if passed else f"FAILED ({result_type})"
            print(f"[{done}/{total}] {snippet_id} → {status} | {succ}/{done} ({succ/done*100:.1f}%)", flush=True)

            with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                csv.DictWriter(f, fieldnames=csv_fields).writerow({
                    'name': snippet_id, 'file': output_file,
                    'result': result_type, 'python_modules': python_modules,
                    'duration': f"{result['duration']:.3f}", 'passed': str(passed),
                })

            try:
                log_path = logs_dir / f'{snippet_id}.log'
                with open(log_path, 'w', encoding='utf-8') as lf:
                    lf.write(f"Gist: {snippet_id}\nResult: {'SUCCESS' if passed else 'FAILED'}\n")
                    lf.write(f"Python: {py_ver}\nResult Type: {result_type}\n")
                    lf.write(f"Modules: {python_modules}\nDuration: {result['duration']:.3f}s\n")
                    if result.get('error'):
                        lf.write(f"Error: {result['error']}\n")
                    lf.write('='*60 + '\n')
                    for line in log_lines:
                        lf.write(line + '\n')
            except Exception:
                pass

        return result

    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_resolve_one, s): s for s in snippets}
            for future in as_completed(futures):
                results.append(future.result())
    else:
        for s in snippets:
            results.append(_resolve_one(s))

    succ = _counter['success']
    rate = f"{succ/total*100:.1f}%" if total > 0 else "N/A"
    print(f"\n{'='*60}\nFINAL: {succ}/{total} ({rate})\n{'='*60}")
    return results


def main():
    parser = argparse.ArgumentParser(description='CGAR — Constraint-Guided Agentic Resolution')
    parser.add_argument('-f', '--file')
    parser.add_argument('--folder')
    parser.add_argument('-m', '--model', default='gemma2')
    parser.add_argument('-b', '--base', default='http://host.docker.internal:11434')
    parser.add_argument('-l', '--loop', type=int, default=10)
    parser.add_argument('-r', '--range', type=int, default=0)
    parser.add_argument('-t', '--temp', type=float, default=0.7)
    parser.add_argument('-d', '--data', default='/results')
    parser.add_argument('-o', '--output', default='/output')
    parser.add_argument('--exact-output', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--no-llm', action='store_true')
    parser.add_argument('--no-level1', action='store_true')
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('-n', '--max-snippets', type=int, default=0)
    parser.add_argument('-w', '--workers', type=int, default=1)
    parser.add_argument('--gist-list', type=str, default='')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--retry-failed', action='store_true')
    args = parser.parse_args()

    if args.file:
        resolve_single(args)
    elif args.folder:
        resolve_folder(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
