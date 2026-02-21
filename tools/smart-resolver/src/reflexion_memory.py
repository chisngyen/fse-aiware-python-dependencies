"""
Reflexion Memory - Verbal Reinforcement Learning for Dependency Resolution

Novel Contribution #2: Inspired by Reflexion (Shinn et al., 2023) and
Self-Debugging (Chen et al., 2023), this module implements verbal reflections
that accumulate across build/test attempts.

Key Insight: Instead of just tracking which versions failed (as PLLM does),
we generate natural language reflections that capture WHY they failed and
what should be tried differently. These reflections are fed back to the LLM
in subsequent attempts, enabling it to learn from its own mistakes within
a single resolution episode.

This is fundamentally different from PLLM's simple error_handler which only
tracks error types and counts. Our approach captures semantic reasoning about
failures.
"""

from typing import Dict, List, Optional
from collections import defaultdict


class ReflexionMemory:
    """
    Maintains verbal reflections across build/test attempts.
    
    Each reflection captures:
    - What was attempted (packages, versions, Python version)
    - What went wrong (error type, specific error)
    - What should be done differently (LLM-generated insight)
    
    These reflections form an episodic memory buffer that improves
    subsequent LLM decisions.
    """

    def __init__(self, max_reflections: int = 10):
        self.max_reflections = max_reflections
        self.reflections = []  # List of reflection strings
        self.attempt_history = []  # Structured attempt records
        self.version_blacklist = defaultdict(set)  # module → set of bad versions
        self.failed_approaches = []  # High-level approach descriptions
        self.success_hints = []  # Things that partially worked
        
    def add_attempt(self, python_version: str, packages: Dict[str, str],
                    error_type: str, error_summary: str, 
                    error_phase: str, llm_reflection: str = ''):
        """
        Record an attempt and generate a reflection.
        
        Args:
            python_version: Python version tried
            packages: Packages dict (name→version)
            error_type: Classified error type
            error_summary: Short error description
            error_phase: 'build' or 'run'
            llm_reflection: Optional LLM-generated reflection
        """
        attempt = {
            'python_version': python_version,
            'packages': dict(packages),
            'error_type': error_type,
            'error_summary': error_summary[:200],
            'error_phase': error_phase,
        }
        self.attempt_history.append(attempt)
        
        # Track bad versions
        if error_phase == 'build':
            # Build failures often mean wrong version for this Python
            for pkg, ver in packages.items():
                if ver and error_summary and pkg.lower() in error_summary.lower():
                    self.version_blacklist[pkg].add(ver)
        
        # Generate reflection
        pkg_str = ', '.join(f"{k}=={v}" if v else k for k, v in packages.items())
        
        reflection = f"Attempt {len(self.attempt_history)}: "
        reflection += f"Python {python_version} with [{pkg_str}] → "
        reflection += f"{error_phase} {error_type}: {error_summary[:100]}"
        
        if llm_reflection:
            reflection += f". Insight: {llm_reflection}"
        
        # Add self-generated insight based on error type
        insight = self._generate_insight(error_type, error_summary, 
                                          python_version, packages)
        if insight:
            reflection += f". {insight}"
        
        self.reflections.append(reflection)
        
        # Keep only last N reflections
        if len(self.reflections) > self.max_reflections:
            self.reflections = self.reflections[-self.max_reflections:]
    
    def add_partial_success(self, hint: str):
        """Record something that partially worked."""
        self.success_hints.append(hint)
    
    def _generate_insight(self, error_type: str, error: str,
                           python_version: str, packages: Dict[str, str]) -> str:
        """Generate rule-based insight from error patterns."""
        
        if error_type == 'SyntaxError':
            if 'print ' in error or 'print(' not in error:
                return "This code likely uses Python 2 syntax. Try Python 2.7."
            if 'f-string' in error.lower() or "f'" in error or 'f"' in error:
                return "Uses f-strings, needs Python 3.6+."
            if 'walrus' in error.lower() or ':=' in error:
                return "Uses walrus operator, needs Python 3.8+."
            return f"Syntax incompatible with Python {python_version}, try different version."
        
        if error_type == 'NonZeroCode':
            if 'requires Python' in error:
                import re
                match = re.search(r'requires Python\s*([><=!]+\s*[\d.]+)', error)
                if match:
                    return f"Package requires Python {match.group(1)}, adjust version."
            if 'Could not build wheels' in error or 'setup.py' in error:
                return "Package needs compilation, may require system libraries or different version."
            return "pip install failed, likely version incompatible with this Python."
        
        if error_type == 'ImportError' or error_type == 'ModuleNotFound':
            import re
            match = re.search(r"No module named ['\"]?(\w[\w.]*)", error)
            if match:
                missing = match.group(1).split('.')[0]
                return f"Missing module '{missing}', need to add it as a dependency."
        
        if error_type == 'DependencyConflict':
            return "Version conflict between packages, need compatible version set."
        
        if error_type == 'Timeout':
            return "Build took too long, package may be too large to compile in time."
        
        return ""
    
    def get_reflection_context(self) -> str:
        """
        Get the accumulated reflections as context for LLM.
        This is the key feature - feeding reflections back to improve decisions.
        """
        if not self.reflections:
            return ""
        
        context = "PREVIOUS ATTEMPTS AND REFLECTIONS:\n"
        for ref in self.reflections:
            context += f"- {ref}\n"
        
        if self.success_hints:
            context += "\nPARTIAL SUCCESSES:\n"
            for hint in self.success_hints[-3:]:
                context += f"- {hint}\n"
        
        if self.version_blacklist:
            context += "\nKNOWN BAD VERSIONS (do not suggest these):\n"
            for pkg, versions in self.version_blacklist.items():
                if versions:
                    context += f"- {pkg}: {', '.join(sorted(versions))}\n"
        
        context += "\nBased on these reflections, make a DIFFERENT choice than before.\n"
        return context
    
    def get_tried_versions(self, module: str) -> List[str]:
        """Get all versions tried for a module across all attempts."""
        versions = set()
        for attempt in self.attempt_history:
            ver = attempt['packages'].get(module, '')
            if ver:
                versions.add(ver)
        versions.update(self.version_blacklist.get(module, set()))
        return sorted(versions)
    
    def get_tried_python_versions(self) -> List[str]:
        """Get all Python versions that have been tried."""
        return list(set(a['python_version'] for a in self.attempt_history))
    
    def should_skip_version(self, module: str, version: str) -> bool:
        """Check if a version is known to be bad."""
        return version in self.version_blacklist.get(module, set())
    
    def get_summary(self) -> str:
        """Get a brief summary of all attempts."""
        if not self.attempt_history:
            return "No previous attempts."
        
        total = len(self.attempt_history)
        error_counts = defaultdict(int)
        py_vers = set()
        for a in self.attempt_history:
            error_counts[a['error_type']] += 1
            py_vers.add(a['python_version'])
        
        errors = ', '.join(f"{k}({v})" for k, v in error_counts.items())
        return f"{total} attempts across Python {', '.join(sorted(py_vers))}. Errors: {errors}"
    
    def reset(self):
        """Reset memory for a new snippet."""
        self.reflections.clear()
        self.attempt_history.clear()
        self.version_blacklist.clear()
        self.failed_approaches.clear()
        self.success_hints.clear()
