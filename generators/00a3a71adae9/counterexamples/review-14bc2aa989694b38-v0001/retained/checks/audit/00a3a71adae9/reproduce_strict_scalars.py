#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
REPO = HERE.parents[3] / "repo"
sys.path[:0] = [str(REPO / "shared/runtime"), str(REPO / "src")]
from reviewer_support import load_selected_generator  # noqa: E402

TASK_ID = "00a3a71adae9"
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=REPO)


def digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def call(label: str, fn, *args, **kwargs) -> dict[str, object]:
    row: dict[str, object] = {"label": label, "args": list(args), "kwargs": kwargs}
    try:
        value = fn(*args, **kwargs)
    except Exception as exc:  # evidence records either outcome
        row.update(status="rejected", exception=type(exc).__name__, message=str(exc))
    else:
        row.update(status="accepted", value_sha256=digest(value))
        if isinstance(value, list):
            row["shape"] = [len(value), len(value[0]) if value else 0]
        else:
            row["value"] = value
    return row


cases = [
    call("generate_seed_bool", GEN.generate, True, 0, difficulty="easy"),
    call("generate_seed_float", GEN.generate, 1.75, 0, difficulty="easy"),
    call("generate_seed_string", GEN.generate, "1", 0, difficulty="easy"),
    call("generate_index_bool", GEN.generate, 991, True, difficulty="easy"),
    call("generate_index_float", GEN.generate, 991, 1.75, difficulty="easy"),
    call("generate_index_string", GEN.generate, 991, "1", difficulty="easy"),
    call("generate_index_negative", GEN.generate, 991, -1, difficulty="easy"),
    call("schedule_seed_float", GEN.schedule_profile, 1.75, 0, "easy"),
    call("schedule_index_float", GEN.schedule_profile, 991, 1.75, "easy"),
    call("schedule_index_negative", GEN.schedule_profile, 991, -1, "easy"),
]
control = {
    "seed_1": call("control_seed_1", GEN.generate, 1, 0, difficulty="easy"),
    "index_1": call("control_index_1", GEN.generate, 991, 1, difficulty="easy"),
}
report = {
    "schema": "arcpuzzles-audit-reproducer-v1",
    "task_id": TASK_ID,
    "generator_path": str(SOURCE.relative_to(REPO)),
    "generator_sha256": SOURCE_SHA256,
    "finding": "generate/schedule_profile accept non-literal integer seeds and sample indices; negative sample_index is also accepted",
    "expected_contract": "seed and sample_index are literal Python int values (not bool); sample_index >= 0",
    "command": ["PYTHONPATH=shared/runtime:src", "python3", "../checks/audit/00a3a71adae9/reproduce_strict_scalars.py"],
    "cwd": "repo",
    "cases": cases,
    "controls": control,
    "accepted_invalid_count": sum(row["status"] == "accepted" for row in cases),
}
out = HERE.with_name("strict_scalar_reproducer.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(out)
print(json.dumps({"accepted_invalid_count": report["accepted_invalid_count"], "generator_sha256": SOURCE_SHA256}, sort_keys=True))
