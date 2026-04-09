"""
Co-occurrence Mining & Dependency Group Templates

Novel Contribution: Inspired by Voyager's skill library (Wang et al., 2023)
and ReGAL's abstraction learning (Stengel-Eskin et al., 2024).

Key ideas:
1. Mine package co-occurrence patterns from historical oracle data
2. Build "dependency group templates" (e.g., ML stack, web stack)
3. When a snippet has partial module info, predict missing packages
4. Provide version combos known to work together

This enables:
- Predicting missing imports that LLM/static miss
- Providing proven version combinations
- Fast-tracking common dependency patterns
"""

from collections import defaultdict, Counter
from typing import Dict, List, Optional, Set, Tuple
import csv
import os
import json
import re


class CooccurrenceMiner:
    """Mines package co-occurrence patterns from historical data."""

    # Pre-defined dependency group templates (common ecosystems)
    DEPENDENCY_GROUPS = {
        'ml_tensorflow': {
            'trigger': {'tensorflow', 'tf'},
            'packages': {
                '2.7': {'tensorflow': '1.5.0', 'numpy': '1.16.6', 'scipy': '1.2.3',
                         'keras': '2.2.4', 'h5py': '2.10.0'},
                '3.6': {'tensorflow': '1.15.5', 'numpy': '1.19.5', 'scipy': '1.5.4',
                         'keras': '2.3.1', 'h5py': '2.10.0'},
                '3.7': {'tensorflow': '2.10.1', 'numpy': '1.21.6', 'scipy': '1.7.3',
                         'keras': '2.10.0', 'h5py': '3.7.0'},
                '3.8': {'tensorflow': '2.13.1', 'numpy': '1.24.3', 'scipy': '1.10.1',
                         'keras': '2.13.1', 'h5py': '3.9.0'},
            },
        },
        'ml_pytorch': {
            'trigger': {'torch', 'pytorch'},
            'packages': {
                '3.6': {'torch': '1.9.1', 'numpy': '1.19.5', 'torchvision': '0.10.1'},
                '3.7': {'torch': '1.13.1', 'numpy': '1.21.6', 'torchvision': '0.14.1'},
                '3.8': {'torch': '2.0.1', 'numpy': '1.24.3', 'torchvision': '0.15.2'},
            },
        },
        'ml_sklearn': {
            'trigger': {'sklearn', 'scikit-learn'},
            'packages': {
                '2.7': {'scikit-learn': '0.20.4', 'numpy': '1.16.6', 'scipy': '1.2.3'},
                '3.6': {'scikit-learn': '0.24.2', 'numpy': '1.19.5', 'scipy': '1.5.4'},
                '3.7': {'scikit-learn': '1.0.2', 'numpy': '1.21.6', 'scipy': '1.7.3'},
                '3.8': {'scikit-learn': '1.3.2', 'numpy': '1.24.3', 'scipy': '1.10.1'},
            },
        },
        'data_science': {
            'trigger': {'pandas', 'matplotlib'},
            'packages': {
                '2.7': {'pandas': '0.24.2', 'numpy': '1.16.6', 'matplotlib': '2.2.5'},
                '3.6': {'pandas': '1.1.5', 'numpy': '1.19.5', 'matplotlib': '3.3.4'},
                '3.7': {'pandas': '1.3.5', 'numpy': '1.21.6', 'matplotlib': '3.5.3'},
                '3.8': {'pandas': '2.0.3', 'numpy': '1.24.3', 'matplotlib': '3.7.5'},
            },
        },
        'web_flask': {
            'trigger': {'flask'},
            'packages': {
                '2.7': {'flask': '1.1.4', 'jinja2': '2.11.3', 'werkzeug': '1.0.1',
                         'itsdangerous': '1.1.0'},
                '3.6': {'flask': '2.0.3', 'jinja2': '3.0.3', 'werkzeug': '2.0.3'},
                '3.7': {'flask': '2.2.5', 'jinja2': '3.1.2', 'werkzeug': '2.2.3'},
                '3.8': {'flask': '3.0.0', 'jinja2': '3.1.2', 'werkzeug': '3.0.1'},
            },
        },
        'web_django': {
            'trigger': {'django'},
            'packages': {
                '2.7': {'django': '1.11.29'},
                '3.6': {'django': '3.2.25'},
                '3.7': {'django': '3.2.25'},
                '3.8': {'django': '4.2.9'},
            },
        },
        'web_requests': {
            'trigger': {'requests'},
            'packages': {
                '2.7': {'requests': '2.27.1', 'urllib3': '1.26.18',
                         'certifi': '2021.10.8'},
                '3.6': {'requests': '2.27.1', 'urllib3': '1.26.18'},
                '3.7': {'requests': '2.31.0', 'urllib3': '2.1.0'},
                '3.8': {'requests': '2.31.0', 'urllib3': '2.1.0'},
            },
        },
        'web_scrapy': {
            'trigger': {'scrapy'},
            'packages': {
                '2.7': {'scrapy': '1.8.2', 'twisted': '20.3.0'},
                '3.6': {'scrapy': '2.5.1', 'twisted': '21.7.0'},
                '3.7': {'scrapy': '2.8.0', 'twisted': '22.10.0'},
            },
        },
        'image_processing': {
            'trigger': {'PIL', 'Pillow', 'cv2', 'opencv-python'},
            'packages': {
                '2.7': {'Pillow': '6.2.2', 'numpy': '1.16.6'},
                '3.6': {'Pillow': '8.4.0', 'numpy': '1.19.5'},
                '3.7': {'Pillow': '9.5.0', 'numpy': '1.21.6'},
                '3.8': {'Pillow': '10.1.0', 'numpy': '1.24.3'},
            },
        },
        'nlp_nltk': {
            'trigger': {'nltk'},
            'packages': {
                '2.7': {'nltk': '3.4.5'},
                '3.6': {'nltk': '3.6.7'},
                '3.7': {'nltk': '3.8.1'},
            },
        },
        'crypto': {
            'trigger': {'cryptography', 'Crypto', 'pycryptodome'},
            'packages': {
                '2.7': {'pycryptodome': '3.9.9'},
                '3.6': {'pycryptodome': '3.15.0', 'cryptography': '3.4.8'},
                '3.7': {'pycryptodome': '3.19.0', 'cryptography': '41.0.7'},
            },
        },
        'async_web': {
            'trigger': {'aiohttp', 'asyncio'},
            'packages': {
                '3.6': {'aiohttp': '3.8.6', 'aiosignal': '1.2.0'},
                '3.7': {'aiohttp': '3.9.1'},
                '3.8': {'aiohttp': '3.9.1'},
            },
        },
        'database': {
            'trigger': {'sqlalchemy', 'psycopg2'},
            'packages': {
                '2.7': {'sqlalchemy': '1.3.24', 'psycopg2-binary': '2.8.6'},
                '3.6': {'sqlalchemy': '1.4.51', 'psycopg2-binary': '2.9.9'},
                '3.7': {'sqlalchemy': '1.4.51', 'psycopg2-binary': '2.9.9'},
                '3.8': {'sqlalchemy': '2.0.23', 'psycopg2-binary': '2.9.9'},
            },
        },
        'aws': {
            'trigger': {'boto3', 'boto', 'aws'},
            'packages': {
                '2.7': {'boto': '2.49.0', 'boto3': '1.17.112'},
                '3.6': {'boto3': '1.26.165'},
                '3.7': {'boto3': '1.34.14'},
            },
        },
        'testing': {
            'trigger': {'pytest', 'mock', 'unittest2'},
            'packages': {
                '2.7': {'pytest': '4.6.11', 'mock': '3.0.5'},
                '3.6': {'pytest': '7.0.1'},
                '3.7': {'pytest': '7.4.4'},
            },
        },
        # --- New templates for common failure patterns ---
        'geo_gdal': {
            'trigger': {'gdal', 'osgeo', 'ogr', 'osr'},
            'packages': {
                '2.7': {'gdal': '2.4.4', 'numpy': '1.16.6'},
                '3.6': {'gdal': '3.0.4', 'numpy': '1.19.5'},
                '3.7': {'gdal': '3.4.3', 'numpy': '1.21.6'},
            },
        },
        'xml_lxml': {
            'trigger': {'lxml', 'etree'},
            'packages': {
                '2.7': {'lxml': '4.6.5'},
                '3.6': {'lxml': '4.9.3'},
                '3.7': {'lxml': '4.9.3'},
                '3.8': {'lxml': '4.9.3'},
            },
        },
        'celery_stack': {
            'trigger': {'celery'},
            'packages': {
                '2.7': {'celery': '4.4.7', 'kombu': '4.6.11', 'billiard': '3.6.4.0'},
                '3.6': {'celery': '5.2.7', 'kombu': '5.2.4'},
                '3.7': {'celery': '5.3.6', 'kombu': '5.3.4'},
            },
        },
        'fastapi': {
            'trigger': {'fastapi', 'uvicorn'},
            'packages': {
                '3.7': {'fastapi': '0.95.2', 'uvicorn': '0.22.0', 'pydantic': '1.10.13'},
                '3.8': {'fastapi': '0.109.0', 'uvicorn': '0.27.0', 'pydantic': '2.5.3'},
            },
        },
        'plotly_viz': {
            'trigger': {'plotly', 'dash'},
            'packages': {
                '2.7': {'plotly': '4.14.3', 'numpy': '1.16.6'},
                '3.6': {'plotly': '5.9.0', 'numpy': '1.19.5'},
                '3.7': {'plotly': '5.18.0', 'numpy': '1.21.6'},
            },
        },
        'spacy_nlp': {
            'trigger': {'spacy'},
            'packages': {
                '3.6': {'spacy': '3.1.7', 'thinc': '8.0.17'},
                '3.7': {'spacy': '3.5.4', 'thinc': '8.1.12'},
                '3.8': {'spacy': '3.7.2', 'thinc': '8.2.2'},
            },
        },
        'selenium': {
            'trigger': {'selenium', 'webdriver'},
            'packages': {
                '2.7': {'selenium': '3.141.0'},
                '3.6': {'selenium': '4.1.5'},
                '3.7': {'selenium': '4.15.2'},
            },
        },
    }

    def __init__(self, results_dir: str = None, logging: bool = True):
        self.logging = logging
        self.cooccurrence: Dict[str, Counter] = defaultdict(Counter)
        self.package_versions: Dict[str, Dict[str, str]] = {}
        self.success_combos: List[Dict] = []

        if results_dir:
            self._load_from_results(results_dir)

    def log(self, msg: str):
        if self.logging:
            print(f"  [CoMiner] {msg}", flush=True)

    def _load_from_results(self, results_dir: str):
        """Mine co-occurrence patterns from historical PLLM results."""
        csv_path = os.path.join(results_dir, 'pllm_results', 'csv',
                                'summary-all-runs.csv')
        if not os.path.exists(csv_path):
            return

        try:
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('run_complete', '').lower() != 'true':
                        continue

                    py_ver = row.get('python_version', '')
                    modules_str = row.get('python_modules', '{}')
                    
                    try:
                        modules = json.loads(modules_str.replace("'", '"'))
                    except (json.JSONDecodeError, ValueError):
                        continue

                    if not modules or not py_ver:
                        continue

                    pkg_names = set()
                    for name in modules.keys():
                        clean = name.strip().lower()
                        if clean and len(clean) > 1:
                            pkg_names.add(clean)

                    # Build co-occurrence matrix
                    for pkg in pkg_names:
                        for other in pkg_names:
                            if pkg != other:
                                self.cooccurrence[pkg][other] += 1

                    # Store successful combos
                    if pkg_names:
                        self.success_combos.append({
                            'python_version': py_ver,
                            'packages': dict(modules),
                            'package_set': pkg_names,
                        })

            if self.logging:
                print(f"  [CoMiner] Mined {len(self.cooccurrence)} package co-occurrence patterns "
                      f"from {len(self.success_combos)} successful runs", flush=True)

        except Exception as e:
            if self.logging:
                print(f"  [CoMiner] Error loading results: {e}", flush=True)

    def predict_missing_packages(self, known_packages: List[str],
                                  threshold: int = 3) -> List[str]:
        """
        Given known packages, predict what other packages are likely needed.
        Uses co-occurrence frequency from historical data.
        """
        predictions = Counter()
        known_lower = {p.lower() for p in known_packages}

        for pkg in known_lower:
            if pkg in self.cooccurrence:
                for cooccur, count in self.cooccurrence[pkg].items():
                    if cooccur not in known_lower and count >= threshold:
                        predictions[cooccur] += count

        # Return packages sorted by frequency, excluding already-known
        result = [pkg for pkg, _ in predictions.most_common(5)
                  if pkg not in known_lower]
        return result

    def get_group_template(self, modules: List[str],
                           python_version: str) -> Optional[Dict[str, str]]:
        """
        Match modules against known dependency group templates.
        Returns version-pinned packages if a template matches.
        
        This is the key "Skill Library" concept from Voyager:
        pre-built, tested, reusable dependency configurations.
        """
        modules_lower = {m.lower() for m in modules}

        best_match = None
        best_overlap = 0

        for group_name, group in self.DEPENDENCY_GROUPS.items():
            trigger_lower = {t.lower() for t in group['trigger']}
            overlap = len(modules_lower & trigger_lower)
            
            if overlap > 0 and overlap > best_overlap:
                # Find best matching Python version
                ver_key = python_version
                if ver_key not in group['packages']:
                    # Try closest version
                    for fallback in [python_version, '3.7', '3.6', '2.7', '3.8']:
                        if fallback in group['packages']:
                            ver_key = fallback
                            break
                
                if ver_key in group['packages']:
                    best_match = {
                        'group': group_name,
                        'packages': dict(group['packages'][ver_key]),
                        'python_version': ver_key,
                    }
                    best_overlap = overlap

        return best_match

    def get_version_for_package(self, package: str,
                                 python_version: str,
                                 copackages: List[str] = None) -> Optional[str]:
        """
        Get the most commonly successful version for a package,
        given a Python version and optional co-packages for context.
        
        Uses historical success data, NOT LLM.
        """
        package_lower = package.lower()
        copackages_lower = {p.lower() for p in (copackages or [])}

        version_counts = Counter()
        
        for combo in self.success_combos:
            if combo['python_version'] != python_version:
                continue
            
            for pkg_name, version in combo['packages'].items():
                if pkg_name.lower() == package_lower and version:
                    # Boost score if co-packages match
                    if copackages_lower:
                        overlap = len(copackages_lower & combo['package_set'])
                        score = 1 + overlap
                    else:
                        score = 1
                    version_counts[version] += score

        if version_counts:
            best_version = version_counts.most_common(1)[0][0]
            return best_version
        
        return None

    def find_similar_snippet(self, modules: List[str],
                              python_version: str) -> Optional[Dict]:
        """
        Find the most similar successful snippet configuration.
        Uses Jaccard similarity on package sets.
        
        Novel: "Nearest neighbor resolution" - find the closest
        historically successful configuration.
        """
        modules_lower = {m.lower() for m in modules}
        if not modules_lower:
            return None

        best_match = None
        best_similarity = 0.0

        for combo in self.success_combos:
            if combo['python_version'] != python_version:
                continue

            pkg_set = combo['package_set']
            if not pkg_set:
                continue

            # Jaccard similarity
            intersection = len(modules_lower & pkg_set)
            union = len(modules_lower | pkg_set)
            similarity = intersection / union if union > 0 else 0

            if similarity > best_similarity and similarity >= 0.3:
                best_similarity = similarity
                best_match = {
                    'packages': combo['packages'],
                    'similarity': similarity,
                    'python_version': combo['python_version'],
                }

        return best_match

    def get_ecosystem_packages(self, modules: List[str]) -> Dict[str, str]:
        """
        Identify ecosystem-level dependencies that should be added.
        E.g., if tensorflow is imported, keras and numpy are likely needed.
        """
        modules_lower = {m.lower() for m in modules}
        additions = {}

        for group_name, group in self.DEPENDENCY_GROUPS.items():
            trigger_lower = {t.lower() for t in group['trigger']}
            if modules_lower & trigger_lower:
                # Found a matching group
                for ver_key in ['3.7', '3.6', '2.7', '3.8']:
                    if ver_key in group['packages']:
                        for pkg, ver in group['packages'][ver_key].items():
                            pkg_lower = pkg.lower()
                            if pkg_lower not in modules_lower and pkg_lower not in additions:
                                additions[pkg] = ver
                        break

        return additions
