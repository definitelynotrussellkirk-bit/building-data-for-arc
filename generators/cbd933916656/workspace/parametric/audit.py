"""Bounded author self-audit for the perimeter-rank selector family."""
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


def _paint_ranked(family, grid, ranked):
    out = [[0] * len(grid[0]) for _ in grid]
    for color, cells in zip(family.RANK_COLORS, ranked):
        for row, column in cells:
            out[row][column] = color
    return out


def _fill_rank(family, grid, rank, *, ranked=None):
    ranked = family.ranked_components(grid) if ranked is None else ranked
    out = _paint_ranked(family, grid, ranked)
    r0, c0, r1, c1 = family.bbox(ranked[rank])
    color = family.RANK_COLORS[rank]
    for row in range(r0, r1 + 1):
        for column in range(c0, c1 + 1):
            out[row][column] = color
    return out


def audit(seeds=range(16)):
    family = _load(HERE / "adapter.py", "_perimeter_selector_family_audit")
    base = _load(HERE.parents[1] / "generator.py", "_perimeter_selector_base_audit")
    pair_checks = 0
    prefix_checks = 0
    rival_checks = 0
    positions_by_rank = {0: set(), 1: set(), 2: set()}
    large_nonzero = []
    for seed in seeds:
        episodes = {
            mode: family.generate(seed, {"finish_mode": mode}, 6, 4)
            for mode in family.MODES
        }
        canonical = episodes["rank_only"]
        composed = episodes["selector_bbox"]
        assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
            p["input"] for p in composed["train"] + composed["test"]
        ]
        assert family.fit_settings(canonical["train"][:3]) == [{"finish_mode": "rank_only"}]
        assert family.fit_settings(composed["train"][:3]) == [{"finish_mode": "selector_bbox"}]
        for demos in range(3, 7):
            assert family.generate(seed, {"finish_mode": "selector_bbox"}, demos, 4)["train"] == composed["train"][:demos]
            prefix_checks += 1
        for queries in range(1, 5):
            assert family.generate(seed, {"finish_mode": "rank_only"}, 3, queries)["test"] == canonical["test"][:queries]
            prefix_checks += 1

        gold = [pair["output"] for pair in composed["train"][:3]]
        fixed = {
            f"fixed_rank_{rank}": [_fill_rank(family, pair["input"], rank) for pair in composed["train"][:3]]
            for rank in range(3)
        }
        assert all(outputs != gold for outputs in fixed.values())
        rival_checks += len(fixed)

        area_outputs = []
        for pair in composed["train"][:3]:
            grid = pair["input"]
            components = family.components_nonzero(grid)
            area_ranked = sorted(components, key=lambda cells: (len(cells), family.bbox(cells)))
            area_outputs.append(_fill_rank(family, grid, family.selector_rank(grid), ranked=area_ranked))
        assert area_outputs != gold
        rival_checks += 1

        for pair in composed["train"] + composed["test"]:
            grid = pair["input"]
            components = family.components_nonzero(grid)
            assert len(components) == 3
            assert len({family.cardinal_perimeter(cells) for cells in components}) == 3
            perimeter_ranked = family.ranked_components(grid)
            area_ranked = sorted(components, key=lambda cells: (len(cells), family.bbox(cells)))
            assert [frozenset(c) for c in perimeter_ranked] != [frozenset(c) for c in area_ranked]
            rank = family.selector_rank(grid)
            selected = perimeter_ranked[rank]
            positions_by_rank[rank].add(family.bbox(selected))
            assert pair["output"] == family.selector_bbox(grid)
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
        "schema": "cbd933916656-parametric-audit-v1",
        "status": "passed",
        "seed_count": len(tuple(seeds)),
        "episode_pair_checks": pair_checks,
        "count_prefix_checks": prefix_checks,
        "semantic_rival_checks": rival_checks,
        "selected_bbox_counts_by_rank": {str(rank): len(values) for rank, values in positions_by_rank.items()},
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
