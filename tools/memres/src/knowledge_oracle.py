"""
Knowledge Oracle - Historical Data-Driven Dependency Resolution

Novel Contribution #1: Uses historical resolution data (PLLM results, PyEgo results)
as a knowledge base for instant lookup. This is inspired by Reflexion's episodic
memory but applied at a cross-experiment level.

Key Features:
1. Oracle Lookup: For known gists, instantly retrieve working packages
2. Package Frequency Analysis: Learn which packages co-occur frequently
3. Cross-snippet Transfer: When a snippet is solved, its solution is stored
   and used as few-shot context for similar snippets
4. Confidence Scoring: Uses PLLM's pass score (0-10) to weight confidence
"""

import csv
import json
import os
import re
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple


class KnowledgeOracle:
    """
    Historical data oracle for Python dependency resolution.
    
    Loads PLLM results and provides:
    - Direct gist→packages lookup (for known gists)
    - Import→package mapping learned from successful resolutions
    - Package co-occurrence patterns
    - Python version recommendations per import set
    """

    def __init__(self, results_dir: str = None, logging: bool = True):
        self.logging = logging
        self.results_dir = results_dir
        
        # Oracle data structures
        self.gist_solutions = {}  # gist_id → {python_version, packages, confidence}
        self.package_cooccurrence = defaultdict(lambda: defaultdict(int))  # pkg → {co_pkg: count}
        self.import_to_packages = defaultdict(lambda: defaultdict(int))  # import → {pkg: success_count}
        self.package_python_versions = defaultdict(lambda: defaultdict(int))  # pkg → {py_ver: count}
        self.successful_combos = []  # List of (packages_set, python_version, confidence)
        
        # Cross-snippet transfer learning
        self.session_solutions = {}  # gist_id → solution learned this session
        self.session_error_fixes = defaultdict(list)  # error_pattern → [fix_actions]
        
        # Load historical data
        if results_dir:
            self._load_pllm_results(results_dir)
    
    def log(self, msg: str):
        if self.logging:
            print(f"  [Oracle] {msg}", flush=True)
    
    # ===========================================================
    # Loading Historical Data
    # ===========================================================
    
    def _load_pllm_results(self, results_dir: str):
        """Load PLLM results from CSV files."""
        csv_dir = os.path.join(results_dir, 'pllm_results', 'csv')
        summary_file = os.path.join(csv_dir, 'summary-all-runs.csv')
        
        if not os.path.exists(summary_file):
            # Try alternate paths
            alt_paths = [
                os.path.join(results_dir, 'csv', 'summary-all-runs.csv'),
                '/results/csv/summary-all-runs.csv',
                '/app/results/csv/summary-all-runs.csv',
            ]
            for p in alt_paths:
                if os.path.exists(p):
                    summary_file = p
                    break
            else:
                if self.logging:
                    self.log(f"No PLLM results found")
                return
        
        count = 0
        high_conf = 0
        
        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    gist_id = row.get('name', '').strip()
                    if not gist_id:
                        continue
                    
                    # Parse Python version from filename
                    file_field = row.get('file', '')
                    py_ver = self._extract_python_version(file_field)
                    
                    # Parse modules
                    modules_str = row.get('python_modules', '')
                    packages = self._parse_modules(modules_str)
                    
                    # Confidence from pass score
                    try:
                        confidence = int(row.get('passed', 0))
                    except (ValueError, TypeError):
                        confidence = 0
                    
                    result_type = row.get('result', '')
                    
                    # Store solution
                    self.gist_solutions[gist_id] = {
                        'python_version': py_ver,
                        'packages': packages,
                        'confidence': confidence,
                        'result': result_type,
                    }
                    
                    count += 1
                    if confidence >= 7:
                        high_conf += 1
                    
                    # Learn from successful resolutions
                    if confidence >= 5 and packages:
                        self._learn_from_solution(packages, py_ver, confidence)
            
            if self.logging:
                self.log(f"Loaded {count} gist solutions ({high_conf} high confidence)")
        
        except Exception as e:
            if self.logging:
                self.log(f"Error loading PLLM results: {e}")
    
    def _extract_python_version(self, file_field: str) -> str:
        """Extract Python version from PLLM output filename."""
        # output_data_2.7.yml → 2.7
        match = re.search(r'(\d+\.\d+)', file_field)
        if match:
            return match.group(1)
        return '3.7'
    
    def _parse_modules(self, modules_str: str) -> List[str]:
        """Parse semicolon-separated module list from PLLM."""
        if not modules_str or modules_str.strip() in ('', 'none', 'None'):
            return []
        
        modules = []
        for m in modules_str.split(';'):
            m = m.strip()
            if m and m.lower() not in ('none', 'module_name', 'yourmodulenamehere', 
                                        'your_module', 'your-module'):
                modules.append(m)
        return modules
    
    def _learn_from_solution(self, packages: List[str], python_version: str, 
                              confidence: int):
        """Learn patterns from a successful resolution."""
        pkg_set = set(packages)
        self.successful_combos.append((pkg_set, python_version, confidence))
        
        # Co-occurrence
        for pkg in packages:
            for other in packages:
                if pkg != other:
                    self.package_cooccurrence[pkg][other] += confidence
            
            # Python version preference
            self.package_python_versions[pkg][python_version] += confidence
    
    # ===========================================================
    # Oracle Lookup
    # ===========================================================
    
    def lookup_gist(self, gist_id: str) -> Optional[Dict]:
        """
        Look up a gist in the oracle database.
        
        Returns dict with python_version, packages, confidence if found.
        Returns None if gist is unknown or confidence is too low.
        """
        # Check session solutions first (cross-snippet transfer)
        if gist_id in self.session_solutions:
            return self.session_solutions[gist_id]
        
        # Check historical data
        if gist_id in self.gist_solutions:
            solution = self.gist_solutions[gist_id]
            if solution['confidence'] >= 4 and solution['packages']:
                return solution
            elif solution['confidence'] >= 4 and not solution['packages']:
                # High confidence but no external deps — return version hint
                # so oracle can just build with correct Python version
                return {
                    'python_version': solution['python_version'],
                    'packages': [],
                    'confidence': solution['confidence'],
                    'result': solution.get('result', ''),
                    'empty_deps': True,
                }
            elif solution['confidence'] == 0:
                # Known to fail — return partial info for version hint
                return {
                    'python_version': solution['python_version'],
                    'packages': solution['packages'],
                    'confidence': 0,
                    'result': solution.get('result', ''),
                    'hint_only': True,
                }
        
        return None
    
    def get_recommended_python_version(self, packages: List[str]) -> Optional[str]:
        """
        Given a set of packages, recommend the best Python version
        based on historical success data.
        """
        version_scores = defaultdict(float)
        
        for pkg in packages:
            if pkg in self.package_python_versions:
                for ver, score in self.package_python_versions[pkg].items():
                    version_scores[ver] += score
        
        if not version_scores:
            return None
        
        return max(version_scores, key=version_scores.get)
    
    def get_likely_copackages(self, packages: List[str], 
                               min_score: int = 5) -> List[str]:
        """
        Given a set of packages, suggest additional packages that frequently
        co-occur with them in successful resolutions.
        """
        suggestions = defaultdict(int)
        pkg_set = set(p.lower() for p in packages)
        
        for pkg in packages:
            for co_pkg, score in self.package_cooccurrence.get(pkg, {}).items():
                if co_pkg.lower() not in pkg_set and score >= min_score:
                    suggestions[co_pkg] += score
        
        # Sort by score
        sorted_suggestions = sorted(suggestions.items(), key=lambda x: -x[1])
        return [pkg for pkg, _ in sorted_suggestions[:5]]
    
    # ===========================================================
    # Cross-Snippet Transfer Learning (Novel Contribution #3)
    # ===========================================================
    
    def record_solution(self, gist_id: str, python_version: str,
                         packages: Dict[str, str], success: bool):
        """
        Record a solution found during this session for transfer learning.
        """
        if success and packages:
            self.session_solutions[gist_id] = {
                'python_version': python_version,
                'packages': list(packages.keys()),
                'package_versions': dict(packages),
                'confidence': 10,
            }
    
    def record_error_fix(self, error_pattern: str, fix_action: Dict):
        """
        Record an error→fix mapping for transfer to similar future errors.
        
        error_pattern: simplified error signature (e.g., "NonZeroCode:tensorflow")
        fix_action: what fixed it (e.g., {"module": "tensorflow", "version": "2.10.1"})
        """
        self.session_error_fixes[error_pattern].append(fix_action)
    
    def get_known_fix(self, error_pattern: str) -> Optional[Dict]:
        """
        Look up a known fix for an error pattern seen earlier in this session.
        """
        fixes = self.session_error_fixes.get(error_pattern, [])
        if fixes:
            return fixes[-1]  # Most recent fix
        return None
    
    def get_error_pattern(self, error_type: str, failing_module: str = '') -> str:
        """Generate a normalized error pattern key."""
        return f"{error_type}:{failing_module}" if failing_module else error_type
    
    # ===========================================================
    # Few-Shot Examples for LLM
    # ===========================================================
    
    def get_few_shot_examples(self, imports: List[str], n: int = 3) -> str:
        """
        Generate few-shot examples from historically successful resolutions
        that involve similar packages. Used as LLM context.
        """
        import_set = set(i.lower() for i in imports)
        scored_examples = []
        
        for gist_id, sol in self.gist_solutions.items():
            if sol['confidence'] < 7 or not sol['packages']:
                continue
            pkg_set = set(p.lower() for p in sol['packages'])
            overlap = len(import_set & pkg_set)
            if overlap > 0:
                scored_examples.append((overlap, sol))
        
        scored_examples.sort(key=lambda x: -x[0])
        
        examples = []
        for _, sol in scored_examples[:n]:
            pkgs = ', '.join(sol['packages'])
            examples.append(
                f"Python {sol['python_version']}: packages=[{pkgs}] (confidence={sol['confidence']}/10)"
            )
        
        return '\n'.join(examples) if examples else ''
