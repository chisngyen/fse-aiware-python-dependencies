"""
LLM Client - Enhanced with RAG and Structured Output

Key improvements over basic version:
1. RAG: Feeds actual PyPI version lists to LLM for version selection
2. Structured prompts: Error-type-specific prompts (like PLLM)
3. JSON output parsing: More robust response parsing
4. Error history: Tells LLM which versions were already tried
"""

import json
import re
import requests
from typing import Optional, Dict, List, Tuple


class LLMClient:

    def __init__(self, base_url: str = "http://localhost:11434",
                 model: str = "gemma2", temp: float = 0.7):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.temp = temp
        self.session = requests.Session()
        self._available = None

    def _call(self, prompt: str, max_tokens: int = 512,
              json_mode: bool = False) -> str:
        """Make a call to Ollama API."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temp,
                    "num_predict": max_tokens,
                }
            }
            if json_mode:
                payload["format"] = "json"

            # Try with 60s timeout, retry once on timeout
            for attempt in range(2):
                try:
                    response = self.session.post(
                        f"{self.base_url}/api/generate",
                        json=payload,
                        timeout=60,
                    )
                    if response.status_code == 200:
                        return response.json().get('response', '')
                    else:
                        print(f"LLM HTTP error: {response.status_code}")
                        return ''
                except requests.exceptions.ReadTimeout:
                    if attempt == 0:
                        print(f"LLM timeout (60s), retrying...")
                        continue
                    print(f"LLM timeout after retry")
                    return ''
            return ''
        except requests.RequestException as e:
            print(f"LLM call failed: {e}")
            return ''

    def is_available(self) -> bool:
        """Check if the LLM server is available."""
        if self._available is not None:
            return self._available
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            self._available = response.status_code == 200
            return self._available
        except requests.RequestException:
            self._available = False
            return False

    # ========================
    # STAGE 1: File Evaluation
    # ========================

    def evaluate_file(self, code: str) -> Dict:
        """
        Evaluate a Python file and return python_version + python_modules.
        This is the initial LLM evaluation (similar to PLLM's evaluate_file).

        Returns: {'python_version': '3.7', 'python_modules': ['requests', 'flask']}
        """
        prompt = f"""Given this Python file, return the Python version needed and a list of pip-installable modules required to run it.

Rules:
- python_version should be like "2.7", "3.6", "3.7", "3.8", etc.
- python_modules should list ONLY third-party pip packages (not stdlib)
- Use pip package names (e.g., "beautifulsoup4" not "bs4", "scikit-learn" not "sklearn", "Pillow" not "PIL")
- Do NOT include: os, sys, json, re, math, datetime, collections, functools, itertools, etc.

Output ONLY valid JSON in this format:
{{"python_version": "X.Y", "python_modules": ["module1", "module2"]}}

Python file:
```python
{code[:3000]}
```

JSON output:"""

        response = self._call(prompt, max_tokens=256, json_mode=True)
        return self._parse_eval_response(response)

    def _parse_eval_response(self, response: str) -> Dict:
        """Parse the evaluate_file response."""
        default = {'python_version': '3.8', 'python_modules': []}

        if not response:
            return default

        try:
            data = json.loads(response.strip())
            version = str(data.get('python_version', '3.8'))
            modules = data.get('python_modules', [])

            # Validate version
            valid_versions = ['2.7', '3.4', '3.5', '3.6', '3.7', '3.8', '3.9', '3.10', '3.11']
            if version not in valid_versions:
                for v in valid_versions:
                    if v in version:
                        version = v
                        break
                else:
                    version = '3.8'

            # Ensure modules is a list
            if isinstance(modules, dict):
                modules = list(modules.keys())
            elif not isinstance(modules, list):
                modules = []

            # Clean module names
            clean_modules = []
            for m in modules:
                if isinstance(m, str) and len(m) > 1:
                    m = m.strip()
                    m = m.split('==')[0].split('>=')[0].split('<=')[0].strip()
                    if m and not m.startswith('#'):
                        clean_modules.append(m)

            return {'python_version': version, 'python_modules': clean_modules}

        except (json.JSONDecodeError, ValueError, AttributeError):
            version_match = re.search(r'"python_version"\s*:\s*"?([\d.]+)"?', response)
            version = version_match.group(1) if version_match else '3.8'
            modules = re.findall(r'"(\w[\w-]*)"', response)
            modules = [m for m in modules if m not in ('python_version', 'python_modules', version)]
            return {'python_version': version, 'python_modules': modules}

    # ===========================
    # STAGE 2: Version Selection (RAG)
    # ===========================

    def select_version(self, module_name: str, available_versions: str,
                       python_version: str, excluded_versions: str = '') -> Optional[str]:
        """
        Given a list of available versions from PyPI, ask LLM to select
        the best one for the given Python version.
        """
        if not available_versions:
            return None

        exclude_text = ""
        if excluded_versions:
            exclude_text = f"\nDO NOT select any of these previously failed versions: {excluded_versions}"

        prompt = f"""Given the available versions of the '{module_name}' Python module (from oldest to newest):
{available_versions}

Select a recent stable version compatible with Python {python_version}.{exclude_text}

Output ONLY valid JSON: {{"module": "{module_name}", "version": "X.Y.Z"}}
Use "None" as the version if no compatible version exists.

JSON output:"""

        response = self._call(prompt, max_tokens=64, json_mode=True)
        return self._parse_module_version(response, module_name)

    def _parse_module_version(self, response: str, expected_module: str = '') -> Optional[str]:
        """Parse a module version response."""
        if not response:
            return None

        try:
            data = json.loads(response.strip())
            version = str(data.get('version', '')).strip()

            if version and version.lower() not in ('none', 'null', ''):
                if re.match(r'^\d+(\.\d+){0,3}([a-zA-Z0-9]*)?$', version):
                    return version
        except (json.JSONDecodeError, ValueError, AttributeError):
            pass

        version_match = re.search(r'"version"\s*:\s*"(\d+[\d.a-zA-Z]*)"', response)
        if version_match:
            return version_match.group(1)

        return None

    # ===========================
    # STAGE 3: Error Analysis
    # ===========================

    def analyze_version_not_found(self, error: str, module_name: str,
                                    available_versions: str,
                                    excluded_versions: str = '') -> Optional[Dict[str, str]]:
        """Handle 'Could not find a version' errors."""
        exclude_text = ""
        if excluded_versions:
            exclude_text = f"\nExcluding previously failed versions: {excluded_versions}"

        # Try to extract version list from error itself (PLLM-style RAG)
        error_versions = self._extract_versions_from_error(error)
        if error_versions:
            available_versions = error_versions

        prompt = f"""A Docker build failed because a version could not be found.

Error:
{error[:1000]}

Available versions for '{module_name}' (oldest to newest):
{available_versions}
{exclude_text}

Select a compatible version from the available versions list.
Output ONLY valid JSON: {{"module": "{module_name}", "version": "X.Y.Z"}}
Use "None" for version if the module should be removed.

JSON output:"""

        response = self._call(prompt, max_tokens=64, json_mode=True)
        version = self._parse_module_version(response, module_name)

        if version:
            return {'module': module_name, 'version': version}
        return None

    def analyze_import_error(self, error: str, current_packages: Dict[str, str],
                              available_versions_map: Dict[str, str],
                              excluded_map: Dict[str, List[str]]) -> Optional[Dict[str, str]]:
        """Handle ImportError."""
        pkg_list = ', '.join(f"{k}=={v}" if v else k for k, v in current_packages.items())

        version_context = ""
        for pkg, versions_str in available_versions_map.items():
            if versions_str:
                excluded = ', '.join(excluded_map.get(pkg, []))
                ex_text = f" (exclude: {excluded})" if excluded else ""
                version_context += f"\n  {pkg}: [{versions_str[:300]}]{ex_text}"

        prompt = f"""An ImportError occurred when running a Python script.

Error:
{error[:1200]}

Currently installed packages: {pkg_list}

Available versions on PyPI:{version_context}

Identify the module causing the error and suggest a fix.
Output ONLY valid JSON: {{"module": "module_name", "version": "X.Y.Z"}}
- Use the pip package name for "module"
- Use "None" for version to remove the package
- Use a specific version string to change/add the package

JSON output:"""

        response = self._call(prompt, max_tokens=64, json_mode=True)
        return self._parse_module_action(response)

    def analyze_module_not_found(self, error: str, current_packages: Dict[str, str],
                                   python_version: str) -> Optional[Dict[str, str]]:
        """Handle ModuleNotFoundError."""
        pkg_list = ', '.join(f"{k}=={v}" if v else k for k, v in current_packages.items())

        prompt = f"""A ModuleNotFoundError occurred when running a Python {python_version} script.

Error:
{error[:1200]}

Currently installed packages: {pkg_list}

Identify the missing module and suggest the correct pip package name and version.
Output ONLY valid JSON: {{"module": "pip_package_name", "version": "X.Y.Z"}}
Use a recent stable version compatible with Python {python_version}.

JSON output:"""

        response = self._call(prompt, max_tokens=64, json_mode=True)
        return self._parse_module_action(response)

    def analyze_attribute_error(self, error: str, current_packages: Dict[str, str],
                                  available_versions_map: Dict[str, str],
                                  excluded_map: Dict[str, List[str]],
                                  python_version: str) -> Optional[Dict[str, str]]:
        """Handle AttributeError."""
        pkg_list = ', '.join(f"{k}=={v}" if v else k for k, v in current_packages.items())

        version_context = ""
        for pkg, versions_str in available_versions_map.items():
            if versions_str:
                excluded = ', '.join(excluded_map.get(pkg, []))
                ex_text = f" (exclude: {excluded})" if excluded else ""
                version_context += f"\n  {pkg}: [{versions_str[:300]}]{ex_text}"

        prompt = f"""An AttributeError occurred when running a Python {python_version} script.

Error:
{error[:1200]}

Currently installed packages: {pkg_list}

Available versions on PyPI:{version_context}

Identify which module is causing the error and suggest a version that would fix it.
Output ONLY valid JSON: {{"module": "module_name", "version": "X.Y.Z"}}

JSON output:"""

        response = self._call(prompt, max_tokens=64, json_mode=True)
        return self._parse_module_action(response)

    def analyze_syntax_error(self, error: str, current_packages: Dict[str, str],
                               python_version: str) -> Optional[Dict[str, str]]:
        """Handle SyntaxError."""
        pkg_list = ', '.join(f"{k}=={v}" if v else k for k, v in current_packages.items())

        prompt = f"""A SyntaxError occurred in a Python {python_version} Docker container.

Error:
{error[:1200]}

Currently installed packages: {pkg_list}

If the SyntaxError is in a module (not the main script), identify the module and suggest a compatible version.
If the SyntaxError is in the main script, suggest a different Python version.

Output ONLY valid JSON: {{"module": "module_name", "version": "X.Y.Z"}}
Use "PYTHON_VERSION_CHANGE" as module name if Python version should change.
Use "None" as version to remove a problematic module.

JSON output:"""

        response = self._call(prompt, max_tokens=64, json_mode=True)
        return self._parse_module_action(response)

    def analyze_dependency_conflict(self, error: str,
                                      current_packages: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Handle dependency conflict errors."""
        pkg_list = ', '.join(f"{k}=={v}" if v else k for k, v in current_packages.items())

        prompt = f"""A dependency conflict occurred during pip install.

Error:
{error[:1500]}

Currently installed packages: {pkg_list}

Identify the conflicting module and suggest a version that resolves the conflict.
Output ONLY valid JSON: {{"module": "module_name", "version": "X.Y.Z"}}

JSON output:"""

        response = self._call(prompt, max_tokens=64, json_mode=True)
        return self._parse_module_action(response)

    def analyze_non_zero_code(self, error: str,
                                current_packages: Dict[str, str],
                                available_versions_map: Dict[str, str],
                                excluded_map: Dict[str, List[str]]) -> Optional[Dict[str, str]]:
        """Handle non-zero exit code from pip install."""
        pkg_list = ', '.join(f"{k}=={v}" if v else k for k, v in current_packages.items())

        version_context = ""
        for pkg, versions_str in available_versions_map.items():
            if versions_str:
                excluded = ', '.join(excluded_map.get(pkg, []))
                ex_text = f" (exclude: {excluded})" if excluded else ""
                version_context += f"\n  {pkg}: [{versions_str[:300]}]{ex_text}"

        prompt = f"""A pip install command failed with a non-zero exit code.

Error:
{error[:1500]}

Currently installed packages: {pkg_list}

Available versions:{version_context}

Identify the failing module and suggest a version that would install correctly.
If a build dependency is needed (like Cython), include that instead.
Output ONLY valid JSON: {{"module": "module_name", "version": "X.Y.Z"}}
Use "None" as version to remove the module.

JSON output:"""

        response = self._call(prompt, max_tokens=64, json_mode=True)
        return self._parse_module_action(response)

    def analyze_generic_error(self, error: str, code: str,
                                python_version: str,
                                packages: Dict[str, str]) -> Optional[str]:
        """Generic error analysis fallback."""
        pkg_list = ', '.join(f"{k}=={v}" if v else k for k, v in packages.items())

        prompt = f"""You are debugging a Python dependency issue.

Python version: {python_version}
Installed packages: {pkg_list}

Error:
```
{error[:1500]}
```

Code excerpt:
```python
{code[:1000]}
```

What is the most likely fix? Choose ONE action:
1. CHANGE_VERSION: python_version=X.Y
2. ADD_PACKAGE: package_name==version
3. REMOVE_PACKAGE: package_name
4. PIN_VERSION: package_name==version
5. UNFIXABLE: this code cannot run in a Docker container

Reply with ONLY the action in the format above."""

        response = self._call(prompt, max_tokens=64)
        return response.strip().split('\n')[0].strip()

    def _parse_module_action(self, response: str) -> Optional[Dict[str, str]]:
        """Parse a module/version action response from LLM."""
        if not response:
            return None

        try:
            data = json.loads(response.strip())
            module = str(data.get('module', '')).strip()
            version = str(data.get('version', '')).strip()

            if not module:
                return None

            module = module.strip()

            if version.lower() in ('none', 'null', ''):
                version = None

            return {'module': module, 'version': version}

        except (json.JSONDecodeError, ValueError, AttributeError):
            module_match = re.search(r'"module"\s*:\s*"([^"]+)"', response)
            version_match = re.search(r'"version"\s*:\s*"([^"]+)"', response)

            if module_match:
                module = module_match.group(1).strip()
                version = version_match.group(1).strip() if version_match else None
                if version and version.lower() in ('none', 'null'):
                    version = None
                return {'module': module, 'version': version}

        return None

    def _extract_versions_from_error(self, error: str) -> str:
        """Extract 'from versions:' list from pip error output."""
        match = re.search(r'from versions:\s*([\d., ]+)', error)
        if match:
            return match.group(1).strip()
        return ''

    # ===========================
    # Reflexion-Enhanced Analysis (Novel Contribution #2)
    # ===========================

    def evaluate_file_with_context(self, code: str, 
                                     reflection_context: str = '',
                                     few_shot_examples: str = '') -> Dict:
        """
        Enhanced evaluate_file with Reflexion memory and few-shot examples.
        """
        context_block = ""
        if reflection_context:
            context_block += f"\n{reflection_context}\n"
        if few_shot_examples:
            context_block += f"\nSIMILAR SUCCESSFUL RESOLUTIONS:\n{few_shot_examples}\n"

        prompt = f"""Given this Python file, return the Python version needed and a list of pip-installable modules required to run it.
{context_block}
Rules:
- python_version should be like "2.7", "3.6", "3.7", "3.8", etc.
- python_modules should list ONLY third-party pip packages (not stdlib)
- Use pip package names (e.g., "beautifulsoup4" not "bs4", "scikit-learn" not "sklearn", "Pillow" not "PIL")
- Do NOT include: os, sys, json, re, math, datetime, collections, functools, itertools, etc.
- For Python 2 code (print statements without parens, urllib2, etc.), use "2.7"

Output ONLY valid JSON in this format:
{{"python_version": "X.Y", "python_modules": ["module1", "module2"]}}

Python file:
```python
{code[:3000]}
```

JSON output:"""

        response = self._call(prompt, max_tokens=256, json_mode=True)
        return self._parse_eval_response(response)

    def analyze_error_with_reflection(self, error: str, error_type: str,
                                        packages: Dict[str, str],
                                        python_version: str, code: str,
                                        reflection_context: str = '',
                                        available_versions: str = '') -> Optional[Dict[str, str]]:
        """
        Reflexion-enhanced error analysis. Uses accumulated reflections 
        to make better fixing decisions.
        """
        pkg_list = ', '.join(f"{k}=={v}" if v else k for k, v in packages.items())

        context_block = ""
        if reflection_context:
            context_block = f"\n{reflection_context}\n"

        version_block = ""
        if available_versions:
            version_block = f"\nAvailable versions on PyPI:\n{available_versions}\n"

        prompt = f"""You are debugging Python dependency issues. Analyze this error and suggest ONE fix.
{context_block}
Error type: {error_type}
Python version: {python_version}
Installed packages: {pkg_list}
{version_block}
Error:
{error[:1500]}

Code excerpt:
```python
{code[:500]}
```

Rules:
- If the error is a SyntaxError in the main script, the Python version is wrong
- If a package fails to install, try a different version from the available list
- If a module is not found, suggest the correct pip package name
- Do NOT suggest versions you already know failed (see reflections above)

Output ONLY valid JSON: {{"module": "name", "version": "X.Y.Z"}}
- "module": pip package name, or "PYTHON_VERSION_CHANGE" to change Python version
- "version": version string, or "None" to remove, or Python version number for version change

JSON output:"""

        response = self._call(prompt, max_tokens=128, json_mode=True)
        return self._parse_module_action(response)

    def generate_reflection(self, error: str, error_type: str,
                             packages: Dict[str, str], python_version: str,
                             fix_applied: Optional[Dict] = None) -> str:
        """
        Generate a verbal reflection about what went wrong and what to try next.
        This is the core of the Reflexion approach.
        """
        pkg_list = ', '.join(f"{k}=={v}" if v else k for k, v in packages.items())
        fix_text = ""
        if fix_applied:
            fix_text = f"Fix applied: {fix_applied}"

        prompt = f"""After a failed attempt to resolve Python dependencies, reflect on what went wrong.

Python {python_version}, packages: {pkg_list}
Error type: {error_type}
Error: {error[:500]}
{fix_text}

Write a ONE SENTENCE reflection about what should be tried differently next time.
Focus on the root cause and a concrete suggestion."""

        response = self._call(prompt, max_tokens=64)
        return response.strip().split('\n')[0].strip()[:200] if response else ""

    # Legacy compatibility

    def suggest_python_version(self, code: str) -> Optional[str]:
        result = self.evaluate_file(code)
        return result.get('python_version')

    def suggest_dependencies(self, code: str, python_version: str,
                              error_log: str = '') -> Dict[str, str]:
        result = self.evaluate_file(code)
        packages = {}
        for module in result.get('python_modules', []):
            packages[module] = ''
        return packages
