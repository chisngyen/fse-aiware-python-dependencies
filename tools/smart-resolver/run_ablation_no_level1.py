#!/usr/bin/env python3
"""
Run the Level 1 Off ablation study.

This script runs a single evaluation of the MEMRES system with Level 1
(Self-Evolving Session Memory) completely disabled, to measure how much
the intra-session memory contributes to the overall resolution success rate.

Usage:
    python run_ablation_no_level1.py
"""

import os
import subprocess
import time

def main():
    compose_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(compose_dir, '..', '..', 'output', 'ablation_no_level1')
    compose_file = os.path.join(compose_dir, 'docker-compose-ablation.yml')

    print("=" * 60)
    print("ABLATION STUDY: Level 1 (Session Memory) OFF")
    print("=" * 60)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Stop any existing containers
    print("Ensuring clean docker state...")
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose-ablation.yml", "down"],
        cwd=compose_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # Build and start container
    print("Building and starting ablation container...")
    start_time = time.time()
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose-ablation.yml", "up", "-d", "--build"],
        cwd=compose_dir, check=True
    )

    # Wait for completion
    print("Waiting for ablation run to complete...")
    print("(This may take 3-4 hours for ~2890 snippets)")
    print()

    while True:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", "smart-resolver"],
            capture_output=True, text=True
        )
        if result.returncode != 0 or result.stdout.strip() != 'true':
            break
        
        # Check progress
        results_csv = os.path.join(output_dir, 'results.csv')
        if os.path.exists(results_csv):
            with open(results_csv, 'r') as f:
                line_count = sum(1 for _ in f) - 1  # subtract header
            elapsed = time.time() - start_time
            print(f"\r  Progress: {line_count}/2890 snippets ({elapsed/60:.1f} min elapsed)", end='', flush=True)
        
        time.sleep(30)

    elapsed = time.time() - start_time
    print(f"\n\nAblation run completed in {elapsed/60:.1f} minutes.")

    # Check results
    results_csv = os.path.join(output_dir, 'results.csv')
    if os.path.exists(results_csv):
        import csv
        with open(results_csv, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        total = len(rows)
        passed = sum(1 for r in rows if r.get('passed') == 'True')
        print(f"\n{'=' * 60}")
        print(f"ABLATION RESULTS (Level 1 OFF)")
        print(f"{'=' * 60}")
        print(f"Total snippets: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success rate: {passed/total*100:.1f}%" if total > 0 else "N/A")
        print(f"{'=' * 60}")                                      
    else:
        print("WARNING: No results.csv found!")

    # Cleanup
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose-ablation.yml", "down"],
        cwd=compose_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

if __name__ == '__main__':
    main()
