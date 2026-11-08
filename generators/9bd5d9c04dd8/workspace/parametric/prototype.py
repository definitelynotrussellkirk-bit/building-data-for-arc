#!/usr/bin/env python3
"""Proposed episode-level selection-mode prototype for ARC task 9bd5d9c04dd8.

The canonical task extracts the isolated 3x3 tile with the most color-1 cells.
This task-local prototype preserves the same object detection, score, crop, and
row-major tie behavior while choosing one hidden episode-level parameter:
``selection_mode`` is either ``most`` (the exact canonical rule) or ``fewest``.
It does not modify the selected production generator or canonical authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.base import stable_rng
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "9bd5d9c04dd8"
PROTOTYPE_VERSION = "selection-mode-v1"
SELECTION_MODES = ("most", "fewest")
CANONICAL_DEFAULT = "most"
N_TRAIN = 3
N_TEST = 1
DEFAULT_EVIDENCE_SEEDS = (0, 1, 2, 4)
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
DEMO_PROFILES = (
    (13, 19, 4),
    (17, 23, 5),
    (19, 25, 6),
    (23, 27, 7),
    (25, 29, 8),
    (27, 30, 6),
)
QUERY_PROFILES = (
    (19, 23, 5),
    (23, 27, 6),
    (27, 30, 7),
    (30, 30, 8),
)

PARAMETER_SPEC = {
    "selection_mode": {
        "allowed": list(SELECTION_MODES),
        "canonical_default": CANONICAL_DEFAULT,
        "chosen_once_per_episode": True,
        "meaning": {
            "most": "extract the isolated 3x3 tile with the greatest color-1 count",
            "fewest": "extract the isolated 3x3 tile with the smallest color-1 count",
        },
        "input_constraints": [
            "2-4 orthogonally isolated, fully nonzero 3x3 tiles",
            "tile color-1 counts are distinct, so both extrema are unambiguous",
            "the same selection_mode labels every demonstration and query in an episode",
        ],
    }
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _validate_mode(selection_mode: str) -> None:
    if type(selection_mode) is not str or selection_mode not in SELECTION_MODES:
        raise ValueError(f"selection_mode must be one of {SELECTION_MODES}")


def _canonical_row(root: Path) -> dict[str, Any]:
    rows = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    if not rows:
        raise ValueError(f"canonical row missing for {TASK_ID}")
    programs = {row.get("program_solution") for row in rows}
    if None in programs or len(programs) != 1:
        raise ValueError(f"canonical variants disagree for {TASK_ID}")
    originals = [row for row in rows if row.get("source") == "training" and row.get("parent_hash") is None]
    return originals[0] if len(originals) == 1 else rows[0]


def program_for(
    selection_mode: str = CANONICAL_DEFAULT,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize the exact Racket rule for one bounded parameter setting."""
    _validate_mode(selection_mode)
    resolved = Path(root).resolve() if root is not None else find_root(__file__)
    canonical = _canonical_row(resolved)["program_solution"]
    canonical_path = Path(__file__).resolve().with_name("canonical.rkt")
    fewest_path = Path(__file__).resolve().with_name("fewest.rkt")
    retained_canonical = canonical_path.read_text(encoding="utf-8")
    if retained_canonical != canonical:
        raise ValueError("retained canonical.rkt differs from the selected canonical program")

    initial = "(best-n -1)"
    comparison = "(if (> ones best-n)"
    if canonical.count(initial) != 1 or canonical.count(comparison) != 1:
        raise ValueError("canonical rule drift: extrema-selection fragments changed")
    alternative = canonical.replace(initial, "(best-n 10)", 1).replace(
        comparison, "(if (< ones best-n)", 1
    )
    if fewest_path.read_text(encoding="utf-8") != alternative:
        raise ValueError("retained fewest.rkt differs from the reviewed transformation")
    return retained_canonical if selection_mode == CANONICAL_DEFAULT else alternative


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose the hidden rule once from the episode seed."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    rng = stable_rng(seed, f"{TASK_ID}|selection_mode", PROTOTYPE_VERSION)
    return {"selection_mode": SELECTION_MODES[rng.randrange(len(SELECTION_MODES))]}


