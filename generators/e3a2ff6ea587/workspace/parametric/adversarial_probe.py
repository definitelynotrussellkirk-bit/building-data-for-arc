"""Finite adversarial probe for the rectangle-fill cascade lesson.

The probe attacks the two-demo lesson, not merely the declared setting programs.
Every rival is executable Python over the same visible grids.  A rival is a
remaining demo shortcut only if it matches *all* visible demonstrations in an
episode; query-only matches are tracked separately.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Callable

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_cascade_probe_impl", _HOME / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("cannot load prototype.py")
p = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(p)

Grid = list[list[int]]
Rival = Callable[[Grid], Grid]


def _blank(grid: Grid) -> Grid:
    return [[0 for _ in row] for row in grid]


def _fill_every_bbox(grid: Grid) -> Grid:
    grid = p._grid(grid)
    out = _blank(grid)
    cells = p._cells_by_color(grid)
    for color in p._colors(grid):
        p._paint(out, p._bbox(cells[color]), color)
    return out


def _fill_exactly_four_bbox(grid: Grid) -> Grid:
    grid = p._grid(grid)
    out = _blank(grid)
    cells = p._cells_by_color(grid)
    for color in p._colors(grid):
        if len(cells[color]) == 4:
            p._paint(out, p._bbox(cells[color]), color)
    return out


def _all_two_point_triggers(grid: Grid) -> Grid:
    grid = p._grid(grid)
    stage, _ = p._stage(grid)
    out = [row[:] for row in stage]
    cells = p._cells_by_color(grid)
    for color in p._colors(grid):
        if len(cells[color]) == 2:
            p._paint(out, p._bbox(cells[color]), color)
    return out


def _any_anchor_hit(grid: Grid) -> Grid:
    grid = p._grid(grid)
    stage, qualifiers = p._stage(grid)
    out = [row[:] for row in stage]
    if not qualifiers:
        return out
    anchor = qualifiers[0]
    cells = p._cells_by_color(grid)
    for color in p._colors(grid):
        points = cells[color]
        if len(points) == 2 and any(stage[r][c] == anchor for r, c in points):
            p._paint(out, p._bbox(points), color)
    return out


def _boundary_profile(grid: Grid) -> Grid:
    """Former surviving shortcut: fixed boundary roles, no Stage-A read."""
    grid = p._grid(grid)
    stage, _ = p._stage(grid)
    out = [row[:] for row in stage]
    h, w = len(grid), len(grid[0])
    cells = p._cells_by_color(grid)
    for color in p._colors(grid):
        points = cells[color]
        boundary = [
            cell for cell in points
            if cell[0] in (0, h - 1) or cell[1] in (0, w - 1)
        ]
        if len(points) == 2 and len(boundary) == 1 and boundary[0] != (h - 1, w - 1):
            p._paint(out, p._bbox(points), color)
    return out


def _first_two_by_position(grid: Grid) -> Grid:
    grid = p._grid(grid)
    stage, _ = p._stage(grid)
    out = [row[:] for row in stage]
    cells = p._cells_by_color(grid)
    ranked = sorted(
        (min(points), color)
        for color, points in cells.items()
        if len(points) == 2
    )
    for _position, color in ranked[:2]:
        p._paint(out, p._bbox(cells[color]), color)
    return out


def _largest_two_bboxes(grid: Grid) -> Grid:
    grid = p._grid(grid)
    stage, _ = p._stage(grid)
    out = [row[:] for row in stage]
    cells = p._cells_by_color(grid)
    ranked = []
    for color, points in cells.items():
        if len(points) != 2:
            continue
        r1, c1, r2, c2 = p._bbox(points)
        ranked.append((-(r2 - r1 + 1) * (c2 - c1 + 1), color))
    for _area, color in sorted(ranked)[:2]:
        p._paint(out, p._bbox(cells[color]), color)
    return out


def _lowest_trigger_only(grid: Grid) -> Grid:
    grid = p._grid(grid)
    stage, qualifiers = p._stage(grid)
    out = [row[:] for row in stage]
    if not qualifiers:
        return out
    anchor = qualifiers[0]
    cells = p._cells_by_color(grid)
    candidates = [
        color
        for color in p._colors(grid)
        if len(cells[color]) == 2
        and sum(stage[r][c] == anchor for r, c in cells[color]) == 1
    ]
    if candidates:
        color = min(candidates)
        p._paint(out, p._bbox(cells[color]), color)
    return out


def _rivals(mode: str, first_demo_output: Grid) -> dict[str, Rival]:
    other = "triggered_cascade" if mode == "canonical" else "canonical"
    return {
        "fill_every_bbox": _fill_every_bbox,
        "fill_exactly_four_bbox": _fill_exactly_four_bbox,
        "all_two_point_triggers": _all_two_point_triggers,
        "any_anchor_hit": _any_anchor_hit,
        "coverage_only": lambda grid: p.apply_counterfactual(grid, "coverage_only"),
        "reverse_stage_order": lambda grid: p.apply_counterfactual(grid, "reverse_stage_order"),
        "skip_stage_a": lambda grid: p.apply_counterfactual(grid, "skip_stage_a"),
        "lowest_trigger_only": _lowest_trigger_only,
        "boundary_profile": _boundary_profile,
        "first_two_by_position": _first_two_by_position,
        "largest_two_bboxes": _largest_two_bboxes,
        "reuse_first_demo_output": lambda _grid: [row[:] for row in first_demo_output],
        "wrong_setting": lambda grid: p.apply_rule(grid, other),
    }


def _matches(rival: Rival, pairs: list[dict[str, Grid]]) -> bool:
    try:
        return all(rival(pair["input"]) == pair["output"] for pair in pairs)
    except Exception:
        return False


def _crossed_controls() -> dict[str, bool]:
    fixed_profile_a = p.generate(0, {"cascade_mode": "triggered_cascade"}, 2, 4)["test"][-1]["input"]
    fixed_profile_b = p.generate(17, {"cascade_mode": "triggered_cascade"}, 2, 4)["test"][-1]["input"]
    varies_intermediate = (
        (len(fixed_profile_a), len(fixed_profile_a[0])) == (len(fixed_profile_b), len(fixed_profile_b[0]))
        and p.digest(p.intermediate(fixed_profile_a)) != p.digest(p.intermediate(fixed_profile_b))
    )

    original = p.generate(41, {"cascade_mode": "triggered_cascade"}, 2, 4)["test"][-1]["input"]
    nuisance_variant = p.mutate_nuisance(original)
    varies_profile = (
        original != nuisance_variant
        and p.intermediate(original) == p.intermediate(nuisance_variant)
        and p.apply_rule(original, "triggered_cascade") == p.apply_rule(nuisance_variant, "triggered_cascade")
    )
    return {
        "intermediate_varies_at_fixed_profile": varies_intermediate,
        "profiles_vary_at_fixed_intermediate": varies_profile,
    }


def run(*, seeds=(0, 17, 41, 91), demo_counts=(2, 6)) -> dict[str, object]:
    checked_seeds = tuple(p._strict_int("seed", seed, 0, p.MAX_SEED) for seed in seeds)
    checked_counts = tuple(p._strict_int("demos", count, p.MIN_DEMOS, p.MAX_DEMOS) for count in demo_counts)
    modes = p.MODES
    remaining_demo: list[dict[str, object]] = []
    remaining_query: list[dict[str, object]] = []
    ambiguous: list[dict[str, object]] = []
    rival_names: set[str] = set()
    checks = 0
    episodes = 0

    for seed in checked_seeds:
        for demos in checked_counts:
            for mode in modes:
                episodes += 1
                episode = p.generate(seed, {"cascade_mode": mode}, demos, 4)
                rivals = _rivals(mode, episode["train"][0]["output"])
                rival_names.update(rivals)
                for name, rival in rivals.items():
                    checks += len(episode["train"]) + len(episode["test"])
                    demo_match = _matches(rival, episode["train"])
                    query_match = _matches(rival, episode["test"])
                    identity = {"seed": seed, "demos": demos, "mode": mode, "rival": name}
                    if demo_match:
                        remaining_demo.append(identity)
                    if query_match:
                        remaining_query.append(identity)
                    if demo_match and not query_match:
                        ambiguous.append(identity)

    crossed = _crossed_controls()
    status = "passed" if not remaining_demo and not remaining_query and not ambiguous and all(crossed.values()) else "failed"
    return {
        "schema": "e3a2ff6ea587-adversarial-probe-v1",
        "status": status,
        "episodes": episodes,
        "pair_rival_checks": checks,
        "seeds": list(checked_seeds),
        "demo_counts": list(checked_counts),
        "rivals": sorted(rival_names),
        "remaining_demo_shortcuts": remaining_demo,
        "remaining_query_shortcuts": remaining_query,
        "ambiguous_episode_shortcuts": ambiguous,
        "crossed_controls": crossed,
        "boundaries": {
            "minimum_demos": p.MIN_DEMOS,
            "maximum_demos": p.MAX_DEMOS,
            "maximum_query_shape": list(p._QUERY_PROFILES[-1]),
        },
        "limits": (
            "Finite executable rivals and sampled controls do not prove universal uniqueness; "
            "the report establishes only the listed families on the listed seeds/counts."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(text, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(args.out)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
