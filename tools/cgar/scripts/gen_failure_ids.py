#!/usr/bin/env python3
"""
Generate failure_ids.txt from a MEMRES results.csv.

Usage:
    python gen_failure_ids.py <results_csv> <output_txt> [--passed]

Arguments:
    results_csv   Path to MEMRES results.csv (e.g., results/memres_output/run_10/results.csv)
    output_txt    Output file path (e.g., output/cgar_eval/failure_ids.txt)
    --passed      If given, output passed gist IDs instead of failed ones

Example (failure cases):
    python gen_failure_ids.py results/memres_output/run_10/results.csv output/cgar_eval/failure_ids.txt

Example (passed cases, for regression):
    python gen_failure_ids.py results/memres_output/run_10/results.csv output/cgar_regression/pass_ids.txt --passed
"""

import argparse
import csv
import os
import random
import sys


def main():
    parser = argparse.ArgumentParser(description='Generate gist ID lists from MEMRES results.csv')
    parser.add_argument('results_csv', help='Path to results.csv')
    parser.add_argument('output_txt', help='Output file path')
    parser.add_argument('--passed', action='store_true',
                        help='Output passed IDs instead of failed ones')
    parser.add_argument('--sample', type=int, default=0,
                        help='If > 0, randomly sample this many IDs (for regression check)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for sampling (default: 42)')
    args = parser.parse_args()

    if not os.path.exists(args.results_csv):
        print(f"ERROR: {args.results_csv} not found", file=sys.stderr)
        sys.exit(1)

    with open(args.results_csv, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    if args.passed:
        selected = [r['name'] for r in rows if r.get('passed') == 'True']
        label = 'passed'
    else:
        selected = [r['name'] for r in rows if r.get('passed') == 'False']
        label = 'failed'

    if args.sample > 0 and args.sample < len(selected):
        random.seed(args.seed)
        selected = random.sample(selected, args.sample)
        print(f"Sampled {len(selected)} {label} gists (seed={args.seed})")
    else:
        print(f"Found {len(selected)} {label} gists")

    os.makedirs(os.path.dirname(os.path.abspath(args.output_txt)), exist_ok=True)
    with open(args.output_txt, 'w', encoding='utf-8') as f:
        for gist_id in selected:
            f.write(gist_id + '\n')

    print(f"Written to {args.output_txt}")


if __name__ == '__main__':
    main()
