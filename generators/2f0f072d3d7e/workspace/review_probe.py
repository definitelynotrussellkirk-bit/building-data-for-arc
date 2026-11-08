"""Independent geometry oracle and reusable lesson audit for 2f0f072d3d7e.

This helper intentionally reconstructs the rule from panel matrices instead of
calling generator internals.  It is authoring/test tooling, not label authority.
Never import it during a visible-only solve.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
from pathlib import Path

TASK_ID = "2f0f072d3d7e"


def load_generator(path=None):
    candidate = path or os.environ.get("GENERATOR_UNDER_TEST")
    if candidate:
        source = Path(candidate)
        if source.is_dir():
            source = source / "generator.py"
    else:
        source = Path(__file__).resolve().parents[1] / "generator.py"
    if source.exists():
        spec = importlib.util.spec_from_file_location("reviewed_generator", source)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )


def split_panels(grid):
    """Return equal panel matrices split on full color-9 columns."""
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        raise ValueError("ragged grid")
    cuts = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    bounds = [-1] + cuts + [w]
    return [[row[a + 1:b] for row in grid] for a, b in zip(bounds, bounds[1:])]


def raw_support(panel):
    return tuple(
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, 9)
    )


def normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def rotate_cw(cells):
    cells = normalize(cells)
    if not cells:
        return ()
    h = max(r for r, _ in cells) + 1
    return normalize((c, h - 1 - r) for r, c in cells)


def reflect_lr(cells):
    cells = normalize(cells)
    if not cells:
        return ()
    w = max(c for _, c in cells) + 1
    return normalize((r, w - 1 - c) for r, c in cells)


def transform(cells, code):
    cells = normalize(cells)
    if code == 4:
        return reflect_lr(cells)
    for _ in range(code):
        cells = rotate_cw(cells)
    return cells


def identify(a, b):
    target = normalize(b)
    for code in range(4):
        if transform(a, code) == target:
            return code
    if reflect_lr(a) == target:
        return 4
    return 0


def parsed(grid):
    ps = split_panels(grid)
    if len(ps) < 5:
        raise ValueError("need A, B, C and at least two candidates")
    supports = [raw_support(p) for p in ps]
    code = identify(supports[0], supports[1])
    target = transform(supports[2], code)
    hits = [i for i, cells in enumerate(supports[3:]) if normalize(cells) == target]
    return ps, supports, code, target, hits


def paint(cells, side, color=8):
    occupied = set(cells)
    return [
        [color if (r, c) in occupied else 0 for c in range(side)]
        for r in range(side)
    ]


def oracle(grid):
    ps, supports, _code, _target, hits = parsed(grid)
    if not hits:
        return [[0 for _ in range(len(ps[3][0]))] for _ in range(len(ps[3]))]
    return paint(supports[3 + hits[0]], len(ps[3]), 8)


def first_candidate(grid):
    ps = split_panels(grid)
    return paint(raw_support(ps[3]), len(ps[3]), 8)


def inverse_transform(grid):
    ps, supports, code, _target, _hits = parsed(grid)
    inverse = {0: 0, 1: 3, 2: 2, 3: 1, 4: 4}[code]
    target = transform(supports[2], inverse)
    for cells in supports[3:]:
        if normalize(cells) == target:
            return paint(cells, len(ps[3]), 8)
    return [[0 for _ in range(len(ps[3][0]))] for _ in range(len(ps[3]))]


def normalized_output(grid):
    ps, supports, _code, _target, hits = parsed(grid)
    if not hits:
        return [[0 for _ in range(len(ps[3][0]))] for _ in range(len(ps[3]))]
    return paint(normalize(supports[3 + hits[0]]), len(ps[3]), 8)


def copy_c(grid):
    ps = split_panels(grid)
    return paint(raw_support(ps[2]), len(ps[2]), 8)


def observed(grid):
    ps, supports, code, _target, hits = parsed(grid)
    if len(hits) != 1:
        raise ValueError(f"expected one winner, found {hits}")
    return {
        "panel_s": len(ps[0]),
        "n_candidates": len(ps) - 3,
        "shape_size_a": len(supports[0]),
        "shape_size_c": len(supports[2]),
        "transform_code": code,
        "winner_rank": hits[0],
    }


def canonical_pairs():
    from reviewer_support import canonical_pairs as read_pairs, find_root

    return read_pairs(TASK_ID, root=find_root(__file__))


def cyclic_rivals(module, pairs):
    """Hold out each pair once; report rivals fitting all other examples."""
    declarations = {}
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        for name, fn in getattr(module, namespace, {}).items():
            declarations[f"{namespace}:{name}"] = fn
    ambiguous = []
    counts = {name: {"windows": 0, "ambiguous": 0} for name in declarations}
    for name, fn in declarations.items():
        fits = [fn(pair["input"]) == pair["output"] for pair in pairs]
        for query in range(len(pairs)):
            counts[name]["windows"] += 1
            demo_fit = all(ok for i, ok in enumerate(fits) if i != query)
            if demo_fit and not fits[query]:
                counts[name]["ambiguous"] += 1
                ambiguous.append({"rival": name, "query_index": query})
    return {"counts": counts, "ambiguities": ambiguous}


def write_probe(seed=17, start=0, band="medium", out=None):
    """Materialize six source-only examples and summarize exact geometry."""
    gen = load_generator()
    rows = []
    for offset in range(6):
        grid = gen.generate(seed, start + offset, difficulty=band)
        rows.append({
            "sample_index": start + offset,
            "observed": observed(grid),
            "input": grid,
            "oracle_output": oracle(grid),
        })
    payload = {
        "task_id": TASK_ID,
        "seed": seed,
        "start": start,
        "band": band,
        "rows": rows,
    }
    if out is not None:
        Path(out).write_text(json.dumps(payload, indent=2) + "\n")
    return payload
