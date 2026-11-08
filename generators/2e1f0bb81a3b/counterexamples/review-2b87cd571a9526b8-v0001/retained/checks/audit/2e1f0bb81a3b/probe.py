"""Findings-only source-bound control and two geometric-rival probes."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
TASK = "2e1f0bb81a3b"
EXPECTED_SHA = "fe58e2a9e06f89a589b35b961d9efbc172e8aa310228300f58afed9ff617dec0"


def write(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2) + "\n")


def generator():
    path = REPO / "generators" / TASK / "generator.py"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == EXPECTED_SHA
    sys.path.insert(0, str(REPO / "shared" / "runtime"))
    spec = importlib.util.spec_from_file_location("audited_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def crop(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    top, bottom = min(r for r, c in cells), max(r for r, c in cells)
    left, right = min(c for r, c in cells), max(c for r, c in cells)
    return [row[left:right + 1] for row in grid[top:bottom + 1]]


def output(grid, transform="lr"):
    obj = crop(grid)
    if transform == "lr":
        other = [row[::-1] for row in obj]
    elif transform == "ud":
        other = obj[::-1]
    elif transform == "rotate180":
        other = [row[::-1] for row in obj[::-1]]
    else:
        raise ValueError(transform)
    return [row + [0] + extra for row, extra in zip(obj, other)]


def prepare():
    module = generator()
    baseline = module.generate(0, 0, difficulty="medium")
    colors = sorted({v for row in baseline for v in row if v})
    requested = 2 if colors != [2] else 3
    overridden = module.generate(0, 0, difficulty="medium", color=requested)
    assert overridden == baseline
    assert colors != [requested]
    errors = module.self_check(overridden, difficulty="medium")
    assert errors == []
    obj = crop(overridden)
    assert obj != [row[::-1] for row in obj]
    write("control-input.json", overridden)
    write("control-probe.json", {
        "seed": 0, "sample_index": 0, "difficulty": "medium", "overrides": {"color": requested},
        "baseline_overrides": {}, "baseline_input": baseline, "input": overridden,
        "requested_color": requested, "observed_foreground_colors": colors,
        "identical_to_no_override": True, "self_check_errors": errors,
        "lawful_ordinary_domain": True,
        "domain_reason": "One connected, single-color, non-LR-symmetric nonempty blob on background zero, produced by the unmodified ordinary medium generator.",
        "python_rule_output": output(overridden),
    })
    # A bounded first-witness search tests just two natural geometric substitutes.
    attempted = 0
    hit = None
    for seed in range(64):
        grids = [module.generate(seed, index, difficulty="medium") for index in range(4)]
        attempted += 4
        for rival in ("ud", "rotate180"):
            same = [output(grid, rival) == output(grid) for grid in grids]
            if same == [True, True, True, False]:
                hit = {"seed": seed, "difficulty": "medium", "sample_indices": [0, 1, 2, 3],
                       "overrides": {}, "rival": rival, "rival_matches": same,
                       "inputs": grids, "python_rule_outputs": [output(g) for g in grids],
                       "rival_outputs": [output(g, rival) for g in grids],
                       "self_check_errors": [module.self_check(g, difficulty="medium") for g in grids]}
                break
        if hit:
            break
    write("rival-search.json", {"seeds_considered": list(range(attempted // 4)),
          "sample_indices": [0, 1, 2, 3], "difficulty": "medium", "candidate_generator_calls": attempted,
          "rivals": ["ud", "rotate180"], "stop_policy": "First 3-demo-fit / query-disagreement witness, at most 64 seeds.",
          "authority_basis_at_selection": "Local Python crop-and-LR mirror, pending public Racket verification if a witness is found.",
          "found": hit})
    if hit:
        assert not any(hit["self_check_errors"])
        write("input.json", hit["inputs"][-1])
        write("rival_output.json", hit["rival_outputs"][-1])
    else:
        write("input.json", overridden)
    print(json.dumps({"control_requested": requested, "control_observed": colors,
                      "control_self_check": errors, "rival_search_samples": attempted,
                      "rival_hit": None if hit is None else {k:hit[k] for k in ("seed", "rival", "rival_matches")}}))


if __name__ == "__main__":
    prepare()
