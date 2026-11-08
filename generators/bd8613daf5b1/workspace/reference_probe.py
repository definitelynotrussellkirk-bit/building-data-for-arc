"""Independent probes for ``bd8613daf5b1``.

The Racket program remains the label authority.  This module keeps a separate
Python transliteration, a canonical-fitting wrong rule, profile measurements,
and a public-API Racket parity helper outside the production generator so task
regressions do not merely test implementation against itself.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
TASK = "bd8613daf5b1"
RULE_HASH = "94cb476392e1"
_RUNTIME = ROOT / "shared" / "runtime"
if str(_RUNTIME) not in sys.path:
    sys.path.insert(0, str(_RUNTIME))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root  # noqa: E402

CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def load_generator(path: str | os.PathLike[str] | None = None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_bd8613daf5b1", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return _canonical_pairs(TASK, root=find_root(__file__))


def _foreground(value: int) -> bool:
    return value not in (0, 9)


def components(grid: list[list[int]], *, by_color: bool = False) -> list[set[tuple[int, int]]]:
    """Return 4-connected foreground components; optionally split by color."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[set[tuple[int, int]]] = []
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or not _foreground(grid[sr][sc]):
                continue
            color = grid[sr][sc]
            todo = [(sr, sc)]
            seen.add((sr, sc))
            component: set[tuple[int, int]] = set()
            while todo:
                r, c = todo.pop()
                component.add((r, c))
                for dr, dc in CARDINAL:
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in seen:
                        continue
                    value = grid[nr][nc]
                    if not _foreground(value) or (by_color and value != color):
                        continue
                    seen.add((nr, nc))
                    todo.append((nr, nc))
            result.append(component)
    return result


def _depth_crop(grid: list[list[int]], *, by_color: bool) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    depth = [[0] * w for _ in range(h)]
    for component in components(grid, by_color=by_color):
        remaining = set(component)
        layer = 1
        while remaining:
            boundary = {
                (r, c)
                for r, c in remaining
                if any((r + dr, c + dc) not in remaining for dr, dc in CARDINAL)
            }
            if not boundary:
                raise AssertionError("finite nonempty component had no boundary")
            for r, c in boundary:
                depth[r][c] = layer
            remaining.difference_update(boundary)
            layer += 1
    occupied = [(r, c) for r in range(h) for c in range(w) if depth[r][c] != 0]
    if not occupied:
        return [[0]]
    r0 = min(r for r, _ in occupied)
    r1 = max(r for r, _ in occupied)
    c0 = min(c for _, c in occupied)
    c1 = max(c for _, c in occupied)
    return [row[c0:c1 + 1] for row in depth[r0:r1 + 1]]


def onion_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent transliteration of the selected color-agnostic authority."""
    return _depth_crop(deepcopy(grid), by_color=False)


def color_separate_output(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: peel each exact-color component separately."""
    return _depth_crop(deepcopy(grid), by_color=True)


def observed(grid: list[list[int]]) -> dict[str, int]:
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def max_component_size(grid: list[list[int]]) -> int:
    return max((len(component) for component in components(grid)), default=0)


def has_multicolor_component(grid: list[list[int]]) -> bool:
    for component in components(grid):
        colors = {grid[r][c] for r, c in component}
        if len(colors) > 1:
            return True
    return False


def racket_outputs(grids: Iterable[list[list[int]]]) -> list[list[list[int]]]:
    """Execute the canonical authority through the public Catalog API."""
    src = ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from arcpuzzles import Catalog

    grids = list(grids)
    receipt = Catalog(ROOT).apply(TASK, grids, reference="canonical", timeout=300)
    if not receipt.get("rule_hash_matches_catalog"):
        raise RuntimeError("executed rule hash did not match the catalog")
    errors = [row.get("error") for row in receipt["results"]]
    if any(error is not None for error in errors):
        raise RuntimeError(f"Racket apply failed: {errors}")
    return [row["output"] for row in receipt["results"]]


def audit(module, count: int = 120) -> dict:
    grids = [module.generate(7301 + index, index) for index in range(count)]
    canonical = canonical_pairs()
    shortcuts = dict(getattr(module, "CANONICAL_SHORTCUTS", {}))
    return {
        "task_id": TASK,
        "version": getattr(module, "VERSION", None),
        "count": count,
        "unique_inputs": len({json.dumps(grid, separators=(",", ":")) for grid in grids}),
        "profiles": sorted({profile(grid) for grid in grids}),
        "max_component_size": max(max_component_size(grid) for grid in grids),
        "multicolor_components": sum(has_multicolor_component(grid) for grid in grids),
        "self_check_failures": [
            {"index": index, "errors": module.self_check(grid)}
            for index, grid in enumerate(grids)
            if module.self_check(grid)
        ],
        "mirror_mismatches": [
            index for index, grid in enumerate(grids)
            if getattr(module, "rule_mirror", onion_output)(grid) != onion_output(grid)
        ],
        "canonical_shortcut_fit": {
            name: all(rival(pair["input"]) == pair["output"] for pair in canonical)
            for name, rival in shortcuts.items()
        },
        "generated_shortcut_counterexamples": {
            name: sum(rival(grid) != onion_output(grid) for grid in grids)
            for name, rival in shortcuts.items()
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", default=os.environ.get("GENERATOR_UNDER_TEST"))
    parser.add_argument("--count", type=int, default=120)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit(load_generator(args.generator), args.count)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if not report["self_check_failures"] and not report["mirror_mismatches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
