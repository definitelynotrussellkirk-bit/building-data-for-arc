"""Lesson-level rival audit for 61f255726e2e (bbox outline of every object).

Test tooling only; the canonical Racket rule stays the label authority. Reads
episodes written by `arcpuzzles generate ... --out FILE.jsonl` (Racket outputs)
and reports, per lesson (all train pairs + first test pair):

* whether the independent Python oracle reproduces every Racket output;
* for each rival rule, how often it fits every demo yet answers the query
  differently (the lesson cannot tell the two apart), and how often it fits
  every demo and the query (the lesson never exercises the difference);
* per-grid morphology: component count, bbox shapes, hollow interiors.

Usage, from the packet root:
  python3 repo/generators/61f255726e2e/workspace/lesson_rivals.py FILE.jsonl [...]
  python3 repo/generators/61f255726e2e/workspace/lesson_rivals.py --generator PATH [--lessons 300]

The second form is Python-only: it labels lessons with this file's oracle (no
Racket), using band in easy/medium/hard, seed 1000+k and sample indices 11k..11k+3,
three demos plus one query. Validate the oracle against Racket with the first form.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

N4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
N8 = N4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def components(grid, deltas=N4):
    """Same-color components in row-major discovery order, as the prelude does."""
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack, cells = [(r, c)], []
            seen.add((r, c))
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in deltas:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out


def bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _paint(base, objs, *, hollow):
    out = [list(row) for row in base]
    for color, cells in objs:
        r1, c1, r2, c2 = bbox(cells)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if not hollow or r in (r1, r2) or c in (c1, c2):
                    out[r][c] = color
    return out


def blank(grid):
    return [[0] * len(grid[0]) for _ in grid]


def oracle(grid):
    return _paint(blank(grid), components(grid), hollow=True)


def fill_bbox(grid):
    return _paint(blank(grid), components(grid), hollow=False)


def union_outline(grid):
    """Keep the blob and add the outline: never erases interior blob cells."""
    return _paint(grid, components(grid), hollow=True)


def outline_8conn(grid):
    return _paint(blank(grid), components(grid, N8), hollow=True)


def outline_per_color(grid):
    by_color = {}
    for color, cells in components(grid):
        by_color.setdefault(color, []).extend(cells)
    return _paint(blank(grid), sorted(by_color.items()), hollow=True)


RIVALS = {
    "fill_bbox": fill_bbox,
    "union_outline": union_outline,
    "outline_8conn": outline_8conn,
    "outline_per_color": outline_per_color,
}


def grid_facts(grid):
    objs = components(grid)
    hollow = interior_blob = 0
    shapes = Counter()
    for _, cells in objs:
        r1, c1, r2, c2 = bbox(cells)
        bh, bw = r2 - r1 + 1, c2 - c1 + 1
        shapes[f"{min(bh, bw)}x{max(bh, bw)}"] += 1
        if bh >= 3 and bw >= 3:
            hollow += 1
            if any(r1 < r < r2 and c1 < c < c2 for r, c in cells):
                interior_blob += 1
    colors = Counter(color for color, _ in objs)
    return {
        "objects": len(objs),
        "hollow_bboxes": hollow,
        "interior_blob_cells": interior_blob,
        "shapes": shapes,
        "repeated_color": any(n > 1 for n in colors.values()),
        "profile": (len(grid), len(grid[0]), len({v for row in grid for v in row})),
    }


def episodes(paths):
    for path in paths:
        for line in Path(path).open():
            row = json.loads(line)
            yield path, row


def pairs_of(row):
    ep = row.get("episode", row)
    train = ep.get("train") or row.get("train")
    test = ep.get("test") or row.get("test")
    return train, test


def main(paths):
    lessons = mismatch = 0
    ambiguous = Counter()
    never_exercised = Counter()
    grids = 0
    objects = Counter()
    shapes = Counter()
    hollow_grids = interior_grids = repeated = 0
    demo_hollow_lessons = demo_interior_lessons = 0
    examples = {}
    for path, row in episodes(paths):
        train, test = pairs_of(row)
        lesson = train + test[:1]
        lessons += 1
        for pair in train + test:
            if oracle(pair["input"]) != pair["output"]:
                mismatch += 1
            facts = grid_facts(pair["input"])
            grids += 1
            objects[facts["objects"]] += 1
            shapes.update(facts["shapes"])
            hollow_grids += facts["hollow_bboxes"] > 0
            interior_grids += facts["interior_blob_cells"] > 0
            repeated += facts["repeated_color"]
        demo_facts = [grid_facts(p["input"]) for p in train]
        demo_hollow_lessons += any(f["hollow_bboxes"] for f in demo_facts)
        demo_interior_lessons += any(f["interior_blob_cells"] for f in demo_facts)
        query = lesson[-1]
        for name, rival in RIVALS.items():
            fits = all(rival(p["input"]) == p["output"] for p in train)
            if not fits:
                continue
            if rival(query["input"]) != query["output"]:
                ambiguous[name] += 1
                examples.setdefault(name, {"file": str(path), "seed": row.get("seed"),
                                           "sample_index": row.get("sample_index"),
                                           "query_input": query["input"]})
            else:
                never_exercised[name] += 1
    report = {
        "lessons": lessons,
        "grids": grids,
        "oracle_mismatches": mismatch,
        "objects_per_grid": dict(sorted(objects.items())),
        "bbox_shapes_min_x_max": dict(shapes.most_common()),
        "grids_with_hollow_bbox": hollow_grids,
        "grids_with_blob_cell_inside_outline": interior_grids,
        "grids_with_repeated_color": repeated,
        "lessons_whose_demos_show_a_hollow_bbox": demo_hollow_lessons,
        "lessons_whose_demos_erase_an_interior_cell": demo_interior_lessons,
        "rival_fits_demos_but_wrong_on_query": dict(ambiguous),
        "rival_fits_whole_lesson": dict(never_exercised),
        "first_ambiguous_example": examples,
    }
    print(json.dumps(report, indent=1))


def python_only(generator_path, lessons, out_dir):
    import importlib.util
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("generator_under_audit", generator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    out_dir.mkdir(parents=True, exist_ok=True)
    for band in ("easy", "medium", "hard"):
        rows = []
        for k in range(lessons):
            pairs = []
            for i in range(4):
                grid = module.generate(1000 + k, k * 11 + i, difficulty=band)
                pairs.append({"input": grid, "output": oracle(grid)})
            rows.append({"seed": 1000 + k, "sample_index": k * 11, "train": pairs[:3], "test": pairs[3:]})
        path = out_dir / f"python_oracle_{band}.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        print(f"== {band}")
        main([str(path)])


if __name__ == "__main__":
    if sys.argv[1:2] == ["--generator"]:
        count = int(sys.argv[sys.argv.index("--lessons") + 1]) if "--lessons" in sys.argv else 300
        target = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else Path("lesson-audit")
        python_only(Path(sys.argv[2]), count, target)
    else:
        main(sys.argv[1:])
