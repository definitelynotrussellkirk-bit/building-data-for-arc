#!/usr/bin/env python3
"""Read-only adversarial probes for the two assigned audit targets."""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from collections import Counter, deque
from pathlib import Path
from typing import Any, Callable

PACKET_ROOT = Path(__file__).resolve().parents[1]
REPO = PACKET_ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))

# The shipped runtime imports tooling through the historical ``scripts``
# package name, while this review packet stores those modules in
# ``shared/tools``.  Register a read-only namespace alias rather than
# mutating the packet or copying tool sources.
scripts_pkg = types.ModuleType("scripts")
scripts_pkg.__path__ = [str(REPO / "shared" / "tools")]
sys.modules.setdefault("scripts", scripts_pkg)

from puzzle_generators import runner  # noqa: E402


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid: list[list[int]]) -> list[tuple[int, list[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[tuple[int, list[tuple[int, int]]]] = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            found.append((color, cells))
    return found


def area_sorted_component_rule(grid: list[list[int]]) -> list[list[int]]:
    items = sorted(
        ((len(cells), color) for color, cells in components(grid)),
        key=lambda item: (-item[0], item[1]),
    )
    row = [color for size, color in items for _ in range(size)]
    return [row or [0]]


def color_frequency_shortcut(grid: list[list[int]]) -> list[list[int]]:
    counts = Counter(value for row in grid for value in row if value != 0)
    items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    row = [color for color, size in items for _ in range(size)]
    return [row or [0]]


def top_row_rule(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for c, color in enumerate(grid[0]):
        if color == 0:
            continue
        for k in range(min(h, w - c)):
            out[k][c + k] = color
    return out


def all_nonzero_emitters_shortcut(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for r0, row in enumerate(grid):
        for c0, color in enumerate(row):
            if color == 0:
                continue
            for k in range(min(h - r0, w - c0)):
                out[r0 + k][c0 + k] = color
    return out


def authoritative(task_id: str, grid: list[list[int]]) -> list[list[int]]:
    rule_source = None
    canonical_path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in canonical_path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            rule_source = row.get("program_solution")
            break
    if not isinstance(rule_source, str) or not rule_source.strip():
        raise FileNotFoundError(f"canonical rule missing for {task_id}")
    callable_text = runner.wrap_rule(rule_source)
    bridge, fn_name = runner._open_bridge_with_rule(callable_text)
    try:
        return runner._apply_rule(bridge, fn_name, grid)
    finally:
        close = getattr(bridge, "close", None)
        if callable(close):
            close()


def census(
    task_id: str,
    shortcut: Callable[[list[list[int]]], list[list[int]]],
    mirror: Callable[[list[list[int]]], list[list[int]]],
) -> dict[str, Any]:
    gen = load_generator(task_id)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for band in ("easy", "medium", "hard"):
        for seed in range(100):
            sample_index = seed * 7 + 3
            try:
                grid = gen.generate(seed, sample_index, difficulty=band)
            except Exception as exc:
                errors.append(
                    f"band={band} seed={seed} sample_index={sample_index}: "
                    f"{type(exc).__name__}: {exc}"
                )
                continue
            comps = components(grid)
            per_color = Counter(color for color, _ in comps)
            sizes = [len(cells) for _, cells in comps]
            rows.append(
                {
                    "band": band,
                    "shortcut_matches": shortcut(grid) == mirror(grid),
                    "one_component_per_color": all(value == 1 for value in per_color.values()),
                    "component_sizes_unique": len(sizes) == len(set(sizes)),
                    "lower_rows_blank": all(value == 0 for row in grid[1:] for value in row),
                    "marker_colors_distinct": len([v for v in grid[0] if v])
                    == len(set(v for v in grid[0] if v)),
                }
            )
    return {
        "requested": 300,
        "generated": len(rows),
        "errors": errors[:10],
        "shortcut_matches": sum(row["shortcut_matches"] for row in rows),
        "one_component_per_color": sum(row["one_component_per_color"] for row in rows),
        "component_sizes_unique": sum(row["component_sizes_unique"] for row in rows),
        "lower_rows_blank": sum(row["lower_rows_blank"] for row in rows),
        "marker_colors_distinct": sum(row["marker_colors_distinct"] for row in rows),
    }


def main() -> int:
    gen0 = load_generator("0f801939eff6")
    counter0 = [[0] * 10 for _ in range(7)]
    for r, c in ((0, 0), (0, 1), (1, 0), (1, 1)):
        counter0[r][c] = 2
    for r, c in ((3, 3), (3, 4), (3, 5)):
        counter0[r][c] = 3
    counter0[6][9] = 2
    auth0 = authoritative("0f801939eff6", counter0)

    gen82 = load_generator("82a4545adba4")
    counter82 = [[0] * 7 for _ in range(5)]
    counter82[0][0] = 2
    counter82[0][4] = 4
    counter82[2][0] = 6
    auth82 = authoritative("82a4545adba4", counter82)

    result = {
        "schema": "adversarial-audit-probes-v1",
        "0f801939eff6": {
            "hypothesis": (
                "sort total nonzero color frequencies instead of segmenting "
                "same-color connected components"
            ),
            "default_census": census(
                "0f801939eff6", color_frequency_shortcut, area_sorted_component_rule
            ),
            "counterexample": counter0,
            "self_check": gen0.self_check(counter0),
            "authoritative_output": auth0,
            "component_rule_output": area_sorted_component_rule(counter0),
            "shortcut_output": color_frequency_shortcut(counter0),
            "shortcut_refuted": auth0 != color_frequency_shortcut(counter0),
        },
        "82a4545adba4": {
            "hypothesis": (
                "emit a down-right ray from every nonzero input cell instead "
                "of ignoring rows below the first"
            ),
            "default_census": census(
                "82a4545adba4", all_nonzero_emitters_shortcut, top_row_rule
            ),
            "counterexample": counter82,
            "self_check": gen82.self_check(counter82),
            "authoritative_output": auth82,
            "top_row_rule_output": top_row_rule(counter82),
            "shortcut_output": all_nonzero_emitters_shortcut(counter82),
            "shortcut_refuted": auth82 != all_nonzero_emitters_shortcut(counter82),
        },
    }
    output = PACKET_ROOT / "checks" / "audit_probes.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
