#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

REPO = Path.cwd()
EVIDENCE = REPO.parent / "checks" / "parametric" / "selector-role-v1_1"
PROTOTYPE = REPO / "generators" / "ef02aedbac38" / "workspace" / "parametric" / "prototype.py"

spec = importlib.util.spec_from_file_location("ef02_public_evidence_probe", PROTOTYPE)
assert spec is not None and spec.loader is not None
prototype = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = prototype
spec.loader.exec_module(prototype)

report = json.loads((EVIDENCE / "report.json").read_text(encoding="utf-8"))
manifest = json.loads((EVIDENCE / "manifest.json").read_text(encoding="utf-8"))
assert report["episode_shape"] == {"demo_count": 3, "query_count": 4}
assert hashlib.sha256((EVIDENCE / "report.json").read_bytes()).hexdigest() == manifest["report_sha256"]

public_receipts = []
for setting, row in sorted(report["episodes"].items()):
    public_path = EVIDENCE / row["public_path"]
    private_path = EVIDENCE / row["private_path"]
    public_bytes = public_path.read_bytes()
    digest = hashlib.sha256(public_bytes).hexdigest()
    assert public_path.name == f"challenge-{digest}.json"
    challenge = json.loads(public_bytes)
    assert len(challenge["train"]) == 3
    assert len(challenge["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    serialized = public_bytes.decode("utf-8")
    assert "selector_role" not in serialized
    assert "episode_seed" not in serialized
    assert "query_answers" not in serialized
    input_keys = [
        json.dumps(pair["input"], sort_keys=True, separators=(",", ":"))
        for pair in challenge["train"] + challenge["test"]
    ]
    assert len(set(input_keys)) == 7
    private = json.loads(private_path.read_text(encoding="utf-8"))
    assert private["checks"]["demo_count"] == 3
    assert private["checks"]["query_count"] == 4
    assert private["checks"]["requested_counts_match"] is True
    assert private["checks"]["all_episode_inputs_distinct"] is True
    assert private["checks"]["queries_distinguish_rival"] is True
    public_receipts.append(
        {
            "setting": setting,
            "public_path": row["public_path"],
            "sha256": digest,
            "visible_pairs": 7,
            "distinct_inputs": 7,
        }
    )

base = {
    "meta": {"selector_role": "five", "episode_seed": 0},
    "train": [{"input": [[5, 2]], "output": [[2, 0]]}],
    "test": [{"input": [[2, 5]], "output": [[0, 2]]}],
}
base_id = prototype.public_filename(base)
private_mutation = deepcopy(base)
private_mutation["meta"] = {"selector_role": "companion", "episode_seed": 99}
private_mutation["test"][0]["output"] = [[5, 0]]
assert prototype.public_filename(private_mutation) == base_id
visible_mutation = deepcopy(base)
visible_mutation["train"][0]["output"] = [[0, 5]]
assert prototype.public_filename(visible_mutation) != base_id

invalid_grid = deepcopy(base)
invalid_grid["train"][0]["input"] = [[True, 2]]
try:
    prototype.public_filename(invalid_grid)
except ValueError as error:
    invalid_grid_error = str(error)
else:
    raise AssertionError("boolean ARC cell was accepted by public identifier")

preflight_receipts = []
with tempfile.TemporaryDirectory() as temp:
    temp = Path(temp)
    cases = [
        ("zero_demo", {"demo_count": 0, "query_count": 4}),
        ("bool_demo", {"demo_count": True, "query_count": 4}),
        ("too_many_queries", {"demo_count": 3, "query_count": 5}),
        ("duplicate_setting_seed", {"seeds": (0, 2, 1), "demo_count": 3, "query_count": 4}),
    ]
    for name, kwargs in cases:
        destination = temp / name
        try:
            prototype.write_evidence(destination, **kwargs)
        except ValueError as error:
            assert not destination.exists()
            preflight_receipts.append({"case": name, "error": str(error), "created_output": False})
        else:
            raise AssertionError(f"invalid preflight case accepted: {name}")

result = {
    "schema": "ef02aedbac38-public-evidence-adversarial-v1",
    "status": "passed",
    "surfaces": [
        "exact public byte identity and private-field redaction",
        "count/seed/numeric-type preflight boundaries",
    ],
    "public_receipts": public_receipts,
    "identity_mutation": {
        "private_metadata_and_query_answer_preserve_id": True,
        "visible_demo_output_changes_id": True,
        "boolean_cell_rejected": invalid_grid_error,
    },
    "preflight_receipts": preflight_receipts,
    "limits": [
        "bounded to retained seeds 0 and 1 and declared selector-role rival",
        "does not exclude arbitrary competing programs",
    ],
}
print(json.dumps(result, indent=2, sort_keys=True))
