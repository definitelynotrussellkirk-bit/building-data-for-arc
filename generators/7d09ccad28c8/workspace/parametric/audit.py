"""Bounded source-local audit for the keyed-ray parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load_family():
    path = HERE / "family.py"
    spec = importlib.util.spec_from_file_location("_audit_route_family", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run() -> dict:
    family = _load_family()
    settings = ({"route_mode": "straight"}, {"route_mode": "clockwise_elbow"})
    episodes = 0
    pairs = 0
    wrong_intermediate_disagreements = 0
    keys: set[int] = set()
    sizes: set[tuple[int, int]] = set()
    max_nonzero = 0
    first_lengths: list[int] = []
    second_lengths: list[int] = []

    for seed in range(12):
        baseline = family.generate(seed, settings[0], 6, 4)
        alternate = family.generate(seed, settings[1], 6, 4)
        assert [p["input"] for s in ("train", "test") for p in baseline[s]] == [
            p["input"] for s in ("train", "test") for p in alternate[s]
        ]
        for demos in range(2, 7):
            for queries in range(1, 5):
                generated = [family.generate(seed, setting, demos, queries) for setting in settings]
                episodes += len(generated)
                assert generated[0]["train"] == baseline["train"][:demos]
                assert generated[0]["test"] == baseline["test"][:queries]
                assert generated[1]["train"] == alternate["train"][:demos]
                assert generated[1]["test"] == alternate["test"][:queries]
                left_inputs = [p["input"] for s in ("train", "test") for p in generated[0][s]]
                right_inputs = [p["input"] for s in ("train", "test") for p in generated[1][s]]
                assert left_inputs == right_inputs
                assert len({json.dumps(grid, separators=(",", ":")) for grid in left_inputs}) == demos + queries

        for split in ("train", "test"):
            for straight_pair, elbow_pair in zip(baseline[split], alternate[split]):
                grid = straight_pair["input"]
                assert straight_pair["output"] == family.transform(grid, "straight")
                assert elbow_pair["output"] == family.transform(grid, "clockwise_elbow")
                assert straight_pair["output"] != elbow_pair["output"]
                wrong = family.transform_wrong_intermediate(grid)
                if wrong != elbow_pair["output"]:
                    wrong_intermediate_disagreements += 1
                analysis = family.route_analysis(grid)
                assert analysis
                for frame in analysis:
                    keys.add(frame["key"][2])
                    first_lengths.append(len(frame["first_leg"]))
                    second_lengths.append(len(frame["second_leg"]))
                sizes.add((len(grid), len(grid[0])))
                max_nonzero = max(max_nonzero, sum(cell != 0 for row in grid for cell in row))
                pairs += 1

    assert keys == {1, 2, 3, 4}
    assert min(first_lengths) >= 1 and min(second_lengths) >= 1
    assert wrong_intermediate_disagreements == pairs
    assert (30, 30) in sizes and max_nonzero >= 150
    sources = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(HERE.iterdir())
        if path.is_file() and path.suffix in {".py", ".rkt", ".json"}
    }
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": family.TASK_ID,
        "status": "passed",
        "seeds": 12,
        "episodes_checked": episodes,
        "pairs_checked": pairs,
        "supported_counts": {"demos": [2, 6], "queries": [1, 4]},
        "setting_independent_inputs": True,
        "prefix_stable_streams": True,
        "all_pairs_distinguish_settings": True,
        "wrong_intermediate_disagreements": wrong_intermediate_disagreements,
        "keys_seen": sorted(keys),
        "sizes_seen": [list(size) for size in sorted(sizes)],
        "max_input_nonzero_cells": max_nonzero,
        "limits": "Finite deterministic audit; protected Racket parity is established separately by authoring preflight.",
        "sources": sources,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "episodes_checked", "pairs_checked")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
