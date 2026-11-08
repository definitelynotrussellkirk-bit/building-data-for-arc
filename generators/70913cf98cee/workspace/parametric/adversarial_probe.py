#!/usr/bin/env python3
"""Bounded semantic-rival probe for the minimum two-demo lesson.

The probe fits plausible wrong rules to demonstrations only and reports any rule
that fits every demo but changes a query.  It also records cross-seed diversity
of the post-recolor component intermediate at fixed profile dimensions.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Callable


def _load_family():
    source = Path(__file__).with_name("family.py")
    name = "_probe_family_" + hashlib.sha256(source.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ImportError(source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


F = _load_family()
Grid = list[list[int]]
Rule = Callable[[Grid], Grid]


def pairs(grid: Grid) -> list[tuple[int, int]]:
    values = [value for value in grid[0] if value]
    return list(zip(values[::2], values[1::2]))


def components(grid: Grid, color: int, connectivity: int = 4) -> list[set[tuple[int, int]]]:
    remaining = {(r, c) for r in range(2, len(grid)) for c in range(len(grid[0]))
                 if grid[r][c] == color}
    deltas = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if connectivity == 8:
        deltas += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    result = []
    while remaining:
        start = remaining.pop(); found = {start}; queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in deltas:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt); found.add(nxt); queue.append(nxt)
        result.append(found)
    return result


def direct(grid: Grid) -> Grid:
    return F.apply_python(grid, "direct")


def successors(grid: Grid, *, previous: bool = False) -> dict[int, int]:
    dsts = [dst for _src, dst in pairs(grid)]
    shift = -1 if previous else 1
    return {dst: dsts[(i + shift) % len(dsts)] for i, dst in enumerate(dsts)}


def repaint_post(grid: Grid, predicate, *, connectivity: int = 4,
                 target="next", cell_filter=None) -> Grid:
    mapped = direct(grid); out = [row[:] for row in mapped]
    ps = pairs(grid); succ = successors(grid, previous=(target == "previous"))
    source_for = {dst: src for src, dst in ps}
    for _src, dst in ps:
        for comp in components(mapped, dst, connectivity):
            if not predicate(comp):
                continue
            color = source_for[dst] if target == "source" else succ[dst]
            for r, c in comp:
                if cell_filter is None or cell_filter(grid, r, c, _src, dst):
                    out[r][c] = color
    return out


def all_destinations(grid: Grid) -> Grid:
    return repaint_post(grid, lambda _comp: True)


def size_le_two(grid: Grid) -> Grid:
    return repaint_post(grid, lambda comp: len(comp) <= 2)


def size_three(grid: Grid) -> Grid:
    return repaint_post(grid, lambda comp: len(comp) == 3)


def horizontal_only(grid: Grid) -> Grid:
    return repaint_post(grid, lambda comp: len(comp) == 2 and len({r for r, _ in comp}) == 1)


def vertical_only(grid: Grid) -> Grid:
    return repaint_post(grid, lambda comp: len(comp) == 2 and len({c for _, c in comp}) == 1)


def connectivity8(grid: Grid) -> Grid:
    return repaint_post(grid, lambda comp: len(comp) == 2, connectivity=8)


def first_pair_only(grid: Grid) -> Grid:
    first = pairs(grid)[0][1]
    mapped = direct(grid); out = [row[:] for row in mapped]; succ = successors(grid)
    for comp in components(mapped, first):
        if len(comp) == 2:
            for r, c in comp: out[r][c] = succ[first]
    return out


def last_pair_only(grid: Grid) -> Grid:
    last = pairs(grid)[-1][1]
    mapped = direct(grid); out = [row[:] for row in mapped]; succ = successors(grid)
    for comp in components(mapped, last):
        if len(comp) == 2:
            for r, c in comp: out[r][c] = succ[last]
    return out


def mapped_cells_only(grid: Grid) -> Grid:
    return repaint_post(grid, lambda comp: len(comp) == 2,
                        cell_filter=lambda original, r, c, src, _dst: original[r][c] == src)


def preexisting_cells_only(grid: Grid) -> Grid:
    return repaint_post(grid, lambda comp: len(comp) == 2,
                        cell_filter=lambda original, r, c, _src, dst: original[r][c] == dst)


def previous_destination(grid: Grid) -> Grid:
    return repaint_post(grid, lambda comp: len(comp) == 2, target="previous")


def next_source(grid: Grid) -> Grid:
    return repaint_post(grid, lambda comp: len(comp) == 2, target="source")


def pre_source_domino(grid: Grid) -> Grid:
    ps = pairs(grid); succ = successors(grid); mapped = direct(grid); out = [row[:] for row in mapped]
    for src, dst in ps:
        for comp in components(grid, src):
            if len(comp) == 2:
                for r, c in comp: out[r][c] = succ[dst]
    return out


def wrong_order(grid: Grid) -> Grid:
    # B first on existing destination dominoes, then canonical A.
    ps = pairs(grid); succ = successors(grid); staged = [row[:] for row in grid]
    for _src, dst in ps:
        for comp in components(grid, dst):
            if len(comp) == 2:
                for r, c in comp: staged[r][c] = succ[dst]
    return direct(staged)


def global_total_two(grid: Grid) -> Grid:
    mapped = direct(grid); out = [row[:] for row in mapped]; succ = successors(grid)
    for _src, dst in pairs(grid):
        cells = [(r, c) for r in range(2, len(mapped)) for c in range(len(mapped[0]))
                 if mapped[r][c] == dst]
        if len(cells) == 2:
            for r, c in cells: out[r][c] = succ[dst]
    return out


def top_half_only(grid: Grid) -> Grid:
    cutoff = (len(grid) + 2) // 2
    return repaint_post(grid, lambda comp: len(comp) == 2 and min(r for r, _ in comp) < cutoff)


def left_half_only(grid: Grid) -> Grid:
    cutoff = len(grid[0]) // 2
    return repaint_post(grid, lambda comp: len(comp) == 2 and min(c for _, c in comp) < cutoff)


RIVALS: dict[str, Rule] = {
    "direct": direct,
    "cycle_dominoes": lambda grid: F.apply_python(grid, "cycle_dominoes"),
    "cycle_all_destinations": all_destinations,
    "cycle_components_size_le_2": size_le_two,
    "cycle_components_size_3": size_three,
    "horizontal_dominoes_only": horizontal_only,
    "vertical_dominoes_only": vertical_only,
    "eight_connected_dominoes": connectivity8,
    "first_legend_pair_only": first_pair_only,
    "last_legend_pair_only": last_pair_only,
    "mapped_source_cells_only": mapped_cells_only,
    "preexisting_destination_cells_only": preexisting_cells_only,
    "previous_destination": previous_destination,
    "paint_with_source": next_source,
    "original_source_dominoes": pre_source_domino,
    "postprocess_before_recolor": wrong_order,
    "global_destination_count_two": global_total_two,
    "top_half_dominoes_only": top_half_only,
    "left_half_dominoes_only": left_half_only,
}


def signature(grid: Grid) -> tuple:
    mapped = direct(grid)
    rows = []
    for _src, dst in pairs(grid):
        comps = components(mapped, dst)
        rows.append((dst, tuple(sorted((len(comp), min(comp)) for comp in comps))))
    return tuple(rows)


def run(seeds: int) -> dict:
    if type(seeds) is not int or not 1 <= seeds <= 10000:
        raise ValueError("seeds must be an integer in 1..10000")
    holes = []
    equivalents = []
    signatures: dict[str, set[str]] = {}
    episodes = 0
    checks = 0
    for seed in range(seeds):
        for mode in F.SETTINGS:
            episode = F.generate(seed, {"postprocess": mode}, 2, 4)
            episodes += 1
            train = episode["train"]; test = episode["test"]
            for name, rival in RIVALS.items():
                if name == mode:
                    continue
                checks += 1
                try:
                    fits = all(rival(pair["input"]) == pair["output"] for pair in train)
                except Exception as exc:  # Rival failure never proves the intended rule.
                    holes.append({"seed": seed, "setting": mode, "rival": name,
                                  "kind": "rival_error", "error": f"{type(exc).__name__}: {exc}"})
                    continue
                if not fits:
                    continue
                disagreements = [i for i, pair in enumerate(test)
                                 if rival(pair["input"]) != pair["output"]]
                row = {"seed": seed, "setting": mode, "rival": name,
                       "query_disagreements": disagreements}
                if disagreements:
                    holes.append({**row, "kind": "teaching_hole"})
                else:
                    equivalents.append(row)
            for pair in train + test:
                dims = f"{len(pair['input'])}x{len(pair['input'][0])}"
                signatures.setdefault(dims, set()).add(repr(signature(pair["input"])))
    report = {
        "schema": "70913cf98cee-adversarial-probe-v1",
        "status": "passed" if not holes else "failed",
        "seeds": seeds,
        "episodes": episodes,
        "rivals": sorted(RIVALS),
        "rival_checks": checks,
        "teaching_holes": holes,
        "observationally_equivalent_on_episode": equivalents,
        "fixed_dimension_intermediate_signature_counts": {
            dims: len(values) for dims, values in sorted(signatures.items())
        },
        "limits": "Finite plausible-rival bank; no universal uniqueness claim.",
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run(args.seeds)
    raw = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw)
    print(raw, end="")
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
