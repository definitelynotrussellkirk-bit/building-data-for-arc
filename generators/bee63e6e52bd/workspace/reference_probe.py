"""Independent review oracle and retained counterexample probe for bee63e6e52bd.

This module deliberately does not import the generator's geometry or Python
rule mirror.  It reconstructs the one-gap frame directly from a grid and
implements the selected Racket rule from that visible structure.  Review tests
use it to avoid accepting a generator and its own mirror by circular agreement.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

TASK_ID = "bee63e6e52bd"
HERE = Path(__file__).resolve()
for candidate in (HERE.parent, *HERE.parents):
    for support in (candidate / "reviewer_support.py", candidate / "shared" / "runtime" / "reviewer_support.py"):
        if support.is_file():
            if str(support.parent) not in sys.path:
                sys.path.insert(0, str(support.parent))
            break
    else:
        continue
    break
else:  # pragma: no cover - CLI import failure is intentionally explicit
    raise ImportError("cannot locate portable reviewer_support.py")

from reviewer_support import canonical_pairs, find_root  # noqa: E402

ROOT = find_root(__file__)


def load_generator(path: Path | None = None):
    source = path or ROOT / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_generator_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def labeled_canonical_pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _validated_grid(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    rows = []
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("cells must be integer ARC colors 0..9")
        rows.append(list(row))
    return rows


def shape_facts(grid: Iterable[Iterable[int]]) -> dict:
    """Infer the frame, open side, gap, and arm lengths from pixels only."""
    rows = _validated_grid(grid)
    h, w = len(rows), len(rows[0])
    colors = sorted({value for row in rows for value in row if value != 0})
    if len(colors) != 1 or colors[0] == 4:
        raise ValueError(f"expected one nonzero, non-4 shape color; found {colors}")
    color = colors[0]
    cells = {(r, c) for r, row in enumerate(rows) for c, value in enumerate(row) if value == color}
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
        raise ValueError("frame bbox must be at least 3x3")
    corners = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
    if not corners <= cells:
        raise ValueError("all four bbox corners must be shape-colored")
    perimeter = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    extras = sorted(cells - perimeter)
    if extras:
        raise ValueError(f"shape cells occur inside the bbox: {extras[:4]}")

    sequences = {
        "top": [(r0, c) in cells for c in range(c0, c1 + 1)],
        "bottom": [(r1, c) in cells for c in range(c0, c1 + 1)],
        "left": [(r, c0) in cells for r in range(r0, r1 + 1)],
        "right": [(r, c1) in cells for r in range(r0, r1 + 1)],
    }
    incomplete = [side for side, occupied in sequences.items() if not all(occupied)]
    if len(incomplete) != 1:
        raise ValueError(f"expected exactly one incomplete side; found {incomplete}")
    side = incomplete[0]
    occupied = sequences[side]
    missing = [index for index, value in enumerate(occupied) if not value]
    if not missing or missing != list(range(missing[0], missing[-1] + 1)):
        raise ValueError("open-side gap must be one nonempty contiguous run")
    arm_before = missing[0]
    arm_after = len(occupied) - missing[-1] - 1
    if arm_before < 1 or arm_after < 1:
        raise ValueError("both mouth arms must retain their corner")
    if side == "left" and c0 == 0:
        raise ValueError("left-facing mouth has no outward cell")
    if side == "right" and c1 == w - 1:
        raise ValueError("right-facing mouth has no outward cell")
    if side == "top" and r0 == 0:
        raise ValueError("top-facing mouth has no outward cell")
    if side == "bottom" and r1 == h - 1:
        raise ValueError("bottom-facing mouth has no outward cell")
    return {
        "height": h,
        "width": w,
        "color": color,
        "bbox": (r0, c0, r1, c1),
        "open_side": side,
        "gap_start": missing[0],
        "gap_end": missing[-1],
        "arm_before": arm_before,
        "arm_after": arm_after,
    }


def _paint_zero(out: list[list[int]], r: int, c: int) -> None:
    if 0 <= r < len(out) and 0 <= c < len(out[0]) and out[r][c] == 0:
        out[r][c] = 4


def _pour_with_assumed_arms(grid: list[list[int]], before: int, after: int) -> list[list[int]]:
    rows = _validated_grid(grid)
    facts = shape_facts(rows)
    out = copy.deepcopy(rows)
    h, w = facts["height"], facts["width"]
    r0, c0, r1, c1 = facts["bbox"]
    side = facts["open_side"]

    if side in ("left", "right"):
        top_tip = r0 + before - 1
        bottom_tip = r1 - after + 1
        mouth_c = c0 - 1 if side == "left" else c1 + 1
        for r in range(top_tip + 1, bottom_tip):
            columns = range(0, c1 + 1) if side == "left" else range(c0, w)
            for c in columns:
                _paint_zero(out, r, c)
        for r in (top_tip, bottom_tip):
            _paint_zero(out, r, mouth_c)
            interior = range(c0 + 1, c1 + 1) if side == "left" else range(c0, c1)
            for c in interior:
                _paint_zero(out, r, c)
        outward = -1 if side == "left" else 1
        for distance in range(1, max(h, w) + 1):
            _paint_zero(out, top_tip - distance, mouth_c + outward * distance)
            _paint_zero(out, bottom_tip + distance, mouth_c + outward * distance)
    else:
        left_tip = c0 + before - 1
        right_tip = c1 - after + 1
        mouth_r = r0 - 1 if side == "top" else r1 + 1
        for c in range(left_tip + 1, right_tip):
            rows_to_fill = range(0, r1 + 1) if side == "top" else range(r0, h)
            for r in rows_to_fill:
                _paint_zero(out, r, c)
        for c in (left_tip, right_tip):
            _paint_zero(out, mouth_r, c)
            interior = range(r0 + 1, r1 + 1) if side == "top" else range(r0, r1)
            for r in interior:
                _paint_zero(out, r, c)
        outward = -1 if side == "top" else 1
        for distance in range(1, max(h, w) + 1):
            _paint_zero(out, mouth_r + outward * distance, left_tip - distance)
            _paint_zero(out, mouth_r + outward * distance, right_tip + distance)
    return out


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    facts = shape_facts(grid)
    return _pour_with_assumed_arms(grid, facts["arm_before"], facts["arm_after"])


def fixed_two_arms(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule that fits every canonical pair exactly."""
    return _pour_with_assumed_arms(grid, 2, 2)


