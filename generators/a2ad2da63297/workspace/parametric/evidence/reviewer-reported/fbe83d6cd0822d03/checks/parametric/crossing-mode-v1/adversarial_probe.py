#!/usr/bin/env python3
"""Bounded independent attack on crossing-mode parity and export boundaries."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
PROTOTYPE = ROOT / "generators/a2ad2da63297/workspace/parametric/prototype.py"
EVIDENCE = HERE / "evidence"
RESULT = HERE / "adversarial-result.json"

spec = importlib.util.spec_from_file_location("a2ad2da63297_parametric_probe", PROTOTYPE)
assert spec and spec.loader
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

# Surface 1: Racket/Python parity, including irregular canonical walls and sampler boundaries.
canonical = canonical_pairs(p.TASK_ID, root=ROOT, labeled_only=True)
canonical_inputs = [pair["input"] for pair in canonical]
generator, _, _ = p.load_selected_generator(p.TASK_ID, root=ROOT)
generated = []
roles = []
for orientation in ("horizontal", "vertical"):
    for pair_count in (2, 4):
        for difficulty in ("easy", "hard"):
            for seed in range(3):
                grid = generator.generate(
                    seed + (100 if orientation == "vertical" else 0),
                    seed * 17 + pair_count,
                    difficulty=difficulty,
                    texture=orientation,
                    pair_count=pair_count,
                )
                assert generator.self_check(grid, difficulty=difficulty) == []
                generated.append(grid)
                roles.append({
                    "orientation": orientation,
                    "pair_count": pair_count,
                    "difficulty": difficulty,
                    "seed": seed,
                })
all_inputs = canonical_inputs + generated
parity = {}
with RacketBridge(max_calls_before_restart=256) as bridge:
    for mode in p.ALLOWED_MODES:
        program = p.materialize_rule(mode, root=ROOT)
        racket = p.execute_rule_many(program, all_inputs, bridge=bridge, root=ROOT)
        python = [p.python_prediction(grid, mode) for grid in all_inputs]
        mismatches = [index for index, (a, b) in enumerate(zip(racket, python, strict=True)) if a != b]
        parity[mode] = {
            "input_count": len(all_inputs),
            "canonical_irregular_count": len(canonical_inputs),
            "generated_boundary_count": len(generated),
            "mismatches": mismatches,
        }
        assert not mismatches

# Surface 2: public/private separation, exact IDs, and numeric rejection.
public_rows = []
for path in sorted((EVIDENCE / "public").glob("challenge-*.json")):
    raw = path.read_bytes()
    data = json.loads(raw)
    expected = public_challenge_bytes(data)
    expected_id = public_challenge_id(data)
    assert raw == expected
    assert path.name == f"challenge-{expected_id}.json"
    assert all(set(pair) == {"input"} for pair in data["test"])
    text = raw.decode("utf-8")
    forbidden = [
        "crossing_mode", "cross_through", "compress_to_barrier", "query_answers",
        '"seed"', "program_sha256", "937e30cc",
    ]
    leaked = [token for token in forbidden if token in text]
    assert not leaked
    public_rows.append({"file": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "leaked": leaked})

private_paths = sorted((EVIDENCE / "private/episodes").glob("*.json"))
assert len(private_paths) == len(public_rows) == 2
for private_path in private_paths:
    private = json.loads(private_path.read_text())
    public_path = EVIDENCE / "public" / f"challenge-{private['public_id']}.json"
    public = json.loads(public_path.read_text())
    baseline = public_challenge_id(public)
    # These private changes must have no route into the visible identifier.
    private["seed"] += 999
    private["parameter"] = {"crossing_mode": "tampered_private_only"}
    private["query_answers"] = []
    assert public_challenge_id(public) == baseline
    # A visible label change must change the identifier.
    changed = json.loads(json.dumps(public))
    changed["train"][0]["output"][0][0] = (changed["train"][0]["output"][0][0] + 1) % 10
    assert public_challenge_id(changed) != baseline

numeric_rejections = {}
valid = json.loads((sorted((EVIDENCE / "public").glob("challenge-*.json"))[0]).read_text())
for label, replacement in (("bool", True), ("float", 1.0), ("out_of_range", 10)):
    bad = json.loads(json.dumps(valid))
    bad["train"][0]["input"][0][0] = replacement
    try:
        public_challenge_bytes(bad)
    except ValueError as exc:
        numeric_rejections[label] = str(exc)
    else:
        raise AssertionError(f"public serializer accepted {label} cell")

result = {
    "schema": "a2ad2da63297-crossing-mode-adversarial-v1",
    "status": "bounded_no_finding",
    "surfaces": ["parameter/Racket parity", "public/private export and numeric types"],
    "parity": parity,
    "generated_roles": roles,
    "public_files": public_rows,
    "private_mutation_public_id_stable": True,
    "visible_mutation_public_id_changed": True,
    "numeric_rejections": numeric_rejections,
    "limits": [
        "24 generated boundary inputs plus the four canonical irregular inputs",
        "two retained public challenges only",
        "finite inspection; no claim beyond the tested source and runtime hashes",
    ],
}
RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
