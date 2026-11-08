"""Bounded author self-audit for the quadrant-summary parametric family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit(seeds=range(16)):
    family = _load(HERE / "adapter.py", "_quad_summary_family_audit")
    base = _load(HERE.parents[1] / "generator.py", "_quad_summary_base_audit")
    pair_checks = 0
    prefix_checks = 0
    rival_checks = 0
    selectors = set()
    rotations = set()
    large_nonzero = []
    for seed in seeds:
        episodes = {
            mode: family.generate(seed, {"finish_mode": mode}, 6, 4)
            for mode in family.MODES
        }
        canonical = episodes["quadrant_summary"]
        composed = episodes["indexed_color_rotate"]
        assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
            p["input"] for p in composed["train"] + composed["test"]
        ]
        assert family.fit_settings(canonical["train"][:2]) == [{"finish_mode": "quadrant_summary"}]
        assert family.fit_settings(composed["train"][:2]) == [{"finish_mode": "indexed_color_rotate"}]
        for demos in range(2, 7):
            assert family.generate(seed, {"finish_mode": "indexed_color_rotate"}, demos, 4)["train"] == composed["train"][:demos]
            prefix_checks += 1
        for queries in range(1, 5):
            assert family.generate(seed, {"finish_mode": "quadrant_summary"}, 2, queries)["test"] == canonical["test"][:queries]
            prefix_checks += 1

        gold = [pair["output"] for pair in composed["train"][:2]]
        summaries = [family.quadrant_summary(pair["input"]) for pair in composed["train"][:2]]
        fixed_rivals = {
            "no_rotation": summaries,
            "always_cw": [family._rotate_cw(summary) for summary in summaries],
            "always_180": [family._rotate_180(summary) for summary in summaries],
            "always_ccw": [family._rotate_ccw(summary) for summary in summaries],
        }
        assert all(outputs != gold for outputs in fixed_rivals.values())
        rival_checks += len(fixed_rivals)

        for pair in composed["train"] + composed["test"]:
            grid = pair["input"]
            summary = family.quadrant_summary(grid)
            index = family.selector_index(grid)
            selected = summary[index // 2][index % 2]
            assert pair["output"] == family.rotate_by_color(summary, selected)
            r0, c0, r1, c1 = family.eight_bbox(grid)
            assert all(
                value in (0, 8)
                for row, values in enumerate(grid)
                for column, value in enumerate(values)
                if not (r0 <= row <= r1 and c0 <= column <= c1)
            )
            selectors.add(index)
            rotations.add(selected % 4)
            pair_checks += 1
        large = composed["test"][3]["input"]
        assert (len(large), len(large[0])) == (30, 30)
        large_nonzero.append(sum(value != 0 for row in large for value in row))

    base_draws = 0
    for difficulty in (None, "medium"):
        for seed in range(16):
            grid = base.generate(seed, seed % 3, difficulty=difficulty)
            assert base.self_check(grid, difficulty=difficulty) == []
            base_draws += 1

    return {
        "schema": "3fb5ef8ad60e-parametric-audit-v1",
        "status": "passed",
        "seed_count": len(tuple(seeds)),
        "episode_pair_checks": pair_checks,
        "count_prefix_checks": prefix_checks,
        "fixed_rotation_rival_checks": rival_checks,
        "selector_indices_seen": sorted(selectors),
        "rotation_counts_seen": sorted(rotations),
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
