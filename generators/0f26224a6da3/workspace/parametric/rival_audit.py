"""Bounded semantic-rival audit for isolated-source selection lessons."""
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_SOURCE = HERE / "prototype.py"
_SPEC = importlib.util.spec_from_file_location(
    "_0f26_audit_proto_" + hashlib.sha256(_SOURCE.read_bytes()).hexdigest(), _SOURCE
)
P = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(P)


def _by_color(grid, chooser, *, dirs=P.DIRS4):
    sources = P.isolated_sources(grid, dirs)
    counts = Counter(grid[row][col] for row, col in sources)
    colors = chooser(counts)
    selected = [(row, col) for row, col in sources if grid[row][col] in colors]
    return P.expand_sources(grid, selected)


def _all_foreground(grid):
    return P.expand_sources(
        grid,
        [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0],
    )


def _interior_truth(grid, scope):
    height, width = len(grid), len(grid[0])
    selected = P.selected_sources(grid, scope)
    selected = [(r, c) for r, c in selected if 0 < r < height - 1 and 0 < c < width - 1]
    return P.expand_sources(grid, selected)


def _eight_neighbor_truth(grid, scope):
    sources = P.isolated_sources(grid, P.DIRS8)
    if scope == "all_isolated":
        return P.expand_sources(grid, sources)
    counts = Counter(grid[r][c] for r, c in sources)
    if not counts:
        return P.expand_sources(grid, [])
    minimum = min(counts.values())
    winners = {color for color, count in counts.items() if count == minimum}
    return P.expand_sources(grid, [(r, c) for r, c in sources if grid[r][c] in winners])


def _rivals(settings):
    truth = settings["source_scope"]
    other = "rarest_color" if truth == "all_isolated" else "all_isolated"
    rivals = {
        "other_native_scope": lambda grid: P.claimed_output(grid, {"source_scope": other}),
        "expand_every_foreground": _all_foreground,
        "interior_sources_only": lambda grid: _interior_truth(grid, truth),
        "eight_neighbor_isolation": lambda grid: _eight_neighbor_truth(grid, truth),
        "minimum_numeric_color": lambda grid: _by_color(grid, lambda counts: {min(counts)}),
        "maximum_numeric_color": lambda grid: _by_color(grid, lambda counts: {max(counts)}),
        "most_frequent_color": lambda grid: _by_color(
            grid, lambda counts: {max(counts, key=lambda color: (counts[color], -color))}
        ),
        "singleton_source_colors": lambda grid: _by_color(
            grid, lambda counts: {color for color, count in counts.items() if count == 1}
        ),
        "top_left_source_color": lambda grid: _by_color(
            grid,
            lambda counts: set(),
        ),
        "top_left_source_only": lambda grid: P.expand_sources(grid, [min(P.isolated_sources(grid))]),
        "no_expansion": lambda grid: [row[:] for row in grid],
    }
    # Override top-left-color with access to positions rather than counts.
    rivals["top_left_source_color"] = lambda grid: P.expand_sources(
        grid,
        [
            (r, c)
            for r, c in P.isolated_sources(grid)
            if grid[r][c] == grid[min(P.isolated_sources(grid))[0]][min(P.isolated_sources(grid))[1]]
        ],
    )
    for color in range(1, 10):
        rivals[f"fixed_color_{color}"] = lambda grid, color=color: P.expand_sources(
            grid,
            [(r, c) for r, c in P.isolated_sources(grid) if grid[r][c] == color],
        )
    return rivals


def audit_episode(seed, settings, demos=2, queries=4):
    episode = P.generate(seed, settings, demos=demos, queries=queries)
    rivals = _rivals(settings)
    survivors, harmful, query_disagreements = [], [], {}
    for name, rival in rivals.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in episode["train"])
            disagreements = [
                index
                for index, pair in enumerate(episode["test"])
                if rival(pair["input"]) != pair["output"]
            ]
        except Exception as error:
            fits = False
            disagreements = [f"error:{type(error).__name__}:{error}"]
        if fits:
            survivors.append(name)
            query_disagreements[name] = disagreements
            if disagreements:
                harmful.append(name)
    constant = episode["train"][0]["output"]
    return {
        "seed": seed,
        "settings": settings,
        "demos": demos,
        "queries": queries,
        "rival_count": len(rivals),
        "survivors": survivors,
        "harmful_survivors": harmful,
        "query_disagreements": query_disagreements,
        "constant_query_failures": sum(pair["output"] != constant for pair in episode["test"]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 4096:
        raise SystemExit("--seeds must be in 1..4096")
    reports = [
        audit_episode(seed, settings)
        for seed in range(args.seeds)
        for settings in P.SETTINGS
    ]
    payload = {
        "schema": "arcpuzzles-bounded-rival-audit-v1",
        "task_id": P.TASK_ID,
        "episodes": len(reports),
        "pairs": sum(report["demos"] + report["queries"] for report in reports),
        "harmful_survivors": sum(len(report["harmful_survivors"]) for report in reports),
        "reports": reports,
        "limitations": "Finite named rivals and sampled seeds; not a proof of universal identifiability.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: payload[k] for k in ("task_id", "episodes", "pairs", "harmful_survivors")}, sort_keys=True))
    if payload["harmful_survivors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
