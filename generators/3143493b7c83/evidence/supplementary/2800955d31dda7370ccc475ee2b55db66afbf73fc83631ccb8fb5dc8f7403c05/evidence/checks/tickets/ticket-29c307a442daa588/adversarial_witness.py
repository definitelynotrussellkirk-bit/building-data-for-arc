#!/usr/bin/env python3
"""Bounded lawful witness for ticket-29c307a442daa588.

Shortcut under test: hard-code the canonical 23x23 / 6x6 lattice and inspect
only the first six lattice cells on each axis.  The shortcut fits every retained
canonical labeled pair because all canonical inputs are 23x23.  A lawful 27x27
current-generator instance with a true match in row/column band 7 refutes it.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import convert_dict_literals, strip_line_comments, strip_rule_wrapper
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator, normalize_grid

TICKET_ID = "ticket-29c307a442daa588"
TASK_ID = "3143493b7c83"
TICKET_SEED = "95d725136c37a41efd6258754ed1f8fb9649e1c126ab7eddc69ef151572d8031"
EXPECTED_SOURCE_SHA256 = "d25c612ee0344b89343998c1ad3fd436eeea48607e2963e1735801ddca80fa7f"
EXPECTED_RULE_HASH = "1e21086e1719"
ROOT = find_root(__file__)
WORK = ROOT.parent
HERE = Path(__file__).resolve().parent


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _grid_bytes(grid: list[list[int]]) -> bytes:
    return json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _grid_hash(grid: list[list[int]]) -> str:
    return _sha(_grid_bytes(grid))


def _racket_literal(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return "(" + " ".join(_racket_literal(item) for item in value) + ")"
    if type(value) is int:
        return str(value)
    raise TypeError(value)


def _head(body: str) -> str | None:
    text = body.lstrip()
    if not text.startswith("("):
        return None
    index = 1
    while index < len(text) and text[index].isspace():
        index += 1
    end = index
    while end < len(text) and text[end] not in " \t\r\n()[];":
        end += 1
    return text[index:end] or None


def _portable_wrap_rule(program: str) -> str:
    source = convert_dict_literals(strip_line_comments(program))
    body = strip_rule_wrapper(source)
    head = _head(body)
    if head in ("lambda", "λ"):
        return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) ({body} g)))"
    if head is None or head in {"pipe", "compose", "fork", "power"}:
        return body
    return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) {body}))"


def _canonical_program() -> str:
    programs = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID and row.get("program_solution"):
                    programs.append(row["program_solution"])
    unique = list(dict.fromkeys(programs))
    if len(unique) != 1:
        raise RuntimeError(f"expected one canonical program, got {len(unique)}")
    return unique[0]


def _apply_racket(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    callable_source = _portable_wrap_rule(program)
    literal = "'" + _racket_literal(normalize_grid(grid))
    return normalize_grid(bridge.eval_text(f"({callable_source} {literal})"))


def _apply_scan(module, grid: list[list[int]], *, canonical_six_only: bool) -> tuple[list[list[int]], list[tuple[int, int]]]:
    errors, info = module._parse_stamp(grid)
    if errors or info is None:
        raise ValueError("; ".join(errors))
    marker, _r0, _c0, _th, _tw, key = info
    height, width = len(grid), len(grid[0])
    row_stop = min(height, 24) if canonical_six_only else height
    col_stop = min(width, 24) if canonical_six_only else width
    output = deepcopy(grid)
    matches: list[tuple[int, int]] = []
    for row_start in range(0, row_stop, 4):
        for col_start in range(0, col_stop, 4):
            if all(
                row_start + tr < height
                and col_start + tc < width
                and grid[row_start + tr][col_start + tc] == 1
                for tr, tc in key
            ):
                matches.append((row_start, col_start))
                for tr, tc in key:
                    output[row_start + tr][col_start + tc] = marker
    return output, matches


def _seed() -> int:
    raw = hashlib.sha256(f"{TICKET_SEED}|{TASK_ID}|outer-band-witness".encode()).digest()
    return int.from_bytes(raw[:8], "big")


def main() -> None:
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source drift: {source_sha256}")

    canonical_results = []
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        rival, matches = _apply_scan(module, pair["input"], canonical_six_only=True)
        canonical_results.append({
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "shape": [len(pair["input"]), len(pair["input"][0])],
            "rival_matches": matches,
            "fits_label": rival == pair["output"],
            "input_sha256": _grid_hash(pair["input"]),
            "output_sha256": _grid_hash(pair["output"]),
        })
    if not canonical_results or not all(row["fits_label"] for row in canonical_results):
        raise RuntimeError("hard-coded six-by-six rival does not fit all retained canonical labels")

    generation_seed = _seed()
    overrides = {
        "cells_r": 7,
        "cells_c": 7,
        "key_h": 3,
        "key_w": 3,
        "n_matches": 4,
        "marker_color": 7,
        "decoy_mode": "few",
        "corner_box": False,
    }
    witness = None
    for sample_index in range(64):
        grid = normalize_grid(module.generate(generation_seed, sample_index, difficulty="hard", **overrides))
        validation = list(module.self_check(grid, difficulty="hard", meta=None))
        if validation:
            continue
        intended, all_matches = _apply_scan(module, grid, canonical_six_only=False)
        rival, rival_matches = _apply_scan(module, grid, canonical_six_only=True)
        outer_matches = [(r, c) for r, c in all_matches if r >= 24 or c >= 24]
        if outer_matches and intended != rival:
            witness = {
                "sample_index": sample_index,
                "input": grid,
                "validation_errors": validation,
                "intended_python": intended,
                "rival_output": rival,
                "all_matches": all_matches,
                "rival_matches": rival_matches,
                "outer_band_matches": outer_matches,
                "observed_overrides": module.observe_overrides(grid),
            }
            break
    if witness is None:
        raise RuntimeError("no outer-band witness found in 64 lawful 7x7 draws")

    program = _canonical_program()
    bridge = RacketBridge(timeout=20.0, startup_timeout=30.0)
    try:
        racket_output = _apply_racket(bridge, program, witness["input"])
        runtime_identity = bridge.runtime_identity
    finally:
        bridge.close()
    if racket_output != witness["intended_python"]:
        raise RuntimeError("independent Python interpretation disagrees with canonical Racket")
    if racket_output == witness["rival_output"]:
        raise RuntimeError("witness failed to distinguish the shortcut")

    differences = [
        [r, c, witness["rival_output"][r][c], racket_output[r][c]]
        for r in range(len(racket_output))
        for c in range(len(racket_output[0]))
        if witness["rival_output"][r][c] != racket_output[r][c]
    ]
    report = {
        "schema": "arcpuzzles-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "ticket_seed": TICKET_SEED,
        "source_path": str(source_path.relative_to(WORK)),
        "generator_sha256": source_sha256,
        "declared_rule_hash": EXPECTED_RULE_HASH,
        "canonical_program_sha256": _sha(program.encode("utf-8")),
        "shortcut": "Assume the canonical 23x23 / 6x6 lattice and scan only starts 0,4,8,12,16,20 on each axis.",
        "canonical_fit": {
            "passed": sum(row["fits_label"] for row in canonical_results),
            "checked": len(canonical_results),
            "pairs": canonical_results,
        },
        "generation": {
            "seed": generation_seed,
            "sample_index": witness["sample_index"],
            "difficulty": "hard",
            "overrides": overrides,
            "observed_overrides": witness["observed_overrides"],
        },
        "lawful_witness": {
            "self_check_errors": witness["validation_errors"],
            "shape": [len(witness["input"]), len(witness["input"][0])],
            "all_matches": witness["all_matches"],
            "shortcut_scanned_matches": witness["rival_matches"],
            "outer_band_matches": witness["outer_band_matches"],
            "input": witness["input"],
            "racket_output": racket_output,
            "shortcut_output": witness["rival_output"],
            "input_sha256": _grid_hash(witness["input"]),
            "racket_output_sha256": _grid_hash(racket_output),
            "shortcut_output_sha256": _grid_hash(witness["rival_output"]),
            "difference_count": len(differences),
            "first_differences": differences[:20],
        },
        "racket_runtime_identity": runtime_identity,
        "outcome": "current generator refutes the canonical-size shortcut on a lawful 7x7 lattice; no peer safety finding",
        "limits": "one deterministic witness plus four retained canonical labels; no full peer battery or census",
    }
    out = HERE / "witness.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "canonical_fit": report["canonical_fit"],
        "witness_shape": report["lawful_witness"]["shape"],
        "outer_band_matches": report["lawful_witness"]["outer_band_matches"],
        "difference_count": report["lawful_witness"]["difference_count"],
        "output": str(out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
