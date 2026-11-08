#!/usr/bin/env python3
"""Attack plausible shortcuts in the local-frame quarter-turn family.

This is intentionally task-specific: it tests bypasses of source-local marker
extraction, frame orientation, turn order, marker-color completeness and target
basis rendering, plus crossed controls and the declared count/size boundaries.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable, Iterable

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_probe_91ba253f9945_prototype", _HOME / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)

Grid = list[list[int]]
Rival = Callable[[Grid, str], Grid]


def _render(grid: Grid, points, coordinate_transform, *, target_basis: bool = True) -> Grid:
    h, w = prototype._validate_grid(grid)
    target = prototype._find_frame(grid, (5, 6, 7))
    out = [row[:] for row in grid]
    for u, v, color in points:
        tu, tv = coordinate_transform(u, v)
        if target_basis:
            r, c = prototype._gpos(target, tu, tv)
        else:
            r, c = target[0][0] + tu, target[0][1] + tv
        if 0 <= r < h and 0 <= c < w:
            out[r][c] = color
    return out


def _opposite(grid: Grid, selected: str) -> Grid:
    other = "clockwise" if selected == "counterclockwise" else "counterclockwise"
    return prototype.apply_rule(grid, other)


def _no_rotation(grid: Grid, selected: str) -> Grid:
    return _render(grid, prototype.extract_intermediate(grid), lambda u, v: (u, v))


def _half_turn(grid: Grid, selected: str) -> Grid:
    return _render(grid, prototype.extract_intermediate(grid), lambda u, v: (-u, -v))


def _only_color(color: int) -> Rival:
    def rival(grid: Grid, selected: str) -> Grid:
        points = [point for point in prototype.extract_intermediate(grid) if point[2] == color]
        return _render(grid, points, lambda u, v: prototype._turned(u, v, selected))
    return rival


def _global_axes_intermediate(grid: Grid, selected: str) -> Grid:
    h, w = prototype._validate_grid(grid)
    source = prototype._find_frame(grid, (2, 3, 4))
    sr, sc = source[0]
    points = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] in (8, 9) and max(abs(r - sr), abs(c - sc)) <= 3:
                points.append((r - sr, c - sc, grid[r][c]))
    return _render(grid, points, lambda u, v: prototype._turned(u, v, selected))


def _ignore_target_basis(grid: Grid, selected: str) -> Grid:
    return _render(
        grid,
        prototype.extract_intermediate(grid),
        lambda u, v: prototype._turned(u, v, selected),
        target_basis=False,
    )


def _nearest_only(grid: Grid, selected: str) -> Grid:
    points = list(prototype.extract_intermediate(grid))
    radius = min(max(abs(u), abs(v)) for u, v, _ in points)
    points = [point for point in points if max(abs(point[0]), abs(point[1])) == radius]
    return _render(grid, points, lambda u, v: prototype._turned(u, v, selected))


def _first_marker_only(grid: Grid, selected: str) -> Grid:
    points = prototype.extract_intermediate(grid)[:1]
    return _render(grid, points, lambda u, v: prototype._turned(u, v, selected))


_LEGACY_SIX_MOTIFS = frozenset(
    tuple(sorted(pattern))
    for pattern in (
        ((-2, -1, 8), (-1, 2, 9), (1, -2, 8), (2, 1, 9), (2, 0, 8)),
        ((-2, 2, 9), (-1, -2, 8), (0, -2, 9), (1, 1, 8), (2, -1, 9)),
        ((-2, 0, 8), (-1, -2, 9), (1, 2, 8), (2, -1, 8), (2, 2, 9)),
        ((-2, -2, 9), (-2, 1, 8), (0, 2, 9), (1, -2, 8), (2, 0, 9)),
        ((-2, 1, 8), (-1, -2, 8), (0, 2, 9), (2, -2, 9), (2, 1, 8)),
        ((-2, -1, 9), (-1, 2, 8), (1, 1, 9), (2, -2, 8), (2, 0, 9)),
    )
)


def _legacy_six_motif_lookup(grid: Grid, selected: str) -> Grid:
    """A finite-template solver that exactly solved the first implementation."""
    points = prototype.extract_intermediate(grid)
    if points not in _LEGACY_SIX_MOTIFS:
        return [row[:] for row in grid]
    return _render(grid, points, lambda u, v: prototype._turned(u, v, selected))


_RIVALS: dict[str, Rival] = {
    "opposite_turn": _opposite,
    "skip_turn": _no_rotation,
    "half_turn": _half_turn,
    "copy_only_color_8": _only_color(8),
    "copy_only_color_9": _only_color(9),
    "global_axes_instead_of_source_frame": _global_axes_intermediate,
    "ignore_target_basis": _ignore_target_basis,
    "nearest_markers_only": _nearest_only,
    "first_marker_only": _first_marker_only,
    "legacy_six_motif_lookup": _legacy_six_motif_lookup,
}
_EPISODE_RIVALS = ("reuse_first_demo_intermediate",)


def _disagrees(rival: Rival, pairs, setting: str) -> bool:
    for pair in pairs:
        try:
            candidate = rival(pair["input"], setting)
        except (ValueError, IndexError):
            return True
        if candidate != pair["output"]:
            return True
    return False


def _crossed_controls() -> dict[str, bool]:
    fixed_profile_a = prototype._sample_input(0, "train", 0)
    fixed_profile_b = prototype._sample_input(17, "train", 0)
    intermediate_varies = prototype.extract_intermediate(fixed_profile_a) != prototype.extract_intermediate(fixed_profile_b)

    fixed_pattern = prototype._sample_pattern(0, "crossed-control", 0)
    fixed_intermediate_train = prototype._sample_input(0, "train", 0, pattern=fixed_pattern)
    fixed_intermediate_query = prototype._sample_input(0, "test", 0, pattern=fixed_pattern)
    profiles_vary = (
        prototype.extract_intermediate(fixed_intermediate_train)
        == prototype.extract_intermediate(fixed_intermediate_query)
        and (len(fixed_intermediate_train), len(fixed_intermediate_train[0]))
        != (len(fixed_intermediate_query), len(fixed_intermediate_query[0]))
    )
    return {
        "intermediate_varies_at_fixed_profile": intermediate_varies,
        "profiles_vary_at_fixed_intermediate": profiles_vary,
    }


def run(*, seeds=(0, 17, 41, 91), demo_counts=(2, 6)) -> dict[str, Any]:
    seeds = tuple(seeds)
    demo_counts = tuple(demo_counts)
    if not seeds or not demo_counts:
        raise ValueError("seeds and demo_counts must be nonempty")

    all_rivals = tuple(_RIVALS) + _EPISODE_RIVALS
    surviving_demo = set(all_rivals)
    surviving_query = set(all_rivals)
    ambiguous_episode_shortcuts = []
    episode_reuse_failures = []
    unique_intermediates = set()
    episodes = 0
    for seed in seeds:
        prototype._strict_int("seed", seed, 0, prototype.MAX_SEED)
        for demos in demo_counts:
            prototype._strict_int("demos", demos, prototype.MIN_DEMOS, prototype.MAX_DEMOS)
            for setting in prototype.TURNS:
                episode = prototype.generate(seed, {"turn": setting}, demos, 4)
                if len(episode["test"]) != 4:
                    raise AssertionError("query count drifted")
                encoded = [
                    json.dumps(pair["input"], separators=(",", ":"))
                    for pair in (*episode["train"], *episode["test"])
                ]
                if len(encoded) != len(set(encoded)):
                    raise AssertionError("duplicate inputs escaped generation")
                intermediates = [
                    prototype.extract_intermediate(pair["input"])
                    for pair in (*episode["train"], *episode["test"])
                ]
                unique_intermediates.update(intermediates)
                if len(intermediates) != len(set(intermediates)):
                    episode_reuse_failures.append({
                        "seed": seed,
                        "demos": demos,
                        "setting": setting,
                    })
                for name, rival in _RIVALS.items():
                    demo_disagrees = _disagrees(rival, episode["train"], setting)
                    query_disagrees = _disagrees(rival, episode["test"], setting)
                    if demo_disagrees:
                        surviving_demo.discard(name)
                    if query_disagrees:
                        surviving_query.discard(name)
                    if not demo_disagrees and query_disagrees:
                        ambiguous_episode_shortcuts.append({
                            "seed": seed,
                            "demos": demos,
                            "setting": setting,
                            "rival": name,
                        })

                fixed_points = prototype.extract_intermediate(episode["train"][0]["input"])
                def fixed_motif(pair):
                    return _render(
                        pair["input"],
                        fixed_points,
                        lambda u, v: prototype._turned(u, v, setting),
                    )
                fixed_demo_disagrees = any(fixed_motif(pair) != pair["output"] for pair in episode["train"])
                fixed_query_disagrees = any(fixed_motif(pair) != pair["output"] for pair in episode["test"])
                if fixed_demo_disagrees:
                    surviving_demo.discard("reuse_first_demo_intermediate")
                if fixed_query_disagrees:
                    surviving_query.discard("reuse_first_demo_intermediate")
                if not fixed_demo_disagrees and fixed_query_disagrees:
                    ambiguous_episode_shortcuts.append({
                        "seed": seed,
                        "demos": demos,
                        "setting": setting,
                        "rival": "reuse_first_demo_intermediate",
                    })
                episodes += 1

    controls = _crossed_controls()
    expected_unique = len(seeds) * (max(demo_counts) + prototype.MAX_QUERIES)
    motif_diversity = {
        "episode_reuse_failures": episode_reuse_failures,
        "unique_marker_motifs": len(unique_intermediates),
        "minimum_expected_unique": expected_unique,
        "legacy_catalog_size": len(_LEGACY_SIX_MOTIFS),
    }
    passed = (
        not surviving_demo
        and not surviving_query
        and not ambiguous_episode_shortcuts
        and not episode_reuse_failures
        and len(unique_intermediates) >= expected_unique
        and all(controls.values())
    )
    return {
        "schema": "arcpuzzles-task-adversarial-probe-v1",
        "task_id": prototype.TASK_ID,
        "status": "passed" if passed else "failed",
        "episodes": episodes,
        "settings": list(prototype.TURNS),
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "rivals": list(all_rivals),
        "episode_shortcut_checks": episodes * len(all_rivals),
        "ambiguous_episode_shortcuts": ambiguous_episode_shortcuts,
        "remaining_demo_shortcuts": sorted(surviving_demo),
        "remaining_query_shortcuts": sorted(surviving_query),
        "motif_diversity": motif_diversity,
        "crossed_controls": controls,
        "boundaries": {
            "minimum_demos": prototype.MIN_DEMOS,
            "maximum_demos": prototype.MAX_DEMOS,
            "minimum_query_shape": list(prototype._QUERY_PROFILES[0]),
            "maximum_query_shape": list(prototype._QUERY_PROFILES[-1]),
        },
        "finite_scope": "bounded named rivals over the listed seeds/settings/count corners; not a universal uniqueness proof",
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 17, 41, 91])
    parser.add_argument("--demo-counts", type=int, nargs="+", default=[2, 6])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = run(seeds=tuple(args.seeds), demo_counts=tuple(args.demo_counts))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