def _isolated_tiles(grid: list[list[int]]) -> list[tuple[int, int, list[list[int]]]]:
    """Independent mirror of the canonical orthogonal-isolation geometry."""
    h, w = len(grid), len(grid[0])
    found = []
    for r0 in range(h - 2):
        for c0 in range(w - 2):
            if not all(grid[r0 + dr][c0 + dc] != 0 for dr in range(3) for dc in range(3)):
                continue
            if r0 and any(grid[r0 - 1][c0 + dc] != 0 for dc in range(3)):
                continue
            if r0 + 3 < h and any(grid[r0 + 3][c0 + dc] != 0 for dc in range(3)):
                continue
            if c0 and any(grid[r0 + dr][c0 - 1] != 0 for dr in range(3)):
                continue
            if c0 + 3 < w and any(grid[r0 + dr][c0 + 3] != 0 for dr in range(3)):
                continue
            found.append((r0, c0, [row[c0:c0 + 3] for row in grid[r0:r0 + 3]]))
    return found


def apply_python(grid: list[list[int]], selection_mode: str) -> list[list[int]]:
    """Independent Python oracle for Racket parity checks."""
    _validate_mode(selection_mode)
    candidates = _isolated_tiles(grid)
    if not candidates:
        raise ValueError("no isolated 3x3 candidate")
    key = lambda item: sum(value == 1 for row in item[2] for value in row)
    selected = max(candidates, key=key) if selection_mode == "most" else min(candidates, key=key)
    return selected[2]



def _validate_settings(settings: dict[str, Any]) -> str:
    if type(settings) is not dict or set(settings) != {"selection_mode"}:
        raise ValueError("settings must name exactly selection_mode")
    selection_mode = settings["selection_mode"]
    _validate_mode(selection_mode)
    return selection_mode


