"""Bounded author self-audit for the 138ffc14ac65 top-endpoint relay family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit(seeds=range(16)):
    seeds = tuple(seeds)
    family = _load(HERE / "prototype.py", "_bridge_family_audit")
    base = _load(HERE.parents[1] / "generator.py", "_bridge_base_audit")
    cases = 0
    prefixes = 0
    rival_checks = 0
    skip_a_changes = 0
    intervals_seen = set()
    large_bridge_counts = []
    for seed in seeds:
        episodes = {
            mode: family.generate(seed, {"finish_rule": mode}, 6, 4)
            for mode in family.MODES
        }
        default = episodes["up_only"]
        relay = episodes["equal_top_bridge"]
        assert [p["input"] for p in default["train"] + default["test"]] == [p["input"] for p in relay["train"] + relay["test"]]
        assert family.fit_settings(default["train"][:2]) == [{"finish_rule": "up_only"}]
        assert family.fit_settings(relay["train"][:2]) == [{"finish_rule": "equal_top_bridge"}]
        rivals = family.simple_rival_outputs(relay["train"][:2])
        gold = [p["output"] for p in relay["train"][:2]]
        assert all(outputs != gold for outputs in rivals.values())
        rival_checks += len(rivals)

        for demos in range(2, 7):
            short = family.generate(seed, {"finish_rule": "equal_top_bridge"}, demos, 4)
            assert short["train"] == relay["train"][:demos]
            prefixes += 1
        for queries in range(1, 5):
            short = family.generate(seed, {"finish_rule": "equal_top_bridge"}, 2, queries)
            assert short["test"] == relay["test"][:queries]
            prefixes += 1

        for pair in relay["train"] + relay["test"]:
            info = family.analyze(pair["input"])
            assert info["pair_intervals"] and info["bridge_cells"]
            assert all(seed_cell[0] > 0 for seed_cell in info["seeds"])
            for interval in info["pair_intervals"]:
                intervals_seen.add(tuple(interval))
            # Stage B on raw input sees an all-zero top row, so skipping Stage A
            # leaves the input unchanged and cannot equal the two-stage output.
            assert pair["output"] != pair["input"]
            skip_a_changes += 1
            cases += 1

        large = relay["test"][3]["input"]
        assert (len(large), len(large[0])) == (30, 30)
        large_info = family.analyze(large)
        assert len(large_info["pair_intervals"]) == 4
        assert len(large_info["bridge_cells"]) >= 12
        large_bridge_counts.append(len(large_info["bridge_cells"]))

    base_draws = 0
    for difficulty in (None, "medium"):
        for seed in range(24):
            grid = base.generate(seed, seed % 3, difficulty=difficulty)
            assert base.self_check(grid, difficulty=difficulty) == []
            base_draws += 1
    exact = base.generate(7, 0, difficulty="easy", grid_h=14, grid_w=14,
                          seed_count=8, texture="warm")
    assert base.observe_overrides(exact) == {"grid_h": 14, "grid_w": 14, "seed_count": 8}

    return {
        "schema": "138ffc14ac65-parametric-audit-v1",
        "status": "passed",
        "seed_count": len(seeds),
        "episode_pair_checks": cases,
        "count_prefix_checks": prefixes,
        "simple_rival_checks": rival_checks,
        "skip_a_changed_cases": skip_a_changes,
        "distinct_color_intervals": len(intervals_seen),
        "large_query_bridge_cell_range": [min(large_bridge_counts), max(large_bridge_counts)],
        "ordinary_base_draws": base_draws,
        "limits": "Finite generated-seed and named-rival audit; not a universal uniqueness proof.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
