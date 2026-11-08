"""Independent oracle, rival solvers, and audit helpers for 4e102ec13fc8.

This module is task-local review tooling.  The canonical Racket program remains
label authority; these Python functions make geometry and shortcut claims
reproducible without importing production helpers.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Iterable

from reviewer_support import find_root

ROOT = find_root(Path(__file__))
TASK = "4e102ec13fc8"
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path: str | os.PathLike[str] | None = None):
    path = Path(path or ROOT / "generators" / TASK / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    from reviewer_support import canonical_pairs as read_pairs, find_root

    return read_pairs(TASK, root=find_root(ROOT), labeled_only=True)


def _components(cells: Iterable[tuple[int, int]]) -> list[frozenset[tuple[int, int]]]:
    unseen = set(cells)
    result: list[frozenset[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(frozenset(component))
    return result


def body_components(grid: list[list[int]]) -> list[frozenset[tuple[int, int]]]:
    """Binary 4-components in rows 1+, excluding authority sentinel color 9."""
    cells = {
        (r, c)
        for r in range(1, len(grid))
        for c, value in enumerate(grid[r])
        if value not in (0, 9)
    }
    return _components(cells)


def depth_map(grid: list[list[int]]) -> dict[tuple[int, int], int]:
    """Repeated cardinal-boundary peeling, independently implemented by BFS.

    For a finite 4-connected set, peel depth equals 1 plus shortest cardinal
    distance to a missing cell.  Multi-source BFS from the exposed boundary is
    independent of the production implementation's iterative erosion.
    """
    depths: dict[tuple[int, int], int] = {}
    for component in body_components(grid):
        queue: deque[tuple[int, int]] = deque()
        for r, c in component:
            if any((r + dr, c + dc) not in component for dr, dc in _CARDINAL):
                depths[(r, c)] = 1
                queue.append((r, c))
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in component and point not in depths:
                    depths[point] = depths[(r, c)] + 1
                    queue.append(point)
    return depths


def reference_output(grid: list[list[int]], *, palette_mode: str = "all_nonzero",
                     body_mode: str = "all", component_mode: str = "all") -> list[list[int]]:
    """Solve the task, with switches used to instantiate canonical-fitting rivals."""
    out = deepcopy(grid)
    header = grid[0]
    if palette_mode == "all_nonzero":
        palette = [value for value in header if value != 0]
    elif palette_mode == "prefix":
        palette = []
        for value in header:
            if value == 0:
                break
            palette.append(value)
    else:
        raise ValueError(palette_mode)
    if not palette:
        return out

    depths = depth_map(grid)
    components = body_components(grid)
    allowed = set(depths)
    if component_mode == "largest" and components:
        allowed = set(max(components, key=lambda comp: (len(comp), tuple(sorted(comp)))))
    elif component_mode != "all":
        raise ValueError(component_mode)

    for (r, c), depth in depths.items():
        if (r, c) not in allowed:
            continue
        if body_mode == "blue_only" and grid[r][c] != 1:
            continue
        if body_mode not in ("all", "blue_only"):
            raise ValueError(body_mode)
        out[r][c] = palette[min(depth - 1, len(palette) - 1)]
    return out


def prefix_palette_output(grid: list[list[int]]) -> list[list[int]]:
    return reference_output(grid, palette_mode="prefix")


def blue_cells_only_output(grid: list[list[int]]) -> list[list[int]]:
    return reference_output(grid, body_mode="blue_only")


def largest_component_only_output(grid: list[list[int]]) -> list[list[int]]:
    return reference_output(grid, component_mode="largest")


def observed(grid: list[list[int]]) -> dict[str, int]:
    palette_positions = [c for c, value in enumerate(grid[0]) if value != 0]
    body_values = {
        value for row in grid[1:] for value in row if value not in (0, 9)
    }
    if len(body_values) != 1:
        raise ValueError(f"expected one body color, found {sorted(body_values)}")
    first, last = min(palette_positions), max(palette_positions)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_size": len(palette_positions),
        "header_gaps": sum(grid[0][c] == 0 for c in range(first, last + 1)),
        "component_count": len(body_components(grid)),
        "shape_color": next(iter(body_values)),
    }


def canonical_shortcut_fit() -> dict[str, bool]:
    rivals = {
        "contiguous_header_prefix": prefix_palette_output,
        "blue_cells_only": blue_cells_only_output,
        "largest_component_only": largest_component_only_output,
    }
    return {
        name: all(fn(pair["input"]) == pair["output"] for pair in canonical_pairs())
        for name, fn in rivals.items()
    }


def audit(module, count: int = 128) -> dict:
    rivals = {
        "contiguous_header_prefix": prefix_palette_output,
        "blue_cells_only": blue_cells_only_output,
        "largest_component_only": largest_component_only_output,
    }
    by_band = {}
    all_inputs = set()
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        profiles = set()
        observables = {name: set() for name in module.AXES}
        for index in range(count):
            grid = module.generate(41000 + index, index * 7 + 3, difficulty=band)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(
                41000 + index, index * 7 + 3, difficulty=band
            )
            official = reference_output(grid)
            counts["changed"] += official != grid
            for name, rival in rivals.items():
                counts[f"refutes_{name}"] += rival(grid) != official
            facts = observed(grid)
            for name, value in facts.items():
                observables[name].add(value)
            profile = (len(grid), len(grid[0]), len({x for row in grid for x in row}))
            profiles.add(profile)
            all_inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
        by_band[str(band)] = {
            **dict(counts),
            "profiles": sorted(profiles),
            "observable_values": {name: sorted(values) for name, values in observables.items()},
        }
    return {
        "schema": "4e102ec13fc8-independent-audit-v1",
        "version": module.VERSION,
        "rule_hash": module.RULE_HASH,
        "canonical_shortcut_fit": canonical_shortcut_fit(),
        "canonical_mirror_matches": sum(
            reference_output(pair["input"]) == pair["output"] for pair in canonical_pairs()
        ),
        "canonical_self_check": [module.self_check(pair["input"]) for pair in canonical_pairs()],
        "distinct_inputs": len(all_inputs),
        "by_band": by_band,
        "limitations": [
            "The Python mirror is supplementary; retained battery and --racket parity use canonical Racket authority.",
            "Finite rival checks do not prove unique induction against every possible rule.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    module = load_generator(args.generator)
    report = audit(module, args.count)
    report["generator_sha256"] = hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"version": report["version"], "distinct_inputs": report["distinct_inputs"],
                      "canonical_shortcut_fit": report["canonical_shortcut_fit"]}, indent=2))
    return int(
        report["canonical_mirror_matches"] != len(canonical_pairs())
        or any(report["canonical_self_check"])
        or any(row["self_check_errors"] or row["nondeterministic"] for row in report["by_band"].values())
    )


if __name__ == "__main__":
    raise SystemExit(main())
