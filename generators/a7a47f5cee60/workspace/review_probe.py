#!/usr/bin/env python3
"""Independent object-contact graph probe for a7a47f5cee60.

Library use:
    report = analyze(grid)

CLI use from the repository root:
    python generators/a7a47f5cee60/workspace/review_probe.py --scan 30
    python generators/a7a47f5cee60/workspace/review_probe.py grid.json

The probe deliberately does not import graph helpers from generator.py.  It is
useful for future repairs because it can catch a shared-oracle mistake.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

MOVES = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _objects(grid):
    h, w = len(grid), len(grid[0])
    pending = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result = []
    while pending:
        start = min(pending)
        pending.remove(start)
        color = grid[start[0]][start[1]]
        cells, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in MOVES:
                point = (r + dr, c + dc)
                if point in pending and grid[point[0]][point[1]] == color:
                    pending.remove(point)
                    cells.add(point)
                    stack.append(point)
        result.append({"color": color, "cells": sorted(cells)})
    return result


def _components(edges, skip=None):
    remaining = set(range(len(edges)))
    if skip is not None:
        remaining.discard(skip)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        comp, stack = {start}, [start]
        while stack:
            i = stack.pop()
            for j in edges[i]:
                if j in remaining:
                    remaining.remove(j)
                    comp.add(j)
                    stack.append(j)
        result.append(sorted(comp))
    return result


def analyze(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("expected a nonempty JSON grid")
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a rectangular JSON grid")
    objects = _objects(grid)
    owner = {tuple(cell): i for i, obj in enumerate(objects) for cell in obj["cells"]}
    edges = [set() for _ in objects]
    for (r, c), i in owner.items():
        for dr, dc in MOVES:
            j = owner.get((r + dr, c + dc))
            if j is not None and j != i:
                edges[i].add(j)
                edges[j].add(i)
    base = len(_components(edges))
    articulations = [
        i for i in range(len(objects))
        if len(_components(edges, i)) > base
    ]
    return {
        "shape": [len(grid), len(grid[0])],
        "object_count": len(objects),
        "objects": [
            {"index": i, "color": obj["color"], "area": len(obj["cells"]), "cells": obj["cells"]}
            for i, obj in enumerate(objects)
        ],
        "edges": [sorted(neighbors) for neighbors in edges],
        "degrees": [len(neighbors) for neighbors in edges],
        "graph_components": _components(edges),
        "graph_component_count": base,
        "articulation_indices": articulations,
    }


def _load_generator():
    home = Path(__file__).resolve().parents[1]
    root = next(p for p in home.parents if (p / "shared/runtime").is_dir() or (p / "arc_repl").is_dir())
    if (root / "shared/runtime").is_dir():
        sys.path.insert(0, str(root / "shared/runtime"))
    else:
        sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location("probed_generator", home / "generator.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _scan(count, difficulty):
    gen = _load_generator()
    rows = []
    for seed in range(count):
        index = seed % len(gen.SCHEDULE_PROFILES)
        grid = gen.generate(seed, index, difficulty=difficulty)
        report = analyze(grid)
        rows.append({
            "seed": seed,
            "sample_index": index,
            "profile": gen.schedule_profile(seed, index, difficulty),
            "shape": report["shape"],
            "object_count": report["object_count"],
            "articulations": report["articulation_indices"],
            "self_check": gen.self_check(grid),
            "rivals_refuted": sorted(
                name for name, rival in gen.SEMANTIC_RIVALS.items()
                if rival(grid) != gen._rule_mirror(grid)
            ),
        })
    return {"generator_id": gen.GENERATOR_ID, "difficulty": difficulty, "samples": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("grid", nargs="?", type=Path, help="JSON file containing one grid")
    parser.add_argument("--scan", type=int, metavar="N", help="scan N generated seeds instead")
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default=None)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)
    if (args.grid is None) == (args.scan is None):
        parser.error("provide exactly one of GRID or --scan N")
    payload = _scan(args.scan, args.difficulty) if args.scan is not None else analyze(
        json.loads(args.grid.read_text(encoding="utf-8"))
    )
    print(json.dumps(payload, indent=None if args.compact else 2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
