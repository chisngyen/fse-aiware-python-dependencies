"""
Convert GitChameleon dataset (final_fix_dataset.jsonl) to hard-gists folder layout
so CGAR can run on it without modification.

Each example becomes: <output_dir>/sample_<id>/snippet.py
The snippet is starting_code + solution body + test (all concatenated into a
runnable script). Version info is intentionally NOT written into the snippet —
CGAR must resolve packages from imports alone, like on HG2.9K.

A separate ground_truth.csv records the expected (python_version, library, version,
extra_dependencies) so we can score CGAR's predictions.
"""

import csv
import json
import os
import sys
from pathlib import Path


def build_snippet(row: dict) -> str:
    """Concatenate starting_code + solution + test into a runnable script."""
    starting = row.get('starting_code', '').rstrip()
    solution = row.get('solution', '').rstrip()
    test = row.get('test', '').rstrip()

    # solution is the function body (indented 4 spaces); paste under starting_code
    parts = [starting]
    if solution:
        parts.append(solution)
    parts.append("")  # blank line
    parts.append("# --- test ---")
    parts.append(test)
    return "\n".join(parts) + "\n"


def main():
    if len(sys.argv) < 3:
        print("Usage: convert_gitchameleon.py <jsonl_path> <output_dir>")
        sys.exit(1)

    jsonl_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    gt_rows = []
    count = 0
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            row = json.loads(line)
            ex_id = row['example_id']
            folder_name = f"sample_{ex_id}"
            snippet_dir = output_dir / folder_name
            snippet_dir.mkdir(exist_ok=True)

            snippet_path = snippet_dir / "snippet.py"
            snippet_path.write_text(build_snippet(row), encoding='utf-8')

            gt_rows.append({
                'gist_id': folder_name,
                'python_version': row.get('python_version', ''),
                'library': row.get('library', ''),
                'version': row.get('version', ''),
                'extra_dependencies': ' '.join(row.get('extra_dependencies', [])),
            })
            count += 1

    gt_path = output_dir / "ground_truth.csv"
    with open(gt_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['gist_id', 'python_version',
                                               'library', 'version',
                                               'extra_dependencies'])
        writer.writeheader()
        writer.writerows(gt_rows)

    print(f"Wrote {count} snippets to {output_dir}")
    print(f"Ground truth: {gt_path}")


if __name__ == '__main__':
    main()
