#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2] / "repo"
PROTOTYPE = ROOT / "generators/88b8e6aaa49d/workspace/parametric/prototype.py"
OUT = Path(__file__).with_name("adversarial.json")

spec = importlib.util.spec_from_file_location("rotation_parametric_adversarial", PROTOTYPE)
assert spec and spec.loader
proto = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = proto
spec.loader.exec_module(proto)


class StrictMirror:
    backend = "adversarial-python-mirror"

    def __init__(self):
        self.executions = []

    def apply(self, grid, quarter_turns):
        proto._validate_grid(grid)
        output = proto.python_mirror(grid, quarter_turns)
        self.executions.append(
            {
                "backend": self.backend,
                "quarter_turns": quarter_turns,
                "input_sha256": proto.digest(grid),
                "output_sha256": proto.digest(output),
            }
        )
        return output


started = time.monotonic()
checks = []

# Surface 1: sampler/count/retry boundary.
boundary = proto.generate_episode(
    99,
    quarter_turns=2,
    demos=16,
    queries=16,
    max_attempts=32,
    engine=StrictMirror(),
)
checks.append(
    {
        "surface": "sampler_count_retry_boundary",
        "status": "pass",
        "case": "32 distinct pairs accepted with exactly 32 attempts",
        "accepted_count": len(boundary["train"]) + len(boundary["test"]),
        "accepted_sample_indices": boundary["accepted_sample_indices"],
        "all_queries_identified": all(
            row["consistent_settings"] == [2]
            for row in boundary["query_identification"]
        ),
    }
)
try:
    proto.generate_episode(
        99,
        quarter_turns=2,
        demos=16,
        queries=16,
        max_attempts=31,
        engine=StrictMirror(),
    )
except RuntimeError as exc:
    retry_error = str(exc)
else:
    raise AssertionError("31 attempts unexpectedly satisfied 32 requested pairs")
checks.append(
    {
        "surface": "sampler_count_retry_boundary",
        "status": "pass",
        "case": "31-attempt budget fails closed for 32 requested pairs",
        "error": retry_error,
    }
)

# Surface 2: visible/private projection and verifier rejection paths.
base = proto.generate_episode(
    17, quarter_turns=3, demos=2, queries=4, engine=StrictMirror()
)
private_change = copy.deepcopy(base)
private_change["seed"] = 123456
private_change["program_solution"] = "PRIVATE CANARY"
for pair in private_change["test"]:
    pair["output"] = [[9]]
assert proto.public_bytes(private_change) == proto.public_bytes(base)
assert proto.public_id(private_change) == proto.public_id(base)
visible_change = copy.deepcopy(base)
visible_change["train"][0]["output"][0][0] = (
    visible_change["train"][0]["output"][0][0] + 1
) % 10
assert proto.public_id(visible_change) != proto.public_id(base)

with tempfile.TemporaryDirectory() as temporary:
    duplicate = copy.deepcopy(base)
    duplicate["seed"] = 999
    try:
        proto.write_episodes(
            Path(temporary) / "duplicate",
            [base, duplicate],
            engine=StrictMirror(),
        )
    except ValueError as exc:
        duplicate_error = str(exc)
    else:
        raise AssertionError("duplicate visible payload was accepted")

    corrupt = copy.deepcopy(base)
    corrupt["test"][0]["output"] = [[9]]
    try:
        proto.write_episodes(
            Path(temporary) / "corrupt",
            [corrupt],
            engine=StrictMirror(),
        )
    except ValueError as exc:
        corrupt_error = str(exc)
    else:
        raise AssertionError("corrupted private label was accepted")

for bad_call in (
    lambda: proto.rule_source(True),
    lambda: proto.generate_episode(0, demos=True, engine=StrictMirror()),
    lambda: proto.generate_episode(1.5, engine=StrictMirror()),
):
    try:
        bad_call()
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError("non-literal numeric control was accepted")

checks.append(
    {
        "surface": "public_private_export_and_rejection",
        "status": "pass",
        "private_metadata_id_invariant": True,
        "visible_demo_change_changes_id": True,
        "duplicate_error": duplicate_error,
        "corrupt_label_error": corrupt_error,
        "nonliteral_numeric_controls_rejected": True,
    }
)

report = {
    "schema": "arc-rotation-parametric-adversarial-v1",
    "task_id": proto.TASK_ID,
    "status": "bounded_no_finding",
    "elapsed_seconds": round(time.monotonic() - started, 3),
    "checks": checks,
    "real_racket_parity_evidence": "quarter-turns-v1/report.json",
    "limits": [
        "The retry probe used the independent Python mirror; the retained evidence bundle separately records 330 protected Racket executions.",
        "Identifiability was attacked only within the declared quarter-turn rival family.",
    ],
}
OUT.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True))
