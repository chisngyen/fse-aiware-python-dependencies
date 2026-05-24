"""Method registry. Every method = ONE .py file with class ``Method``.

The harness discovers methods by importing the file path passed via
``--method``. There is no class registration step — naming the file
and exporting ``Method`` is the entire contract.
"""
