#!/usr/bin/env python3
"""Bounded adversarial-witness probe for 02dc25c0440b."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
REPO = next(parent / "repo" for parent in HERE.parents if (parent / "repo" / "shared" / "runtime").is_dir())
for path in (REPO / "shared" / "runtime", REPO / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from reviewer_support import canonical_path, load_selected_generator  # noqa: E402

TASK_ID = "02dc25c0440b"
TICKET_ID = "ticket-790ab6c71b4fffd3"
PINNED_GENERATOR_SHA256 = "19dc63b1aa479f1f40e86bbf93eae65a204bcf902abbc20ea6514048cb696aaf"
PINNED_RULE_HASH = "26aef6bd40c2"
SEED_HEX = "a1b569726e3c30065ca9e3b23e3f032051ee4c253d82b3a2f1f11a860afbaf89"
MAX_DRAWS = 64


def canonical_row() -> dict:
    for line in canonical_path(REPO).open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise KeyError(TASK_ID)


def rule_body(program: str) -> str:
    text = program.strip()
    if not text.startswith("(rule!") or not text.endswith(")"):
        raise ValueError("expected canonical (rule! BODY) program")
    return text[len("(rule!") : -1].strip()


def guide_column(grid: list[list[int]]) -> int:
    h, w = len(grid), len(grid[0])
    columns = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(columns) != 1:
        raise ValueError(f"expected one guide column, got {columns}")
    return columns[0]


def one_color_shortcut(grid: list[list[int]]) -> tuple[list[list[int]], int]:
    """Mirror only the most frequent left-side color; ties choose the lowest."""
    gc = guide_column(grid)
    counts = Counter(
        grid[r][c]
        for r in range(len(grid))
        for c in range(gc)
        if grid[r][c] not in (0, 9)
    )
    selected = min(counts, key=lambda color: (-counts[color], color))
    out = [row[:] for row in grid]
    for r in range(len(grid)):
        for c in range(gc):
            if grid[r][c] != selected:
                continue
            mc = 2 * gc - c
            if 0 <= mc < len(grid[0]):
                out[r][mc] = selected
    return out, selected


def main() -> int:
    module, source, digest = load_selected_generator(TASK_ID, root=REPO)
    if digest != PINNED_GENERATOR_SHA256:
        raise RuntimeError(f"generator changed: {digest}")
    row = canonical_row()
    program = row["program_solution"]
    seed = int(SEED_HEX[:16], 16) % (2**31)

    candidate = None
    for sample_index in range(MAX_DRAWS):
        grid = module.generate(seed, sample_index, difficulty="hard", texture="plain")
        errors = module.self_check(grid, difficulty="hard")
        if errors:
            continue
        gc = guide_column(grid)
        colors = sorted(
            {
                grid[r][c]
                for r in range(len(grid))
                for c in range(gc)
                if grid[r][c] not in (0, 9)
                and 0 <= 2 * gc - c < len(grid[0])
            }
        )
        if len(colors) >= 2:
            candidate = (sample_index, grid, errors, gc, colors)
            break
    if candidate is None:
        raise RuntimeError(f"no lawful two-color witness in {MAX_DRAWS} bounded draws")

    sample_index, grid, errors, gc, colors = candidate
    shortcut_output, selected_color = one_color_shortcut(grid)
    with RacketBridge() as bridge:
        bridge.define_grid("g", grid)
        correct_output = bridge.eval_text(rule_body(program))

    differing_cells = [
        [r, c, correct_output[r][c], shortcut_output[r][c]]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if correct_output[r][c] != shortcut_output[r][c]
    ]
    omitted_in_bounds = [
        [r, c, grid[r][c], 2 * gc - c]
        for r in range(len(grid))
        for c in range(gc)
        if grid[r][c] not in (0, 9, selected_color)
        and 0 <= 2 * gc - c < len(grid[0])
    ]
    passed = bool(differing_cells and omitted_in_bounds and not errors)
    report = {
        "schema": "arcpuzzles-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "type": "adversarial_witness",
        "status": "completed" if passed else "unknown",
        "consumer": "target_current_audit",
        "task_id": TASK_ID,
        "source": {
            "path": str(source.relative_to(REPO)),
            "sha256": digest,
            "pinned_sha256": PINNED_GENERATOR_SHA256,
        },
        "rule": {
            "pinned_rule_hash": PINNED_RULE_HASH,
            "program_sha256": hashlib.sha256(program.encode("utf-8")).hexdigest(),
            "authority": "canonical program_solution executed by protected RacketBridge",
        },
        "probe": {
            "seed_hex": SEED_HEX,
            "seed_int": seed,
            "sample_index": sample_index,
            "difficulty": "hard",
            "overrides": {"texture": "plain"},
            "bounded_draws": sample_index + 1,
            "maximum_draws": MAX_DRAWS,
        },
        "shortcut": {
            "name": "mirror_only_most_frequent_left_color",
            "description": "Mirror only one selected left-side color/object class instead of every colored left cell.",
            "selected_color": selected_color,
        },
        "witness": {
            "guide_column": gc,
            "in_bounds_left_colors": colors,
            "self_check": errors,
            "input": grid,
            "canonical_racket_output": correct_output,
            "shortcut_output": shortcut_output,
            "differing_cells": differing_cells,
            "omitted_in_bounds_source_cells": omitted_in_bounds,
            "outputs_differ": correct_output != shortcut_output,
        },
        "conclusion": (
            "A lawful generated case contains multiple independently mirrored colors; "
            "the one-color shortcut omits visible mirrored cells."
            if passed
            else "The bounded probe did not establish the intended distinction."
        ),
    }
    out = HERE.with_name("report.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "sample_index": sample_index,
        "colors": colors,
        "selected_color": selected_color,
        "differing_cells": len(differing_cells),
        "report": str(out),
    }, indent=2, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
