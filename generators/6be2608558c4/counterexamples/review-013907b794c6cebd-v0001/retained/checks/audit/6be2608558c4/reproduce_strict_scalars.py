from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = '6be2608558c4'
CASES = [{'name': 'bool_seed', 'call': 'generate', 'kwargs': {'seed': True, 'sample_index': 0, 'difficulty': 'easy'}, 'expected': 'reject'}, {'name': 'float_seed', 'call': 'generate', 'kwargs': {'seed': 1.0, 'sample_index': 0, 'difficulty': 'easy'}, 'expected': 'reject'}, {'name': 'negative_sample_index', 'call': 'generate', 'kwargs': {'seed': 991, 'sample_index': -1, 'difficulty': 'easy'}, 'expected': 'reject'}, {'name': 'invalid_difficulty', 'call': 'generate', 'kwargs': {'seed': 991, 'sample_index': 0, 'difficulty': '__invalid_difficulty__'}, 'expected': 'reject'}, {'name': 'schedule_negative_sample_index', 'call': 'schedule_profile', 'kwargs': {'seed': 991, 'sample_index': -1, 'difficulty': 'easy'}, 'expected': 'reject'}, {'name': 'schedule_bool_seed', 'call': 'schedule_profile', 'kwargs': {'seed': True, 'sample_index': 0, 'difficulty': 'easy'}, 'expected': 'reject'}]


def load_module():
    source = Path("generators") / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def json_hash(value) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def run_case(module, row):
    kind = row["call"]
    kwargs = row["kwargs"]
    try:
        if kind == "generate":
            value = module.generate(
                kwargs["seed"],
                kwargs["sample_index"],
                difficulty=kwargs.get("difficulty"),
            )
            result = {
                "status": "accepted",
                "output_type": type(value).__name__,
                "shape": [len(value), len(value[0])],
                "grid_sha256": json_hash(value),
                "self_check": module.self_check(value),
            }
        elif kind == "schedule_profile":
            value = module.schedule_profile(
                kwargs["seed"],
                kwargs["sample_index"],
                difficulty=kwargs.get("difficulty"),
            )
            result = {
                "status": "accepted",
                "output_type": type(value).__name__,
                "value": value,
            }
        else:
            raise AssertionError(kind)
    except Exception as exc:
        result = {
            "status": "raised",
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }
    return {**row, "result": result}


def main():
    module, source = load_module()
    rows = [run_case(module, row) for row in CASES]
    payload = {
        "schema": "arcpuzzles-audit-strict-scalars-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "command": ["python3", f"../checks/audit/{TASK_ID}/reproduce_strict_scalars.py"],
        "cwd": str(Path.cwd()),
        "expectation": "Every case marked expected=reject should raise TypeError or ValueError.",
        "cases": rows,
        "defect_reproduced": any(
            row.get("expected") == "reject" and row["result"]["status"] == "accepted"
            for row in rows
        ),
    }
    out = Path("../checks/audit") / TASK_ID / "strict-scalars-reproduction.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "task_id": TASK_ID,
        "defect_reproduced": payload["defect_reproduced"],
        "accepted_invalid": sum(
            row.get("expected") == "reject" and row["result"]["status"] == "accepted"
            for row in rows
        ),
        "out": str(out),
    }, indent=2))


if __name__ == "__main__":
    main()