def _validate_request(seed: int, demos: int, queries: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    if type(demos) is not int or not DEMO_LIMITS[0] <= demos <= DEMO_LIMITS[1]:
        raise ValueError(f"demos must be an integer in {DEMO_LIMITS[0]}..{DEMO_LIMITS[1]}")
    if type(queries) is not int or not QUERY_LIMITS[0] <= queries <= QUERY_LIMITS[1]:
        raise ValueError(f"queries must be an integer in {QUERY_LIMITS[0]}..{QUERY_LIMITS[1]}")


def program(settings: dict[str, Any]) -> str:
    """Return exact Racket source for one finite hidden setting."""
    return program_for(_validate_settings(settings))


def _axis_positions(length: int) -> list[int]:
    """Top-left positions for separated 3x3 slots, including boundaries."""
    limit = length - 3
    positions = list(range(0, limit + 1, 6))
    if positions[-1] != limit:
        if limit - positions[-1] >= 5:
            positions.append(limit)
        elif len(positions) == 1 or limit - positions[-2] >= 5:
            positions[-1] = limit
    return positions


def _candidate_anchors(height: int, width: int) -> list[tuple[int, int]]:
    return [(row, col) for row in _axis_positions(height) for col in _axis_positions(width)]


def _tile(rng, ones: int, candidate_index: int) -> list[list[int]]:
    positions = list(range(9))
    rng.shuffle(positions)
    one_positions = set(positions[:ones])
    palette = list(range(2, 10))
    rng.shuffle(palette)
    cells = []
    for index in range(9):
        if index in one_positions:
            cells.append(1)
        else:
            cells.append(palette[(index + candidate_index) % len(palette)])
    return [cells[0:3], cells[3:6], cells[6:9]]


def _scene(seed: int, split: str, index: int, profile: tuple[int, int, int]) -> list[list[int]]:
    height, width, candidate_count = profile
    rng = stable_rng(seed, f"{TASK_ID}|native|{split}|{index}", "2")
    anchors = _candidate_anchors(height, width)
    if candidate_count > min(8, len(anchors)):
        raise ValueError("profile requests too many distinct-count candidates")

    middle_pool = list(range(2, 8))
    rng.shuffle(middle_pool)
    chosen_counts = [1, 8, *middle_pool[: candidate_count - 2]]
    first_count = chosen_counts.pop(2)
    rng.shuffle(chosen_counts)
    counts = [first_count, *chosen_counts]
    assert len(counts) == candidate_count and counts[0] not in {min(counts), max(counts)}

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for candidate_index, ((top, left), ones) in enumerate(zip(anchors, counts, strict=False)):
        tile = _tile(rng, ones, candidate_index)
        for row_offset, values in enumerate(tile):
            grid[top + row_offset][left:left + 3] = values

    # Fill unused slots with objects that are too thin to become 3x3 candidates.
    for distractor_index, (top, left) in enumerate(anchors[candidate_count:]):
        if distractor_index >= max(2, candidate_count // 2):
            break
        color = 2 + rng.randrange(8)
        if distractor_index % 2:
            for offset in range(3):
                grid[top + 1][left + offset] = color
        else:
            for row_offset in range(2):
                for col_offset in range(2):
                    grid[top + row_offset][left + col_offset] = color

    report = analyze(grid)
    if len(report["candidates"]) != candidate_count:
        raise AssertionError("constructed scene created an accidental or missing candidate")
    if report["candidates"][0]["ones"] in {
        min(row["ones"] for row in report["candidates"]),
        max(row["ones"] for row in report["candidates"]),
    }:
        raise AssertionError("first candidate must be a deliberate wrong answer for both modes")
    return grid


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    candidates = []
    for row, col, tile in _isolated_tiles(grid):
        candidates.append({
            "top_left": [row, col],
            "ones": sum(value == 1 for values in tile for value in values),
            "tile": tile,
        })
    return {
        "shape": [len(grid), len(grid[0])],
        "nonzero_cells": sum(value != 0 for row in grid for value in row),
        "candidates": candidates,
    }


def first_candidate_output(grid: list[list[int]]) -> list[list[int]]:
    candidates = _isolated_tiles(grid)
    if not candidates:
        raise ValueError("no isolated 3x3 candidate")
    return [row[:] for row in candidates[0][2]]


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    """Generate deterministic setting-matched inputs and Python claim labels."""
    mode = _validate_settings(settings)
    _validate_request(seed, demos, queries)
    train_inputs = [
        _scene(seed, "demo", index, DEMO_PROFILES[index])
        for index in range(demos)
    ]
    test_inputs = [
        _scene(seed, "query", index, QUERY_PROFILES[index])
        for index in range(queries)
    ]
    signatures = [json.dumps(grid, separators=(",", ":")) for grid in train_inputs + test_inputs]
    if len(signatures) != len(set(signatures)):
        raise AssertionError("native episode inputs must be distinct")
    return {
        "train": [{"input": grid, "output": apply_python(grid, mode)} for grid in train_inputs],
        "test": [{"input": grid, "output": apply_python(grid, mode)} for grid in test_inputs],
        "program_solution": program({"selection_mode": mode}),
    }


def _racket_outputs(program: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    body = strip_rule_wrapper(program)
    bridge = RacketBridge()
    try:
        outputs = []
        for grid in grids:
            bridge.define_grid("g", grid)
            outputs.append(bridge.eval_text(f"({body} g)"))
        return outputs
    finally:
        bridge.shutdown()


def _public_episode(grids, selected_outputs) -> dict[str, Any]:
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "train": [
            {"input": grid, "output": output}
            for grid, output in zip(
                grids[:N_TRAIN], selected_outputs[:N_TRAIN], strict=True
            )
        ],
        # Hidden setting, Racket source, and query answer are intentionally omitted.
        "test": [{"input": grid} for grid in grids[N_TRAIN:]],
    }


def materialize_episode(
    seed: int,
    *,
    difficulty: str = "medium",
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Generate and Racket-label one complete parameter-consistent episode."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    resolved = Path(root).resolve() if root is not None else find_root(__file__)
    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=resolved)
    mode = choose_parameters(seed)["selection_mode"]
    rival_mode = "fewest" if mode == "most" else "most"
    start = stable_rng(seed, f"{TASK_ID}|episode_start", PROTOTYPE_VERSION).randrange(10_000)
    grids = [
        generator.generate(seed, start + index, difficulty=difficulty)
        for index in range(N_TRAIN + N_TEST)
    ]

    programs = {value: program_for(value, root=resolved) for value in SELECTION_MODES}
    outputs = {value: _racket_outputs(programs[value], grids) for value in SELECTION_MODES}
    for value in SELECTION_MODES:
        mirrors = [apply_python(grid, value) for grid in grids]
        if outputs[value] != mirrors:
            raise AssertionError(f"Racket output disagrees with {value!r} Python mirror")

    differences = [
        outputs["most"][index] != outputs["fewest"][index]
        for index in range(len(grids))
    ]
    demo_differences = [index for index, differs in enumerate(differences[:N_TRAIN]) if differs]
    query_differences = [index for index, differs in enumerate(differences[N_TRAIN:]) if differs]
    if demo_differences != list(range(N_TRAIN)) or query_differences != [0]:
        raise AssertionError("episode failed to distinguish both parameter settings")

    selected = outputs[mode]
    rival = outputs[rival_mode]
    prototype_path = Path(__file__).resolve()
    ledger_path = canonical_path(resolved)
    return {
        "schema": "arc-parametric-prototype-evidence-v1",
        "task_id": TASK_ID,
        "prototype_status": "proposed",
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "difficulty": difficulty,
        "sample_start": start,
        "parameter": {
            "selection_mode": mode,
            "allowed": list(SELECTION_MODES),
            "canonical_default": CANONICAL_DEFAULT,
        },
        "parameter_spec": PARAMETER_SPEC,
        "rival_setting": rival_mode,
        "demonstration_difference_indices": demo_differences,
        "query_difference_indices": query_differences,
        "racket_verified": True,
        "programs": {
            value: {"text": text, "sha256": _sha256_text(text)}
            for value, text in programs.items()
        },
        "sources": {
            "prototype_path": str(prototype_path),
            "prototype_sha256": _sha256_file(prototype_path),
            "generator_path": str(generator_path),
            "generator_sha256": generator_sha,
            "canonical_path": str(ledger_path),
            "canonical_sha256": _sha256_file(ledger_path),
        },
        "public": _public_episode(grids, selected),
        "private": {
            "train": [
                {
                    "input": grids[index],
                    "output": selected[index],
                    "rival_output": rival[index],
                    "settings_disagree": differences[index],
                }
                for index in range(N_TRAIN)
            ],
            "test": [
                {
                    "input": grids[index],
                    "output": selected[index],
                    "rival_output": rival[index],
                    "settings_disagree": differences[index],
                }
                for index in range(N_TRAIN, N_TRAIN + N_TEST)
            ],
        },
        "limitations": [
            "prototype only; production remains bound to the canonical most-color-1 rule",
            "bounded evidence for retained seeds and generated episodes, not all seeds or hypotheses",
            "generated lessons use distinct color-1 counts; lawful tie behavior remains outside this prototype's teaching support",
        ],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_EVIDENCE_SEEDS))
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="easy")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    root = find_root(__file__)
    out_dir = args.out_dir.resolve()
    records = []
    observed = set()
    programs_written = False
    for seed in args.seeds:
        evidence = materialize_episode(seed, difficulty=args.difficulty, root=root)
        mode = evidence["parameter"]["selection_mode"]
        observed.add(mode)

        public_path = out_dir / "public" / f"seed-{seed}.json"
        private_path = out_dir / "private" / f"seed-{seed}.json"
        _write_json(public_path, evidence["public"])
        private_document = dict(evidence)
        private_document.pop("public")
        _write_json(private_path, private_document)

        if not programs_written:
            for value, record in evidence["programs"].items():
                rule_path = out_dir / "private" / "rules" / f"selection-{value}.rkt"
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(record["text"] + "\n", encoding="utf-8")
            programs_written = True

        records.append(
            {
                "seed": seed,
                "selection_mode": mode,
                "sample_start": evidence["sample_start"],
                "demonstration_difference_indices": evidence["demonstration_difference_indices"],
                "query_difference_indices": evidence["query_difference_indices"],
                "public_path": str(public_path),
                "public_sha256": _sha256_file(public_path),
                "private_path": str(private_path),
                "private_sha256": _sha256_file(private_path),
            }
        )

    if observed != set(SELECTION_MODES):
        raise RuntimeError(f"retained seeds must cover both settings; observed {sorted(observed)}")
    summary = {
        "schema": "arc-parametric-prototype-summary-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "prototype_status": "proposed",
        "parameter_spec": PARAMETER_SPEC,
        "command": " ".join(shlex.quote(part) for part in [sys.executable, *sys.argv]),
        "episodes": records,
    }
    _write_json(out_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
