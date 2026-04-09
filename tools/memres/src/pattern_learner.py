"""
Pattern Learner

Learns from historical PLLM results to recommend Python versions
and identify known-working module combinations.
"""

import csv
import os
from collections import Counter, defaultdict
from typing import Optional, Dict, List, Tuple


class PatternLearner:

    def __init__(self, results_dir: str = None):
        self.module_versions = defaultdict(list)
        self.module_success = defaultdict(lambda: {'success': 0, 'fail': 0})
        self.version_success = defaultdict(lambda: {'success': 0, 'fail': 0})
        self.total_success = 0
        self.total_fail = 0

        if results_dir:
            self.load_results(results_dir)

    def load_results(self, results_dir: str):
        """Load historical results from CSV files."""
        csv_dir = os.path.join(results_dir, 'csv')
        summary_file = os.path.join(csv_dir, 'summary-all-runs.csv')

        if not os.path.exists(summary_file):
            print(f"Warning: {summary_file} not found")
            return

        with open(summary_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                success = row.get('result', '') == 'OtherPass'
                python_version = row.get('file', '').replace('output_data_', '').replace('.yml', '')
                modules = row.get('python_modules', '')

                if success:
                    self.total_success += 1
                else:
                    self.total_fail += 1

                # Track version success
                self.version_success[python_version]['success' if success else 'fail'] += 1

                # Track module success
                if modules:
                    for module in modules.split(';'):
                        module = module.strip()
                        if module:
                            self.module_success[module]['success' if success else 'fail'] += 1
                            if success:
                                self.module_versions[module].append(python_version)

        total = self.total_success + self.total_fail
        if total > 0:
            print(f"Loaded {total} historical results ({self.total_success} success, {self.total_fail} fail)")

    def get_best_python_version(self, modules: List[str]) -> Optional[str]:
        """
        Recommend the best Python version based on module success history.
        """
        version_scores = Counter()

        for module in modules:
            if module in self.module_versions:
                for version in self.module_versions[module]:
                    version_scores[version] += 1

        if not version_scores:
            return None

        best_version = version_scores.most_common(1)[0][0]
        return best_version

    def get_module_success_rate(self, module: str) -> float:
        """Get historical success rate for a module."""
        stats = self.module_success.get(module, {'success': 0, 'fail': 0})
        total = stats['success'] + stats['fail']
        if total == 0:
            return 0.5  # Unknown, assume 50%
        return stats['success'] / total

    def is_likely_to_succeed(self, modules: List[str], python_version: str) -> float:
        """
        Estimate probability of success based on historical patterns.
        Returns float 0.0 to 1.0
        """
        if not modules:
            return 0.5

        scores = []
        for module in modules:
            rate = self.get_module_success_rate(module)
            scores.append(rate)

        return sum(scores) / len(scores)

    def get_stats(self) -> Dict:
        """Return summary statistics."""
        total = self.total_success + self.total_fail
        return {
            'total_tests': total,
            'success_rate': self.total_success / total if total > 0 else 0,
            'total_modules': len(self.module_success),
            'version_distribution': dict(self.version_success),
        }
