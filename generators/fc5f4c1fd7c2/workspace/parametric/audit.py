"""Bounded author self-audit for the fc5f4c1fd7c2 corner relay family."""
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
    family = _load(HERE / "prototype.py", "_fc5_family_audit")
    base = _load(HERE.parents[1] / "generator.py", "_fc5_base_audit")
    cases = 0
    prefixes = 0
    rival_checks = 0
    skip_a_changes = 0
    selected = set()
    large_nonzero = []
    for seed in seeds:
        episodes = {
            mode: family.generate(seed, {"finish_mode": mode}, 6, 4)
            for mode in family.MODES
        }
        left = episodes["mark_only"]
        right = episodes["selector_frame"]
        assert [p["input"] for p in left["train"] + left["test"]] == [p["input"] for p in right["train"] + right["test"]]
        assert family.fit_settings(left["train"][:2]) == [{"finish_mode": "mark_only"}]
        assert family.fit_settings(right["train"][:2]) == [{"finish_mode": "selector_frame"}]
        rivals = family.simple_rival_outputs(right["train"][:2])
        gold = [p["output"] for p in right["train"][:2]]
        assert all(outputs != gold for outputs in rivals.values())
        rival_checks += len(rivals)
        for demos in range(2, 7):
            short = family.generate(seed, {"finish_mode": "selector_frame"}, demos, 4)
            assert short["train"] == right["train"][:demos]
            prefixes += 1
        for queries in range(1, 5):
            short = family.generate(seed, {"finish_mode": "selector_frame"}, 2, queries)
            assert short["test"] == right["test"][:queries]
            prefixes += 1
        for pair in right["train"] + right["test"]:
            analysis = family.analyze(pair["input"])
            assert analysis["selected_bbox"] is not None and analysis["frame_cells"]
            selected.add(tuple(analysis["selected_bbox"]))
            # Skip-A leaves no blue intermediate for the selector and therefore
            # cannot produce either the canonical marks or the selected frame.
            assert pair["output"] != pair["input"]
            skip_a_changes += 1
            cases += 1
        large = right["test"][3]["input"]
        assert (len(large), len(large[0])) == (30, 30)
        count = sum(v != 0 for row in large for v in row)
        assert count >= 80
        large_nonzero.append(count)

    base_draws = 0
    for difficulty in (None, "medium"):
        for seed in range(24):
            grid = base.generate(seed, seed % 3, difficulty=difficulty)
            assert base.self_check(grid, difficulty=difficulty) == []
            base_draws += 1
    exact = base.generate(7, 0, difficulty="easy", grid_h=18, grid_w=20,
                          n=4, n_distractor=3, texture="warm")
    assert base.observe_overrides(exact) == {"grid_h": 18, "grid_w": 20, "n": 4, "n_distractor": 3}

    return {
        "schema": "fc5f4c1fd7c2-parametric-audit-v1",
        "status": "passed",
        "seed_count": len(tuple(seeds)),
        "episode_pair_checks": cases,
        "count_prefix_checks": prefixes,
        "simple_rival_checks": rival_checks,
        "skip_a_changed_cases": skip_a_changes,
        "distinct_selected_bboxes": len(selected),
        "large_query_nonzero_range": [min(large_nonzero), max(large_nonzero)],
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
