#!/usr/bin/env python3
"""One bounded replay of the pinned singleton-corner audit witness."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "61c0bcd32328"
TICKET_ID = "ticket-842448bdd5ada342"
RETURN_ID = "review-51f76761d3848e0b:v0002"
AUDITED_SOURCE_SHA256 = "3c0cd7f5e883c70aa52eb73b2672bada64daf54461a909f0ed0e7fb0e058220a"
CURRENT_SOURCE_SHA256 = "4f45d334880485ba8e7926f352f6f9c919dad53df3a9b868af43703964dff4ec"
ASSET_MANIFEST_SHA256 = "5d11575b32a3d3c3e1b9389f7bbcfdb067fcbdbf697202d6f27f554ab95abfd6"
AUDIT_INDEX_SHA256 = "6576e819ebdc4c8e9cf53fafc058e82401aef0d0c4b347a5efc523b73a4e50b1"
AUDIT_RECORD_SHA256 = "365bfd6518e774bb57774dd42b5ebf340cf998ce443cbc57ead27bcd87d5f02e"
RULE_HASH = "e3835c9a174e"
BASE = REPO / "generators" / TASK / "counterexamples" / "review-51f76761d3848e0b-v0002"
RETAINED = BASE / "retained" / "checks" / "audit" / TASK
CURRENT_SOURCE = REPO / "generators" / TASK / "generator.py"
AUDITED_SOURCE = (
    REPO
    / "generators"
    / TASK
    / "evidence"
    / "owner-notes-merge-69a7900174b5588a"
    / "historical"
    / "before-files"
    / "generators"
    / TASK
    / "generator.py"
)
ASSET_MANIFEST = BASE / "audit_assets.json"
AUDIT_INDEX = REPO / "generators" / TASK / "evidence" / "review_index.json"
OUT = HERE / "replay.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(data)


def normalized_rule_hash(source: str) -> str:
    return sha256_bytes(" ".join(source.split()).encode())[:12]


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("ticket_generator_61c0_audited", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def components(grid: list[list[int]], background: int):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, list[tuple[int, int]]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == background or (row, col) in seen:
                continue
            color = grid[row][col]
            cells = {(row, col)}
            seen.add((row, col))
            todo = [(row, col)]
            while todo:
                current_row, current_col = todo.pop()
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        cells.add((next_row, next_col))
                        todo.append((next_row, next_col))
            result.append((color, sorted(cells)))
    return result


def ignore_singletons_rival(grid: list[list[int]]) -> list[list[int]]:
    """Apply the reference copy geometry, but treat singleton components as noise."""
    height, width = len(grid), len(grid[0])
    background = Counter(value for row in grid for value in row if value != 0).most_common(1)[0][0]
    output = [row[:] for row in grid]
    for color, cells in components(grid, background):
        if len(cells) == 1:
            continue
        min_row, max_row = min(row for row, _ in cells), max(row for row, _ in cells)
        min_col, max_col = min(col for _, col in cells), max(col for _, col in cells)
        if min_row == 0 and min_col == 0:
            delta_row, delta_col = 0, width - 1 - max_col
        elif min_row == 0 and max_col == width - 1:
            delta_row, delta_col = height - 1 - max_row, 0
        elif max_row == height - 1 and max_col == width - 1:
            delta_row, delta_col = 0, -min_col
        elif max_row == height - 1 and min_col == 0:
            delta_row, delta_col = -min_row, 0
        else:
            continue
        for row, col in cells:
            output[row + delta_row][col + delta_col] = color
    return output


def canonical_record():
    rows = []
    canonical = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in canonical.read_text(encoding="utf-8").splitlines():
        if TASK not in line:
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rows.append(row)
    assert rows
    programs = {row["program_solution"] for row in rows}
    assert len(programs) == 1
    pairs: dict[tuple[tuple[int, ...], ...], list[list[int]]] = {}
    occurrences = 0
    for row in rows:
        for split in ("train", "test"):
            examples = row[split]
            if isinstance(examples, dict):
                examples = [examples]
            for pair in examples:
                occurrences += 1
                input_key = tuple(tuple(int(value) for value in values) for values in pair["input"])
                pairs.setdefault(input_key, [[int(value) for value in values] for values in pair["output"]])
    return next(iter(programs)), pairs, occurrences


def main() -> int:
    if OUT.exists():
        raise FileExistsError(OUT)

    assert sha256_file(AUDITED_SOURCE) == AUDITED_SOURCE_SHA256
    assert sha256_file(CURRENT_SOURCE) == CURRENT_SOURCE_SHA256
    assert sha256_file(ASSET_MANIFEST) == ASSET_MANIFEST_SHA256
    assert sha256_file(AUDIT_INDEX) == AUDIT_INDEX_SHA256

    manifest = json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["return_id"] == RETURN_ID
    assert manifest["audited_generator_sha256"] == AUDITED_SOURCE_SHA256
    verified_assets = []
    for row in manifest["files"]:
        path = REPO / row["path"]
        actual = sha256_file(path)
        assert actual == row["sha256"], (path, actual, row["sha256"])
        assert path.stat().st_size == row["bytes"]
        verified_assets.append(
            {"path": str(path.relative_to(REPO)), "sha256": actual, "bytes": path.stat().st_size}
        )

    index = json.loads(AUDIT_INDEX.read_text(encoding="utf-8"))
    matching = [row for row in index["audits"] if row["return_id"] == RETURN_ID]
    assert len(matching) == 1
    audit_record = matching[0]
    assert sha256_json(audit_record) == AUDIT_RECORD_SHA256
    assert audit_record["source_sha256"] == AUDITED_SOURCE_SHA256
    assert audit_record["resolution"] == "needs_triage"

    generator = load_module(AUDITED_SOURCE)
    overrides = {"scene_profile": "single_tl"}
    control = generator.generate(0, 0, difficulty="easy", **overrides)
    analysis = generator._analysis(control)
    assert len(analysis["corner_parts"]) == 1
    corner, part = analysis["corner_parts"][0]
    assert corner == "tl" and (0, 0) in part["cells"] and len(part["cells"]) >= 2
    witness = [row[:] for row in control]
    removed = sorted(part["cells"] - {(0, 0)})
    for row, col in removed:
        witness[row][col] = analysis["background"]
    inputs = [control, witness]

    retained_inputs = json.loads((RETAINED / "input.json").read_text(encoding="utf-8"))["inputs"]
    assert inputs == retained_inputs
    validations = [generator.self_check(grid, difficulty="easy") for grid in inputs]
    observations = [generator.observe_overrides(grid) for grid in inputs]
    assert validations == [[], []]
    assert observations == [overrides, overrides]

    program, canonical_pairs, occurrences = canonical_record()
    assert normalized_rule_hash(program) == RULE_HASH == generator.RULE_HASH
    canonical_agreement = [
        ignore_singletons_rival([list(row) for row in input_key]) == expected
        for input_key, expected in canonical_pairs.items()
    ]
    assert all(canonical_agreement)

    bridge = RacketBridge(timeout=30, max_calls_before_restart=16)
    try:
        runtime = bridge.runtime_identity
        bridge.eval_text(f"(define __ticket_rule {wrap_rule(program)})")
        actual_outputs = []
        for index_value, grid in enumerate(inputs):
            name = f"__ticket_input_{index_value}"
            bridge.define_grid(name, grid)
            actual_outputs.append(bridge.eval_text(f"(__ticket_rule {name})"))
    finally:
        bridge.shutdown()

    retained_racket = json.loads((RETAINED / "racket.json").read_text(encoding="utf-8"))
    retained_racket_outputs = [row["output"] for row in retained_racket["results"]]
    retained_rivals = json.loads((RETAINED / "rival.json").read_text(encoding="utf-8"))["outputs"]
    mirrors = [generator.rule_mirror(grid) for grid in inputs]
    rivals = [ignore_singletons_rival(grid) for grid in inputs]
    assert actual_outputs == retained_racket_outputs == mirrors
    assert rivals == retained_rivals
    assert actual_outputs[0] == rivals[0]
    assert actual_outputs[1] != rivals[1]
    differences = [
        {"row": row, "col": col, "racket": value, "rival": rivals[1][row][col]}
        for row, values in enumerate(actual_outputs[1])
        for col, value in enumerate(values)
        if value != rivals[1][row][col]
    ]
    assert differences == [{"row": 0, "col": 7, "racket": 1, "rival": 4}]

    report = {
        "schema": "arcpuzzles-audit-replay-ticket-v1",
        "ticket_id": TICKET_ID,
        "status": "reproduced",
        "task_id": TASK,
        "audit_return_id": RETURN_ID,
        "audit_not_cleared": True,
        "claim": (
            "The retained audited source accepts a lawful singleton top-left corner mutation "
            "under the same profile; exact Racket copies it to (0,7), while the "
            "ignore-singletons rival does not."
        ),
        "source_binding": {
            "audited_generator_path": str(AUDITED_SOURCE.relative_to(REPO)),
            "audited_generator_sha256": AUDITED_SOURCE_SHA256,
            "current_generator_path": str(CURRENT_SOURCE.relative_to(REPO)),
            "current_generator_sha256": CURRENT_SOURCE_SHA256,
            "current_source_differs_from_audited_source": True,
            "assets_manifest_sha256": ASSET_MANIFEST_SHA256,
            "audit_index_sha256": AUDIT_INDEX_SHA256,
            "audit_record_sha256": AUDIT_RECORD_SHA256,
            "rule_hash": RULE_HASH,
        },
        "asset_files_verified": verified_assets,
        "witness": {
            "seed": 0,
            "sample_index": 0,
            "difficulty": "easy",
            "overrides": overrides,
            "removed_cells": [list(cell) for cell in removed],
            "regenerated_inputs_match_retained": True,
            "fresh_racket_outputs_match_retained": True,
            "fresh_rival_outputs_match_retained": True,
            "self_check": validations,
            "observed_overrides": observations,
            "canonical_unique_pairs": len(canonical_pairs),
            "canonical_pair_occurrences": occurrences,
            "rival_matches_all_canonical_pairs": all(canonical_agreement),
            "singleton_input_sha256": sha256_json(witness),
            "racket_output_sha256": sha256_json(actual_outputs[1]),
            "rival_output_sha256": sha256_json(rivals[1]),
            "differences": differences,
        },
        "racket_runtime": runtime,
        "limitations": [
            "One generated control and one one-cell mutation only; no random-seed census or peer battery.",
            "The current generator has a different retained hash, so this replay confirms only the pinned historical claim.",
            "Reproduction does not automatically clear, broaden, or re-resolve the audit.",
        ],
        "command": f"python3 review.py run python3 ../checks/tickets/{TICKET_ID}/replay.py",
        "probe_sha256": sha256_file(Path(__file__)),
    }
    with OUT.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": "reproduced", "differences": differences, "out": str(OUT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
