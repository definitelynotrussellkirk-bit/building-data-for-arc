#!/usr/bin/env python3
"""One bounded overlap witness for ticket-7826a0e04c70e5fa."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import find_root, load_selected_generator
from puzzle_generators.rule_wrap import strip_line_comments as runtime_strip_comments, strip_rule_wrapper

TASK_ID = "026edc506fe6"
TICKET_ID = "ticket-7826a0e04c70e5fa"
PINNED_GENERATOR_SHA256 = "d0849f6305e8df540f5e7a74f70234d3725abef3d43c168451146015bb6aa733"
PINNED_RULE_HASH = "7be9f4d727bc"
PROBE_SEED = "17c60a944870a0c950d16f5eb3f5e06c22fdebea43652001e28f24e2105538f9"
ROOT = find_root(__file__)
OUT = ROOT.parent / "checks" / "tickets" / TICKET_ID / "result.json"
CANONICAL = (
    ROOT
    / "shared/data/base/solutions/banks/b18129f611a9/M134__026edc506fe6.json"
)


def json_sha256(value) -> str:
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return hashlib.sha256(raw).hexdigest()


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def strip_line_comments(source: str) -> str:
    return "\n".join(line.split(";", 1)[0] for line in source.splitlines())


def cells(grid, color: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }


def execute(source: str, grid: list[list[int]]) -> list[list[int]]:
    # This exact rule uses only a bare body with free `g`; the sparse review
    # bundle omits the `scripts.comment_solutions` dependency required by the
    # general wrap_rule pipeline.  Reuse its comment/wrapper parsers and apply
    # the one necessary callable wrapper for this pinned source.
    clean = runtime_strip_comments(source)
    body = strip_rule_wrapper(clean)
    assert "{" not in body and "(for/" not in body
    wrapped = f"(lambda (g) {body})"
    with RacketBridge(timeout=30.0) as bridge:
        bridge.eval_text(f"(define __ticket_rule {wrapped})")
        bridge.define_grid("__ticket_input", grid)
        return bridge.eval_text("(__ticket_rule __ticket_input)")


def main() -> int:
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    assert hashlib.sha256(Path(source_path).read_bytes()).hexdigest() == source_sha256
    assert source_sha256 == PINNED_GENERATOR_SHA256

    record = json.loads(CANONICAL.read_text(encoding="utf-8"))
    # The ticket hash pins the archival executable source.  The selected target
    # differs only by comments, so retain and verify both authority forms.
    source = record["racket_target"]["raw_code"]
    selected_source = record["racket_target"]["target_code"]
    rule_hash = normalized_rule_hash(source)
    selected_semantic_hash = normalized_rule_hash(strip_line_comments(selected_source))
    assert rule_hash == selected_semantic_hash == PINNED_RULE_HASH

    witness = None
    for sample_index in range(64):
        grid = generator.generate(
            PROBE_SEED,
            sample_index,
            difficulty="medium",
            texture="overlap",
        )
        if generator.self_check(grid):
            continue
        reds = cells(grid, 2)
        greens = cells(grid, 3)
        blues = cells(grid, 1)
        if len(reds) != 1 or len(greens) != 1 or len(blues) < 2:
            continue
        red = next(iter(reds))
        green = next(iter(greens))
        delta = (green[0] - red[0], green[1] - red[1])
        moved = {(r + delta[0], c + delta[1]) for r, c in blues}
        overlap = moved & blues
        if not overlap:
            continue
        if not all(0 <= r < len(grid) and 0 <= c < len(grid[0]) for r, c in moved):
            continue
        witness = {
            "sample_index": sample_index,
            "input": grid,
            "red": list(red),
            "green": list(green),
            "delta": list(delta),
            "blue_cells": [list(p) for p in sorted(blues)],
            "translated_cells": [list(p) for p in sorted(moved)],
            "overlap_cells": [list(p) for p in sorted(overlap)],
        }
        break
    assert witness is not None, "bounded search found no lawful overlap witness"

    grid = witness["input"]
    actual = execute(source, grid)
    moved = {tuple(p) for p in witness["translated_cells"]}
    overlap = {tuple(p) for p in witness["overlap_cells"]}

    intended = copy.deepcopy(grid)
    for r, c in moved:
        intended[r][c] = 4
    assert actual == intended
    assert all(actual[r][c] == 4 for r, c in overlap)

    # Plausible shortcut: paint the translated copy only on background cells,
    # preserving every original blue cell and therefore assuming no overlap.
    shortcut = copy.deepcopy(grid)
    blue_cells = {tuple(p) for p in witness["blue_cells"]}
    for r, c in moved:
        if (r, c) not in blue_cells:
            shortcut[r][c] = 4
    differing = [
        [r, c, shortcut[r][c], actual[r][c]]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if shortcut[r][c] != actual[r][c]
    ]
    assert differing
    assert {tuple(row[:2]) for row in differing} == overlap

    result = {
        "schema": "arc-generator-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "consumer": "target_current_audit",
        "status": "completed",
        "probe_seed": PROBE_SEED,
        "sample_index": witness["sample_index"],
        "source": {
            "path": str(Path(source_path).relative_to(ROOT.parent)),
            "sha256": source_sha256,
            "pinned_sha256": PINNED_GENERATOR_SHA256,
            "matches_pin": True,
        },
        "rule": {
            "authority_path": str(CANONICAL.relative_to(ROOT)),
            "normalized_hash": rule_hash,
            "pinned_hash": PINNED_RULE_HASH,
            "matches_pin": True,
            "archival_program_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "selected_program_sha256": hashlib.sha256(selected_source.encode()).hexdigest(),
            "selected_comment_stripped_hash": selected_semantic_hash,
        },
        "runtime": racket_runtime_status(),
        "shortcut": (
            "Assume the translated yellow copy never overlaps the original blue "
            "shape; preserve blue cells instead of overpainting them."
        ),
        "witness": witness,
        "actual_output": actual,
        "shortcut_output": shortcut,
        "actual_output_sha256": json_sha256(actual),
        "shortcut_output_sha256": json_sha256(shortcut),
        "differing_cells": differing,
        "conclusion": (
            "A lawful overlap input makes the canonical Racket rule paint yellow "
            "over original blue cells, refuting the no-overlap shortcut."
        ),
        "limits": [
            "One bounded witness search over sample indices 0..63.",
            "No full peer battery, census, or general safety claim.",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "sample_index": witness["sample_index"],
                "overlap_cells": len(overlap),
                "differing_cells": len(differing),
                "result": str(OUT),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