def witness_input() -> list[list[int]]:
    """A compact lawful right-open frame with 1/3 arms."""
    grid = [[0] * 7 for _ in range(7)]
    color = 8
    r0, c0, r1, c1 = 1, 0, 5, 4
    for c in range(c0, c1 + 1):
        grid[r0][c] = grid[r1][c] = color
    for r in range(r0, r1 + 1):
        grid[r][c0] = color
    # Right side: one cell from the top and three from the bottom.
    grid[r0][c1] = color
    for r in range(r1 - 2, r1 + 1):
        grid[r][c1] = color
    return grid


def audit(module, count: int = 64) -> dict:
    canonical = labeled_canonical_pairs()
    report = {
        "schema": f"{TASK_ID}-independent-review-v1",
        "generator_version": getattr(module, "VERSION", None),
        "generator_sha256": hashlib.sha256(
            (ROOT / "generators" / TASK_ID / "generator.py").read_bytes()
        ).hexdigest(),
        "canonical": {
            "pairs": len(canonical),
            "oracle_matches": sum(intended_output(pair["input"]) == pair["output"] for pair in canonical),
            "fixed_two_matches": sum(fixed_two_arms(pair["input"]) == pair["output"] for pair in canonical),
            "self_check_errors": [module.self_check(pair["input"]) for pair in canonical],
        },
        "bands": {},
    }
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        seen = set()
        for index in range(count):
            grid = module.generate(8100 + index, index, difficulty=band)
            facts = shape_facts(grid)
            is_canonical_arms = (facts["arm_before"], facts["arm_after"]) == (2, 2)
            counts["draws"] += 1
            counts["valid"] += not module.self_check(grid)
            counts["deterministic"] += grid == module.generate(8100 + index, index, difficulty=band)
            counts["canonical_arm_draws"] += is_canonical_arms
            counts["counterexample_draws"] += not is_canonical_arms
            counts["shortcut_disagreement"] += intended_output(grid) != fixed_two_arms(grid)
            seen.add(json.dumps(grid, separators=(",", ":")))
        counts["unique_inputs"] = len(seen)
        report["bands"][str(band)] = dict(counts)
    witness = witness_input()
    report["witness"] = {
        "input": witness,
        "facts": shape_facts(witness),
        "intended": intended_output(witness),
        "fixed_two_arms": fixed_two_arms(witness),
    }
    failures = []
    canonical_report = report["canonical"]
    if canonical_report["oracle_matches"] != canonical_report["pairs"]:
        failures.append("independent oracle does not match every canonical label")
    if canonical_report["fixed_two_matches"] != canonical_report["pairs"]:
        failures.append("declared canonical shortcut does not fit every canonical label")
    if any(canonical_report["self_check_errors"]):
        failures.append("generator rejects at least one canonical input")
    for band, values in report["bands"].items():
        if values["valid"] != values["draws"]:
            failures.append(f"{band}: invalid generated draw")
        if values["deterministic"] != values["draws"]:
            failures.append(f"{band}: nondeterministic generated draw")
        if values["shortcut_disagreement"] != values["counterexample_draws"]:
            failures.append(f"{band}: fixed-two shortcut mismatch does not track non-2/2 arms")
        if values["counterexample_draws"] == 0:
            failures.append(f"{band}: no generated shortcut counterexample")
    if report["witness"]["intended"] == report["witness"]["fixed_two_arms"]:
        failures.append("compact witness does not refute the shortcut")
    report["failures"] = failures
    report["status"] = "pass" if not failures else "fail"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    module = load_generator(args.generator)
    report = audit(module, args.count)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return int(report["status"] != "pass")


if __name__ == "__main__":
    raise SystemExit(main())
