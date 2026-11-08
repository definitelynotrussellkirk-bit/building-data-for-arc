"""Reproduce call-level scalar coercion in one selected generator."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

REPO = Path.cwd().resolve()
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import load_selected_generator  # noqa: E402

TASK_ID = "1bc816e1eb99"
OUT = REPO.parent / "checks/audit/1bc816e1eb99/strict_scalar.json"


def digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


module, source, source_hash = load_selected_generator(TASK_ID, root=REPO)
probes = [
    ("valid_baseline", (0, 0), {"difficulty": "hard"}),
    ("bool_seed", (True, 0), {"difficulty": "hard"}),
    ("float_seed", (1.5, 0), {"difficulty": "hard"}),
    ("string_seed", ("1", 0), {"difficulty": "hard"}),
    ("bool_sample_index", (0, True), {"difficulty": "hard"}),
    ("float_sample_index", (0, 1.5), {"difficulty": "hard"}),
    ("string_sample_index", (0, "1"), {"difficulty": "hard"}),
    ("negative_sample_index", (0, -1), {"difficulty": "hard"}),
]
records = []
for name, args, kwargs in probes:
    try:
        value = module.generate(*args, **kwargs)
    except Exception as exc:  # evidence records either disposition
        records.append({
            "name": name,
            "args": list(args),
            "arg_types": [type(arg).__name__ for arg in args],
            "kwargs": kwargs,
            "status": "rejected",
            "exception_type": type(exc).__name__,
            "exception": str(exc),
        })
    else:
        records.append({
            "name": name,
            "args": list(args),
            "arg_types": [type(arg).__name__ for arg in args],
            "kwargs": kwargs,
            "status": "accepted",
            "output_shape": [len(value), len(value[0])],
            "output_sha256": digest(value),
            "self_check_errors": module.self_check(value, difficulty=kwargs["difficulty"]),
        })

report = {
    "schema": "audit-strict-scalar-probe-v1",
    "task_id": TASK_ID,
    "generator_path": source.relative_to(REPO).as_posix(),
    "generator_sha256": source_hash,
    "command": ["python3", "review.py", "run", "python3", "../checks/audit/1bc816e1eb99/strict_scalar_probe.py"],
    "cwd": "packet_root",
    "expectation": "seed and sample_index should reject bool, non-integral/string scalars, and negative sample_index before generation",
    "records": records,
}
OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
