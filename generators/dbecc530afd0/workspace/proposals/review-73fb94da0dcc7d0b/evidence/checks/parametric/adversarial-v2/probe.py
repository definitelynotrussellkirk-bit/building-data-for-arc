#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "dbecc530afd0"
HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
EVIDENCE = ROOT.parent / "checks" / "parametric" / "inset-depth-v2"

spec = importlib.util.spec_from_file_location("dbecc_adversarial_prototype", PROTOTYPE_PATH)
assert spec is not None and spec.loader is not None
prototype = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)
generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=ROOT)

sampler_cases = [(1, 1), (1, 8), (8, 1), (8, 4), (4, 8)]
validated_inputs = 0
for seed in range(16):
    for demo_count, query_count in sampler_cases:
        prototype.validate_counts(demo_count, query_count)
        grids = prototype.generate_inputs(seed, demo_count + query_count)
        identities = [json.dumps(grid, separators=(",", ":")) for grid in grids]
        assert len(grids) == demo_count + query_count
        assert len(identities) == len(set(identities))
        for grid in grids:
            assert generator.self_check(grid) == []
            validated_inputs += 1

invalid_cases = [(True, 4), (3, False), (0, 4), (3, 0), (100, 1), (1, 100), (8, 8)]
rejected = 0
for case in invalid_cases:
    try:
        prototype.validate_counts(*case)
    except ValueError:
        rejected += 1
    else:
        raise AssertionError(f"invalid count case accepted: {case}")

privacy_checks = []
for private_path in sorted((EVIDENCE / "private" / "episodes").glob("*.json")):
    episode = json.loads(private_path.read_text(encoding="utf-8"))
    public = prototype.public_challenge(episode)
    public_id = public_challenge_id(public)
    public_path = EVIDENCE / "public" / f"challenge-{public_id}.json"
    assert public_path.is_file()
    assert public_path.read_bytes() == public_challenge_bytes(public)

    private_only = deepcopy(episode)
    private_only["seed"] = 10_000 + episode["seed"]
    private_only["parameters"] = {"inset_depth": 99}
    private_only["racket_program"] = "not public"
    demo_count = episode["counts"]["demonstrations"]
    for pair in private_only["pairs"][demo_count:]:
        pair["output"] = [[9]]
    assert public_challenge_id(prototype.public_challenge(private_only)) == public_id

    visible_change = deepcopy(episode)
    cell = visible_change["pairs"][demo_count]["input"][0][0]
    visible_change["pairs"][demo_count]["input"][0][0] = (cell + 1) % 10
    assert public_challenge_id(prototype.public_challenge(visible_change)) != public_id
    privacy_checks.append(
        {
            "public_id": public_id,
            "canonical_bytes": len(public_path.read_bytes()),
            "private_and_query_answer_mutation_preserved_id": True,
            "query_input_mutation_changed_id": True,
        }
    )

result = {
    "status": "passed",
    "surfaces": {
        "sampler_boundaries": {
            "seeds": 16,
            "count_cases": [list(case) for case in sampler_cases],
            "validated_inputs": validated_inputs,
            "all_distinct_within_episode": True,
            "all_passed_production_self_check": True,
            "invalid_count_cases_rejected": rejected,
        },
        "public_private_export": {
            "episodes_checked": len(privacy_checks),
            "checks": privacy_checks,
            "public_files_use_canonical_visible_bytes": True,
        },
    },
    "bindings": {
        "prototype_path": str(PROTOTYPE_PATH.relative_to(ROOT)),
        "prototype_sha256": hashlib.sha256(PROTOTYPE_PATH.read_bytes()).hexdigest(),
        "generator_path": str(generator_path.relative_to(ROOT)),
        "generator_sha256": generator_sha,
        "evidence_report_sha256": hashlib.sha256((EVIDENCE / "report.json").read_bytes()).hexdigest(),
    },
    "limits": "Finite seeds/count edges and two retained episodes; no exhaustive sampler proof.",
}
(Path(__file__).with_name("result.json")).write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(result, sort_keys=True))
