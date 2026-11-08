"""Independent oracle and audit helpers for e4351af561ac.

This module is reviewer tooling, not label authority.  It intentionally does not
import geometry helpers from the generator under review.  Canonical labels come
from reviewer_support; generated-label parity can additionally be checked by the
repository's Racket-backed battery and lesson census.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Iterable

TASK = "e4351af561ac"
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path: str | os.PathLike[str] | None = None):
    if path is None:
        path = Path(__file__).resolve().parents[1] / "generator.py"
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid: list[list[int]]) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    """Return monochrome four-connected nonzero components in scan order."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.popleft()
                cells.append((rr, cc))
                for dr, dc in CARDINAL:
                    point = (rr + dr, cc + dc)
                    if (0 <= point[0] < h and 0 <= point[1] < w
                            and point not in seen
                            and grid[point[0]][point[1]] == color):
                        seen.add(point)
                        todo.append(point)
            result.append((color, tuple(sorted(cells))))
    return result


def normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def rotate(shape: Iterable[tuple[int, int]], turns: int = 1) -> tuple[tuple[int, int], ...]:
    result = normalize(shape)
    for _ in range(turns % 4):
        result = normalize((c, -r) for r, c in result)
    return result


def mirror(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return normalize((r, -c) for r, c in shape)


def rotation_class(shape: Iterable[tuple[int, int]]) -> frozenset[tuple[tuple[int, int], ...]]:
    base = normalize(shape)
    return frozenset(rotate(base, turns) for turns in range(4))


def _blank_like(grid):
    return [[0 for _ in row] for row in grid]


def _paint(out, cells, color=8):
    for r, c in cells:
        out[r][c] = color
    return out


def official_output(grid):
    """Independent transcription of the selected canonical rule."""
    comps = components(grid)
    templates = [cells for color, cells in comps if color == 1]
    if len(templates) != 1:
        raise ValueError(f"expected one color-1 template, found {len(templates)}")
    target = rotation_class(templates[0])
    out = _blank_like(grid)
    for color, cells in comps:
        if color == 3 and normalize(cells) in target:
            _paint(out, cells, 8)
    return out


def translation_only(grid):
    comps = components(grid)
    template = normalize(next(cells for color, cells in comps if color == 1))
    out = _blank_like(grid)
    for color, cells in comps:
        if color == 3 and normalize(cells) == template:
            _paint(out, cells, 8)
    return out


def reflection_allowed(grid):
    comps = components(grid)
    template = next(cells for color, cells in comps if color == 1)
    accepted = rotation_class(template) | rotation_class(mirror(template))
    out = _blank_like(grid)
    for color, cells in comps:
        if color == 3 and normalize(cells) in accepted:
            _paint(out, cells, 8)
    return out


def all_green(grid):
    out = _blank_like(grid)
    for color, cells in components(grid):
        if color == 3:
            _paint(out, cells, 8)
    return out


def color_agnostic(grid):
    comps = components(grid)
    template = next(cells for color, cells in comps if color == 1)
    accepted = rotation_class(template)
    out = _blank_like(grid)
    for color, cells in comps:
        if color not in (0, 1) and normalize(cells) in accepted:
            _paint(out, cells, 8)
    return out


def size_only(grid):
    comps = components(grid)
    template = next(cells for color, cells in comps if color == 1)
    out = _blank_like(grid)
    for color, cells in comps:
        if color == 3 and len(cells) == len(template):
            _paint(out, cells, 8)
    return out


RIVALS = {
    "translation_only": translation_only,
    "reflection_allowed": reflection_allowed,
    "all_green": all_green,
    "color_agnostic": color_agnostic,
    "size_only": size_only,
}


def observed(grid):
    comps = components(grid)
    template = next(cells for color, cells in comps if color == 1)
    accepted = rotation_class(template)
    threes = [cells for color, cells in comps if color == 3]
    others = [cells for color, cells in comps if color not in (1, 3)]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "template_size": len(template),
        "n_match": sum(normalize(cells) in accepted for cells in threes),
        "n_nonmatch": sum(normalize(cells) not in accepted for cells in threes),
        "n_other_match": sum(normalize(cells) in accepted for cells in others),
    }


def canonical_pairs():
    from reviewer_support import canonical_pairs as load_pairs, find_root
    return load_pairs(TASK, root=find_root(__file__), labeled_only=True)


def audit(module, samples_per_band: int = 128):
    canonical = canonical_pairs()
    canonical_mismatches = [i for i, pair in enumerate(canonical)
                            if official_output(pair["input"]) != pair["output"]]
    canonical_self_check = [module.self_check(pair["input"]) for pair in canonical]
    totals = Counter()
    by_band = {}
    for band in ("easy", "medium", "hard"):
        counts = Counter()
        unique = set()
        for i in range(samples_per_band):
            grid = module.generate(9000 + i, i, difficulty=band)
            counts["samples"] += 1
            counts["self_check_failures"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(9000 + i, i, difficulty=band)
            intended = official_output(grid)
            for name, rival in RIVALS.items():
                counts[f"refutes_{name}"] += rival(grid) != intended
            unique.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
        counts["unique_inputs"] = len(unique)
        by_band[band] = dict(counts)
        totals.update(counts)
    return {
        "schema": "e4351af561ac-independent-audit-v1",
        "version": module.VERSION,
        "canonical_mismatches": canonical_mismatches,
        "canonical_self_check": canonical_self_check,
        "totals": dict(totals),
        "by_band": by_band,
        "warning": "Python oracle is supplementary; canonical Racket remains label authority.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator")
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.samples)
    report["generator_sha256"] = hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return int(bool(report["canonical_mismatches"])
               or any(report["canonical_self_check"])
               or report["totals"].get("self_check_failures", 0)
               or report["totals"].get("nondeterministic", 0))


if __name__ == "__main__":
    raise SystemExit(main())
