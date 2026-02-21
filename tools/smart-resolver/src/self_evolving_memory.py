"""
Self-Evolving Session Memory - Novel Contribution for FSE 2026 AIWare

Inspired by Mobile-Agent-E (Wang et al., 2025) self-evolving paradigm:
- Tips: High-level guidelines accumulated from resolution experience
- Shortcuts: Reusable resolution patterns from successful sessions

Unlike static knowledge bases, this module LEARNS during runtime:
1. After each successful resolution, extracts "Tips" (version compatibility
   insights, Python version recommendations) and "Shortcuts" (proven
   package→version combos that can be directly reused).
2. After each failed resolution, records anti-patterns to avoid.
3. Later snippets benefit from earlier resolutions within the same session.

Key Innovation: Applies self-evolving agent paradigm (from GUI navigation)
to dependency resolution — a novel domain transfer.

References:
- Wang et al., "Mobile-Agent-E: Self-Evolving Mobile Assistant", 2025
- Shinn et al., "Reflexion: Language Agents with Verbal RL", NeurIPS 2023
"""

import re
import time
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple


class SelfEvolvingMemory:
    """
    Self-evolving session memory that accumulates Tips and Shortcuts
    across snippet resolutions within a single session.
    
    Tips: Natural language guidelines (e.g., "twisted needs py2.7 for 
    StringIO compatibility", "torch+cpu is faster to install")
    
    Shortcuts: Concrete resolution patterns (e.g., {imports: ['cv2'],
    packages: {'opencv-python': '4.5.5.64'}, python: '3.7'})
    """

    def __init__(self, logging: bool = True):
        self.logging = logging
        
        # === Tips: high-level guidelines ===
        self.tips: List[Dict] = []
        # Each tip: {
        #   'text': str,          # Natural language tip
        #   'source_gist': str,   # Which gist generated this tip
        #   'category': str,      # 'version', 'package', 'python', 'error'
        #   'confidence': float,  # 0-1
        #   'uses': int,          # How many times this tip was applied
        # }
        
        # === Shortcuts: reusable resolution patterns ===
        self.shortcuts: List[Dict] = []
        # Each shortcut: {
        #   'imports': set,           # Import names that trigger this shortcut
        #   'packages': dict,         # {pkg: version}
        #   'python_version': str,
        #   'source_gist': str,
        #   'duration': float,        # How long it took
        #   'uses': int,
        # }
        
        # === Anti-patterns: things to avoid ===
        self.anti_patterns: List[Dict] = []
        # Each: {
        #   'pattern': str,        # What went wrong
        #   'imports': set,        # Which imports triggered it
        #   'category': str,       # 'timeout', 'version_conflict', 'system_only'
        # }
        
        # === Package success/failure tracking ===
        self.package_success: Dict[str, Dict] = defaultdict(lambda: {
            'success_count': 0,
            'fail_count': 0,
            'best_version': {},       # py_ver → version
            'failed_versions': {},    # py_ver → [versions]
            'copackages': set(),      # packages that succeeded together
        })
        
        # === Import → Package resolution cache ===
        self.import_resolution_cache: Dict[str, str] = {}
        
        # === Python version success tracking ===
        self.python_version_success: Dict[str, int] = defaultdict(int)
        self.python_version_fail: Dict[str, int] = defaultdict(int)
        
        # Session statistics
        self.session_start = time.time()
        self.total_resolved = 0
        self.total_failed = 0
    
    def log(self, msg: str):
        if self.logging:
            print(f"  [SelfEvolve] {msg}", flush=True)
    
    # ===========================================================
    # Learning from successes
    # ===========================================================
    
    def learn_from_success(self, gist_id: str, python_version: str,
                           packages: Dict[str, str], imports: List[str],
                           duration: float, error_history: List[Dict] = None):
        """
        Extract Tips and Shortcuts from a successful resolution.
        Called after each successful snippet resolution.
        """
        self.total_resolved += 1
        self.python_version_success[python_version] += 1
        
        # Record package success
        for pkg, ver in packages.items():
            self.package_success[pkg]['success_count'] += 1
            if ver:
                self.package_success[pkg]['best_version'][python_version] = ver
            self.package_success[pkg]['copackages'].update(
                p for p in packages if p != pkg
            )
        
        # Cache import→package resolutions
        for imp in imports:
            imp_lower = imp.lower()
            for pkg in packages:
                pkg_lower = pkg.lower()
                # Heuristic: import name matches package name
                if (imp_lower == pkg_lower or 
                    imp_lower.replace('-', '_') == pkg_lower.replace('-', '_') or
                    imp_lower in pkg_lower or pkg_lower in imp_lower):
                    self.import_resolution_cache[imp_lower] = pkg
        
        # === Generate Tips ===
        
        # Tip: Python version compatibility
        if error_history:
            failed_py_versions = set()
            for attempt in error_history:
                if not attempt.get('success', False):
                    failed_py_versions.add(attempt.get('python_version', ''))
            
            if failed_py_versions:
                tip_text = (f"For imports {imports[:3]}, Python {python_version} "
                           f"works but {failed_py_versions} fail")
                self._add_tip(tip_text, gist_id, 'python', 0.8)
        
        # Tip: Package version insights
        for pkg, ver in packages.items():
            if ver:
                tip_text = f"{pkg}=={ver} works on Python {python_version}"
                self._add_tip(tip_text, gist_id, 'version', 0.7)
        
        # Tip: Duration insight for heavy packages
        if duration > 120:
            heavy = [p for p in packages if p.lower() in 
                    {'tensorflow', 'torch', 'scipy', 'keras', 'mxnet'}]
            if heavy:
                tip_text = (f"Heavy packages {heavy} take {duration:.0f}s to install, "
                           f"allocate extra time")
                self._add_tip(tip_text, gist_id, 'performance', 0.9)
        
        # === Generate Shortcut ===
        import_set = set(imp.lower() for imp in imports) if imports else set()
        if import_set and packages:
            self.shortcuts.append({
                'imports': import_set,
                'packages': dict(packages),
                'python_version': python_version,
                'source_gist': gist_id,
                'duration': duration,
                'uses': 0,
            })
        
        self.log(f"Learned from {gist_id}: {len(self.tips)} tips, "
                f"{len(self.shortcuts)} shortcuts")
    
    def learn_from_failure(self, gist_id: str, python_version: str,
                           packages: Dict[str, str], imports: List[str],
                           error_type: str, error_msg: str):
        """Record anti-patterns from a failed resolution."""
        self.total_failed += 1
        self.python_version_fail[python_version] += 1
        
        # Record package failures
        for pkg, ver in packages.items():
            self.package_success[pkg]['fail_count'] += 1
            if ver:
                if python_version not in self.package_success[pkg]['failed_versions']:
                    self.package_success[pkg]['failed_versions'][python_version] = []
                self.package_success[pkg]['failed_versions'][python_version].append(ver)
        
        # Categorize anti-pattern
        import_set = set(imp.lower() for imp in imports) if imports else set()
        category = 'unknown'
        if error_type == 'Timeout':
            category = 'timeout'
        elif error_type in ('ImportError', 'ModuleNotFound'):
            category = 'missing_package'
        elif error_type in ('VersionNotFound', 'NonZeroCode'):
            category = 'version_conflict'
        elif error_type == 'SyntaxError':
            category = 'python_version'
        
        self.anti_patterns.append({
            'pattern': f"{error_type}: {error_msg[:100]}",
            'imports': import_set,
            'packages': dict(packages),
            'python_version': python_version,
            'category': category,
            'source_gist': gist_id,
        })
    
    # ===========================================================
    # Querying accumulated knowledge
    # ===========================================================
    
    def find_shortcut(self, imports: List[str]) -> Optional[Dict]:
        """
        Find a matching shortcut for the given imports.
        Returns the best-matching shortcut (highest Jaccard similarity).
        """
        if not imports or not self.shortcuts:
            return None
        
        query_set = set(imp.lower() for imp in imports)
        best_match = None
        best_score = 0.0
        
        for shortcut in self.shortcuts:
            # Jaccard similarity
            intersection = len(query_set & shortcut['imports'])
            union = len(query_set | shortcut['imports'])
            if union == 0:
                continue
            score = intersection / union
            
            # Boost score if all query imports are covered
            if query_set.issubset(shortcut['imports']):
                score += 0.3
            
            if score > best_score and score >= 0.5:
                best_score = score
                best_match = shortcut
        
        if best_match:
            best_match['uses'] += 1
            self.log(f"Shortcut match (score={best_score:.2f}): "
                    f"{best_match['packages']}")
        
        return best_match
    
    def get_relevant_tips(self, imports: List[str] = None,
                          packages: List[str] = None,
                          category: str = None) -> List[str]:
        """Get tips relevant to the current resolution context."""
        relevant = []
        
        for tip in self.tips:
            # Filter by category if specified
            if category and tip['category'] != category:
                continue
            
            # All tips with high confidence are always relevant
            if tip['confidence'] >= 0.8:
                relevant.append(tip['text'])
                continue
            
            # Check package relevance
            if packages:
                for pkg in packages:
                    if pkg.lower() in tip['text'].lower():
                        relevant.append(tip['text'])
                        break
        
        return relevant[:10]  # Max 10 tips
    
    def get_best_version(self, package: str, python_version: str) -> Optional[str]:
        """Get the best known version for a package from session experience."""
        info = self.package_success.get(package)
        if not info:
            return None
        
        best = info['best_version'].get(python_version)
        if best:
            self.log(f"Session version for {package} on py{python_version}: {best}")
        return best
    
    def should_avoid_version(self, package: str, version: str,
                            python_version: str) -> bool:
        """Check if a version was previously tried and failed."""
        info = self.package_success.get(package)
        if not info:
            return False
        
        failed = info['failed_versions'].get(python_version, [])
        return version in failed
    
    def get_recommended_python_version(self) -> Optional[str]:
        """
        Recommend Python version based on session success rates.
        Weighted by number of successes minus failures.
        """
        scores = {}
        for ver in set(list(self.python_version_success.keys()) + 
                      list(self.python_version_fail.keys())):
            scores[ver] = (self.python_version_success.get(ver, 0) - 
                          self.python_version_fail.get(ver, 0) * 0.5)
        
        if not scores:
            return None
        
        return max(scores, key=scores.get)
    
    def get_known_copackages(self, package: str) -> Set[str]:
        """Get packages that have been successfully used together with this one."""
        info = self.package_success.get(package)
        if info:
            return info['copackages']
        return set()
    
    def resolve_import(self, import_name: str) -> Optional[str]:
        """
        Try to resolve an import name to a pip package using session cache.
        """
        return self.import_resolution_cache.get(import_name.lower())
    
    # ===========================================================
    # Tips for LLM context
    # ===========================================================
    
    def get_tips_context(self) -> str:
        """
        Generate a context string of accumulated tips for LLM prompts.
        This is fed as additional context to the LLM during resolution.
        """
        if not self.tips and not self.shortcuts:
            return ""
        
        parts = []
        if self.tips:
            parts.append("=== Session Tips (learned from previous snippets) ===")
            seen = set()
            for tip in self.tips[-15:]:  # Last 15 tips
                if tip['text'] not in seen:
                    parts.append(f"- {tip['text']}")
                    seen.add(tip['text'])
        
        if self.shortcuts:
            parts.append("\n=== Known Working Shortcuts ===")
            for sc in self.shortcuts[-5:]:  # Last 5 shortcuts
                pkgs = ', '.join(f"{k}=={v}" if v else k 
                               for k, v in sc['packages'].items())
                parts.append(f"- Python {sc['python_version']}: {pkgs}")
        
        return "\n".join(parts)
    
    def get_session_summary(self) -> Dict:
        """Get a summary of what the session has learned."""
        return {
            'total_resolved': self.total_resolved,
            'total_failed': self.total_failed,
            'tips_count': len(self.tips),
            'shortcuts_count': len(self.shortcuts),
            'anti_patterns_count': len(self.anti_patterns),
            'cached_imports': len(self.import_resolution_cache),
            'session_duration': time.time() - self.session_start,
            'success_rate': (self.total_resolved / 
                           max(1, self.total_resolved + self.total_failed)),
        }
    
    # ===========================================================
    # Internal helpers
    # ===========================================================
    
    def _add_tip(self, text: str, source_gist: str, category: str,
                 confidence: float):
        """Add a tip, deduplicating similar tips."""
        # Check for duplicates
        for existing in self.tips:
            if existing['text'] == text:
                existing['confidence'] = max(existing['confidence'], confidence)
                return
        
        self.tips.append({
            'text': text,
            'source_gist': source_gist,
            'category': category,
            'confidence': confidence,
            'uses': 0,
        })
