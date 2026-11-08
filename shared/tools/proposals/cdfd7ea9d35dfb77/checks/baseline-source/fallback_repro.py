from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

BASELINE = Path(__file__).with_name("generator.py")
spec = importlib.util.spec_from_file_location("baseline_9e47b59d6afc", BASELINE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module._free = lambda *args, **kwargs: False
returned = module.generate(0, 0, difficulty="medium")
report = {
    "task_id": "9e47b59d6afc",
    "baseline_generator_sha256": hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
    "probe": "force every placement attempt to fail by replacing _free with a false predicate",
    "call": {"seed": 0, "sample_index": 0, "difficulty": "medium"},
    "generate_returned_instead_of_raising": True,
    "dimensions": [len(returned), len(returned[0])],
    "nonzero_cells": sum(value != 0 for row in returned for value in row),
    "self_check_errors": module.self_check(returned),
}
print(json.dumps(report, indent=2, sort_keys=True))
