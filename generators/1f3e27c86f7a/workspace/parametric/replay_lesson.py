"""Reproduce the retained stripe-only lesson shortcut with current Racket labels."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from arcpuzzles.worker import lesson_check
from prototype import GENERATOR, GENERATOR_SHA256, RuleRunner, canonical_program


def stripe_only(grid):
    """Independent, narrow Python rival: stripe fallback or identity otherwise."""
    out = deepcopy(grid)
    if GENERATOR.observe_overrides(grid).get("rule_branch") != "stripe":
        return out
    for values in GENERATOR._stripe_candidates(grid):
        runs = GENERATOR._runs(values)
        middle = len(runs) // 2
        fixed = sum(count for i, (_, count) in enumerate(runs) if i != middle)
        for component in GENERATOR._components(grid):
            if component["color"] != values[0] or GENERATOR._has_inner(grid, component):
                continue
            row1, col1, row2, col2 = component["bbox"]
            middle_width = col2 - col1 + 1 - fixed
            if middle_width <= 0:
                continue
            fitted = [color for i, (color, count) in enumerate(runs)
                      for _ in range(middle_width if i == middle else count)]
            for row in range(row1, row2 + 1):
                out[row][col1:col2 + 1] = fitted
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise ValueError("Choose a new output directory")
    grids = [GENERATOR.generate(10, i, difficulty="medium") for i in range(5)]
    branches = [GENERATOR.observe_overrides(grid)["rule_branch"] for grid in grids]
    assert branches == ["stripe"] * 4 + ["bottom_align"]
    assert all(GENERATOR.self_check(grid) == [] for grid in grids)
    with RuleRunner() as runner:
        pairs = [{"input": grid, "output": runner.apply(grid)} for grid in grids]
    matches = [stripe_only(pair["input"]) == pair["output"] for pair in pairs]
    assert matches == [True] * 4 + [False]
    episode = {"train": pairs[:4], "test": pairs[4:]}
    verdict = lesson_check(GENERATOR, episode, {
        "demonstration_policy": {"automatic": False, "declared_minimum": 4}})
    assert verdict["status"] == "diagnostic_unsupported"
    try:
        lesson_check(GENERATOR, episode, {
            "demonstration_policy": {"automatic": True, "declared_minimum": 4}})
    except ValueError as exc:
        automatic_error = str(exc)
        assert "Automatic lesson unsupported" in automatic_error
    else:
        raise AssertionError("Automatic policy silently accepted the unsupported lesson")
    result = {
        "task_id": GENERATOR.TASK_ID, "seed": 10, "sample_indices": list(range(5)),
        "difficulty": "medium", "branches": branches, "individual_self_checks": "passed",
        "canonical_rule_hash": GENERATOR.RULE_HASH,
        "canonical_program_sha256": hashlib.sha256(canonical_program().encode()).hexdigest(),
        "generator_sha256": GENERATOR_SHA256,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rival_demo_and_query_matches": matches, "automatic_error": automatic_error,
        "explicit_verdict": verdict, "episode": episode,
        "query_rival_output": stripe_only(grids[-1]),
        "scope": "Exact retained five-input witness. Guard rejects unsupported branch coverage; no schedule guarantee.",
        "audit_disposition": "proposed_resolution_of_silent_admission; maintainer assessment still required",
    }
    args.out.mkdir(parents=True)
    (args.out / "witness.json").write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"rival_demo_matches": 4, "rival_query_disagrees": True,
                      "automatic_rejected": True, "explicit_status": verdict["status"],
                      "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
