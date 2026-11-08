from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter, deque
from pathlib import Path
from typing import Iterable

from reviewer_support import canonical_pairs, find_root

TASK_ID = "c8e53a07acc8"
SOURCE_SHA256 = "312e7083ffb6ad87018ecca3b069d769236104e8e872605178cb9bc16c2af30f"
RULE_HASH12 = "559aa4d81a8f"
ADJ8 = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]


def load_generator(root: Path):
    path = root / "generators" / TASK_ID / "generator.py"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == SOURCE_SHA256
    spec = importlib.util.spec_from_file_location("audit_c8_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def mode(grid: list[list[int]]) -> int:
    counts = Counter(v for row in grid for v in row)
    return max(counts, key=counts.get)


def components(grid: list[list[int]], bg: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == bg:
                continue
            seen.add((r, c))
            q = deque([(r, c)])
            comp: list[tuple[int, int]] = []
            while q:
                rr, cc = q.popleft()
                comp.append((rr, cc))
                for dr, dc in ADJ8:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] != bg
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            result.append(comp)
    return result


def apply_templates(grid: list[list[int]], *, first_template_only: bool) -> list[list[int]]:
    """Python mirror of the canonical rule, optionally truncating template iteration."""
    h, w = len(grid), len(grid[0])
    bg = mode(grid)
    comps = components(grid, bg)
    colors_of = lambda cells: list(dict.fromkeys(grid[r][c] for r, c in cells))
    singles = [cells for cells in comps if len(colors_of(cells)) == 1]
    templates = [cells for cells in comps if len(colors_of(cells)) > 1]
    if first_template_only:
        templates = templates[:1]
    out = [row[:] for row in grid]

    for cells in templates:
        colors = colors_of(cells)
        def count_color(color: int) -> int:
            return sum(grid[r][c] == color for r, c in cells)
        anchor_colors = [
            color for color in colors
            if any(grid[obj[0][0]][obj[0][1]] == color and len(obj) == count_color(color)
                   for obj in singles)
        ]
        anchor_cells = [(r, c) for r, c in cells if grid[r][c] in anchor_colors]
        non_anchor = [(r, c) for r, c in cells if grid[r][c] not in anchor_colors]
        stamped = False
        for ar, ac in anchor_cells:
            color = grid[ar][ac]
            cnt = count_color(color)
            targets = [p for obj in singles
                       if grid[obj[0][0]][obj[0][1]] == color and len(obj) == cnt
                       for p in obj]
            for tr, tc in targets:
                dr, dc = tr - ar, tc - ac
                anchors_ok = all(
                    0 <= rr + dr < h and 0 <= cc + dc < w
                    and grid[rr + dr][cc + dc] == grid[rr][cc]
                    for rr, cc in anchor_cells
                )
                fills_bg = any(
                    0 <= rr + dr < h and 0 <= cc + dc < w
                    and grid[rr + dr][cc + dc] == bg
                    for rr, cc in non_anchor
                )
                if anchors_ok and fills_bg:
                    stamped = True
                    for rr, cc in cells:
                        nr, nc = rr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            out[nr][nc] = grid[rr][cc]
        if stamped:
            for rr, cc in non_anchor:
                if count_color(grid[rr][cc]) == 1:
                    out[rr][cc] = bg
    return out


def structural_summary(grid: list[list[int]]) -> dict:
    bg = mode(grid)
    comps = components(grid, bg)
    color_counts = [len({grid[r][c] for r, c in comp}) for comp in comps]
    return {
        "shape": [len(grid), len(grid[0])],
        "background": bg,
        "component_count": len(comps),
        "multicolor_template_count": sum(n > 1 for n in color_counts),
        "single_color_component_count": sum(n == 1 for n in color_counts),
        "palette_size": len({v for row in grid for v in row}),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--inputs-out", required=True)
    parser.add_argument("--racket")
    args = parser.parse_args()

    root = find_root(Path.cwd())
    gen = load_generator(root)
    generated = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(10):
            seed = 7000 + 100 * band_index + index
            grid = gen.generate(seed, index, difficulty=band)
            errors = gen.self_check(grid, difficulty=band)
            generated.append({
                "band": band,
                "seed": seed,
                "sample_index": index,
                "self_check": errors,
                "input": grid,
                "structure": structural_summary(grid),
                "single_template_rival": apply_templates(grid, first_template_only=True),
            })

    Path(args.inputs_out).write_text(json.dumps({"inputs": [x["input"] for x in generated]}, separators=(",", ":")))

    canonical = canonical_pairs(TASK_ID, root=root, variant=0, labeled_only=True)
    canonical_rows = []
    mirror_mismatches = []
    rival_differences = []
    canonical_counterexample = None
    for pair in canonical:
        full = apply_templates(pair["input"], first_template_only=False)
        rival = apply_templates(pair["input"], first_template_only=True)
        key = {"split": pair["split"], "pair_index": pair["pair_index"]}
        if full != pair["output"]:
            mirror_mismatches.append(key)
        if rival != pair["output"]:
            diff = sum(a != b for ra, rb in zip(rival, pair["output"]) for a, b in zip(ra, rb))
            rival_differences.append({**key, "differing_cells": diff})
            if canonical_counterexample is None:
                canonical_counterexample = {
                    **key,
                    "input": pair["input"],
                    "actual_canonical_output": pair["output"],
                    "single_template_rival_output": rival,
                    "differing_cells": diff,
                    "structure": structural_summary(pair["input"]),
                }
        canonical_rows.append({**key, "structure": structural_summary(pair["input"])})

    racket_matches = None
    racket_record = None
    if args.racket:
        racket_record = json.loads(Path(args.racket).read_text())
        outputs = racket_record.get("outputs")
        if outputs is None and "output" in racket_record:
            outputs = [racket_record["output"]]
        if outputs is None and isinstance(racket_record.get("results"), list):
            outputs = [row.get("output") for row in racket_record["results"]]
        if outputs is not None:
            racket_matches = [
                generated[i]["single_template_rival"] == output
                for i, output in enumerate(outputs)
            ]

    result = {
        "schema": "audit-single-template-rival-v1",
        "task_id": TASK_ID,
        "generator_sha256": SOURCE_SHA256,
        "declared_rule_hash_expected": RULE_HASH12,
        "command": "PYTHONPATH=shared/runtime python3 ../checks/audit/c8e53a07acc8/probe_single_template.py ...",
        "generated": {
            "count": len(generated),
            "seed_ranges": {"easy": [7000, 7009], "medium": [7100, 7109], "hard": [7200, 7209]},
            "self_check_failures": sum(bool(x["self_check"]) for x in generated),
            "template_counts": Counter(x["structure"]["multicolor_template_count"] for x in generated),
            "palette_sizes": Counter(x["structure"]["palette_size"] for x in generated),
            "single_template_rival_matches_racket": None if racket_matches is None else sum(racket_matches),
            "single_template_rival_racket_total": None if racket_matches is None else len(racket_matches),
            "examples": [{k: x[k] for k in ("band", "seed", "sample_index", "structure", "self_check")} for x in generated[:6]],
        },
        "canonical_variant_0": {
            "pair_count": len(canonical),
            "full_python_mirror_mismatches": mirror_mismatches,
            "single_template_rival_differences": rival_differences,
            "pairs": canonical_rows,
            "counterexample": canonical_counterexample,
        },
        "racket_record": None if racket_record is None else {
            "path": args.racket,
            "schema": racket_record.get("schema"),
            "executed_rule_hash": racket_record.get("executed_rule_hash"),
            "rule_text_sha256": racket_record.get("rule_text_sha256"),
            "generator_sha256": racket_record.get("generator_sha256"),
            "command": racket_record.get("command"),
            "cwd": racket_record.get("cwd"),
        },
    }
    Path(args.out).write_text(json.dumps(result, indent=2, default=lambda x: dict(x)))
    print(json.dumps(result, indent=2, default=lambda x: dict(x)))


if __name__ == "__main__":
    main()
