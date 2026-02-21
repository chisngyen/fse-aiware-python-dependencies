#!/usr/bin/env python3
"""
Smart Resolver - Entry point

Usage:
    # Resolve single file
    python run.py -f /gists/0a2ac74d800a2eff9540/snippet.py -m gemma2

    # Resolve entire folder
    python run.py --folder /gists -m gemma2 -l 10

    # With historical data
    python run.py -f /gists/0a2ac74d800a2eff9540/snippet.py -m gemma2 -d /results
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

from src.enhanced_resolver import EnhancedResolver


def resolve_single(args):
    """Resolve a single snippet file."""
    resolver = EnhancedResolver(
        base_url=args.base,
        model=args.model,
        temp=args.temp,
        results_dir=args.data,
        logging=True,
        use_llm=not args.no_llm,
        build_timeout=args.timeout,
    )

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

    return result


def _load_conf_ids(results_dir: str, nonzero: bool = False) -> set:
    """Load gist IDs filtered by confidence from PLLM results.
    
    Args:
        results_dir: Path to results directory
        nonzero: If False, return conf=0 (passed==0). If True, return conf>0 (passed>0).
    """
    import glob
    ids = set()
    csv_pattern = os.path.join(results_dir, 'csv', 'summary-all-runs.csv')
    matches = glob.glob(csv_pattern)
    if not matches:
        # Try alternative path
        csv_pattern = os.path.join(results_dir, 'pllm_results', 'csv', 'summary-all-runs.csv')
        matches = glob.glob(csv_pattern)
    for csv_file in matches:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    passed = int(row.get('passed', 0))
                    if nonzero and passed > 0:
                        ids.add(row['name'])
                    elif not nonzero and passed == 0:
                        ids.add(row['name'])
                except (ValueError, KeyError):
                    pass
    label = "conf>0" if nonzero else "conf=0"
    print(f"Loaded {len(ids)} {label} gist IDs", flush=True)
    return ids


def resolve_folder(args):
    """Resolve all snippet files in a folder."""
    folder = Path(args.folder)
    output_dir = Path(args.output or '/output')
    output_dir.mkdir(parents=True, exist_ok=True)

    resolver = EnhancedResolver(
        base_url=args.base,
        model=args.model,
        temp=args.temp,
        results_dir=args.data,
        logging=True,
        use_llm=not args.no_llm,
        build_timeout=args.timeout,
    )

    # Find all snippet.py files
    snippets = sorted(folder.glob('*/snippet.py'))
    
    # Filter by confidence level
    if args.conf0_only and args.data:
        conf_ids = _load_conf_ids(args.data, nonzero=False)
        if conf_ids:
            snippets = [s for s in snippets if s.parent.name in conf_ids]
            print(f"Filtered to {len(snippets)} conf=0 snippets", flush=True)
    elif args.conf_nonzero and args.data:
        conf_ids = _load_conf_ids(args.data, nonzero=True)
        if conf_ids:
            snippets = [s for s in snippets if s.parent.name in conf_ids]
            print(f"Filtered to {len(snippets)} conf>0 snippets", flush=True)
    
    # Filter to specific gist list
    if args.gist_list:
        gist_ids = set(args.gist_list.split(','))
        snippets = [s for s in snippets if s.parent.name in gist_ids]
        print(f"Filtered to {len(snippets)} specified gists", flush=True)
    
    if args.max_snippets > 0:
        snippets = snippets[:args.max_snippets]

    # Prepare incremental CSV output
    csv_path = output_dir / 'results.csv'
    json_path = output_dir / 'results.json'
    csv_fields = ['snippet_id', 'success', 'python_version', 'modules', 'duration', 'error']

    # Resume support: load already-processed snippet IDs
    already_done = set()
    failed_ids = set()
    if (args.resume or args.retry_failed) and csv_path.exists():
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    already_done.add(row['snippet_id'])
                    if row.get('success') == 'False':
                        failed_ids.add(row['snippet_id'])
            print(f"Resume: found {len(already_done)} already-processed snippets ({len(failed_ids)} failed)", flush=True)
        except Exception as e:
            print(f"Resume: failed to read existing CSV ({e}), starting fresh", flush=True)
            already_done = set()
            failed_ids = set()

    if args.retry_failed and failed_ids:
        # Only re-run previously failed snippets
        snippets = [s for s in snippets if s.parent.name in failed_ids]
        print(f"Retry-failed: {len(snippets)} failed snippets to retry", flush=True)
        # Remove failed entries from CSV so they can be re-written
        if csv_path.exists():
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                kept_rows = [row for row in reader if row['snippet_id'] not in failed_ids]
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=csv_fields)
                writer.writeheader()
                writer.writerows(kept_rows)
            print(f"Retry-failed: kept {len(kept_rows)} successful entries in CSV", flush=True)
    elif already_done:
        snippets = [s for s in snippets if s.parent.name not in already_done]
        print(f"Resume: {len(snippets)} snippets remaining", flush=True)
    
    total = len(snippets)
    success_count = 0
    results = []
    workers = getattr(args, 'workers', 1) or 1

    print(f"Found {total} snippets to resolve (workers={workers})", flush=True)
    print(f"{'='*60}", flush=True)

    # Write CSV header only if starting fresh (no resume, no retry)
    if not already_done and not args.retry_failed:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=csv_fields)
            writer.writeheader()

    # Thread-safe write lock and counters
    _lock = threading.Lock()
    _counter = {'done': 0, 'success': 0}

    def _resolve_one(snippet_path):
        """Resolve a single snippet (called from worker thread)."""
        snippet_id = snippet_path.parent.name
        try:
            result = resolver.resolve(
                snippet_path=str(snippet_path),
                max_loops=args.loop,
                search_range=args.range,
            )
        except Exception as e:
            result = {
                'success': False,
                'python_version': '',
                'modules': {},
                'duration': 0,
                'error': f'Exception: {e}',
            }
        result['snippet_id'] = snippet_id

        with _lock:
            _counter['done'] += 1
            if result['success']:
                _counter['success'] += 1
            done = _counter['done']
            succ = _counter['success']

            # Print progress
            status = f"SUCCESS (Python {result['python_version']})" if result['success'] else f"FAILED ({result['error']})"
            print(f"[{done}/{total}] {snippet_id} -> {status}  |  Running: {succ}/{done} ({succ/done*100:.1f}%)", flush=True)

            # Incremental CSV write
            with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=csv_fields)
                writer.writerow({
                    'snippet_id': snippet_id,
                    'success': result['success'],
                    'python_version': result['python_version'],
                    'modules': json.dumps(result['modules']),
                    'duration': f"{result['duration']:.1f}",
                    'error': result['error'],
                })

        return result

    # Execute with thread pool
    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_resolve_one, s): s for s in snippets}
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    snippet_path = futures[future]
                    print(f"  Worker exception for {snippet_path.parent.name}: {e}", flush=True)
    else:
        for snippet_path in snippets:
            result = _resolve_one(snippet_path)
            results.append(result)

    success_count = _counter['success']

    # Write final JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    # Write final summary
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS")
    print(f"Total: {total}")
    print(f"Success: {success_count}")
    print(f"Failed: {total - success_count}")
    print(f"Success Rate: {success_count/total*100:.1f}%" if total > 0 else "N/A")
    print(f"{'='*60}")
    print(f"\nResults saved to: {csv_path}")
    print(f"Full results saved to: {json_path}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Smart Resolver - Enhanced Python Dependency Resolution'
    )
    parser.add_argument('-f', '--file', help='Path to single Python snippet')
    parser.add_argument('--folder', help='Path to folder containing snippets')
    parser.add_argument('-m', '--model', default='gemma2', help='Ollama model name')
    parser.add_argument('-b', '--base', default='http://host.docker.internal:11434',
                       help='Ollama base URL')
    parser.add_argument('-l', '--loop', type=int, default=10, help='Max resolution loops')
    parser.add_argument('-r', '--range', type=int, default=0, help='Python version search range')
    parser.add_argument('-t', '--temp', type=float, default=0.7, help='Model temperature')
    parser.add_argument('-d', '--data', default='/results',
                       help='Path to historical results directory (contains pllm_results/)')
    parser.add_argument('-o', '--output', default='/output',
                       help='Output directory for results')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('--no-llm', action='store_true', help='Disable LLM calls (faster)')
    parser.add_argument('--timeout', type=int, default=180, help='Docker build timeout (seconds)')
    parser.add_argument('-n', '--max-snippets', type=int, default=0,
                       help='Max snippets to process (0=all)')
    parser.add_argument('-w', '--workers', type=int, default=1,
                       help='Number of parallel workers (default: 1)')
    parser.add_argument('--conf0-only', action='store_true',
                       help='Only test conf=0 snippets (PLLM failures)')
    parser.add_argument('--conf-nonzero', action='store_true',
                       help='Only test conf>0 snippets (PLLM successes)')
    parser.add_argument('--gist-list', type=str, default='',
                       help='Comma-separated gist IDs to test')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from existing results.csv (skip already-processed)')
    parser.add_argument('--retry-failed', action='store_true',
                       help='Re-run only previously failed snippets from results.csv')

    args = parser.parse_args()

    if args.file:
        resolve_single(args)
    elif args.folder:
        resolve_folder(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
