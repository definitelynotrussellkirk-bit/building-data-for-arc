from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
sys.path.insert(0, str(ROOT / "shared" / "runtime"))
SOURCE = ROOT / "generators" / "3ef0261e0888" / "generator.py"
spec = importlib.util.spec_from_file_location("audit_3ef0261e0888", SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def digest(grid):
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()

blank = module.generate(0, 0, texture="blank_interior")
default = module.generate(0, 0)
warm = module.generate(0, 0, texture="warm")
result = {
    "task_id": module.TASK_ID,
    "blank_interior_is_advertised_valid": "blank_interior" in module.AXES["texture"]["valid"],
    "blank_interior_self_check": module.self_check(blank),
    "blank_interior_grid": blank,
    "ignored_helpful_texture": {
        "default_sha256": digest(default),
        "warm_sha256": digest(warm),
        "byte_identical": default == warm,
    },
}
print(json.dumps(result, indent=2))
