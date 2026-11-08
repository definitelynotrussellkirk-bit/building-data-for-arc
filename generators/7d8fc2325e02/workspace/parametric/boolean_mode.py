#!/usr/bin/env python3
"""Isolated episode-level OR/XOR prototype for ARC task 7d8fc2325e02.

The selected production generator and canonical rule remain unchanged.  This
prototype chooses one Boolean occupancy mode once per episode, materializes the
matching Racket rule, labels every pair by executing that rule, and exports a
public challenge with the hidden setting and query answer removed.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "7d8fc2325e02"
GENERATOR_SHA256 = "2a50dc1cd6412ff6ff7fc2e227c1e5bce5cf8e8de4fa8cef374abca8218a0ff6"
CANONICAL_RULE_HASH = "e9653f7b4ad7"
MODES = ("or", "xor")
CANONICAL_MODE = "or"
PROTOTYPE_SCHEMA = "arcpuzzles-separated-panel-boolean-mode-prototype-v1"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def choose_mode(seed: Any, mode: Any = None) -> str:
    """Choose the hidden rule once from a parameter-specific seed domain."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative literal integer")
    if mode is not None:
        if type(mode) is not str or mode not in MODES:
            raise ValueError(f"boolean_mode must be one of {MODES}")
        return mode
    digest = hashlib.sha256(f"{TASK_ID}:boolean-mode-v1:{seed}".encode()).digest()
    return MODES[digest[0] % len(MODES)]


def _canonical_record(root: Path) -> dict[str, Any]:
    rows = []
    for line in canonical_path(root).read_text().splitlines():
        record = json.loads(line)
        if record.get("task_id") == TASK_ID:
            rows.append(record)
    if len(rows) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}, found {len(rows)}")
    return rows[0]


def materialize_program(mode: str = CANONICAL_MODE, *, root: Path | str | None = None) -> str:
    """Return the exact canonical OR program or the nearby XOR variant."""
    chosen = choose_mode(0, mode)
    root_path = Path(root) if root is not None else find_root(__file__)
    canonical = _canonical_record(root_path)["program_solution"]
    if chosen == "or":
        return canonical
    return """(rule! (lambda (g)
         (let ((w (cols g)))
           (grid-from-fn 4
                         w
                         (lambda (r c)
                           (if (or (and (!= 0 (at g r c))
                                        (= 0 (at g (+ r 5) c)))
                                   (and (= 0 (at g r c))
                                        (!= 0 (at g (+ r 5) c))))
                               3
                               0))))))"""


def python_apply(grid: Any, mode: str) -> list[list[int]]:
    """Independent Python oracle for the two bounded prototype settings."""
    chosen = choose_mode(0, mode)
    source = normalize_grid(grid)
    if len(source) != 9 or not source or not source[0]:
        raise ValueError("input must be a nonempty 9-row separated-panel grid")
    width = len(source[0])
    if any(len(row) != width for row in source):
        raise ValueError("input must be rectangular")
    output: list[list[int]] = []
    for row in range(4):
        result_row = []
        for col in range(width):
            top = source[row][col] != 0
            bottom = source[row + 5][col] != 0
            occupied = (top or bottom) if chosen == "or" else (top != bottom)
            result_row.append(3 if occupied else 0)
        output.append(result_row)
    return output


def execute(bridge: RacketBridge, program: str, grid: Any) -> list[list[int]]:
    """Execute one exact `(rule! ...)` program using the public bridge API."""
    source = program.strip()
    if not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("expected one `(rule! ...)` program")
    rule_expression = source[len("(rule! ") : -1].strip()
    if not rule_expression.startswith("(lambda"):
        raise ValueError("boolean-mode prototype expects a lambda rule")
    bridge.define_grid("__boolean_mode_input__", normalize_grid(grid))
    result = bridge.eval_text(f"({rule_expression} __boolean_mode_input__)")
    return normalize_grid(result)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Allowlist the solver-visible fields; omit setting, program and query labels."""
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def generate_episode(
    seed: int,
    *,
    mode: str | None = None,
    bridge: RacketBridge,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Generate three demonstrations and one query under one fixed hidden mode."""
    chosen = choose_mode(seed, mode)
    root_path = Path(root) if root is not None else find_root(__file__)
    generator, _, source_hash = load_selected_generator(TASK_ID, root=root_path)
    if source_hash != GENERATOR_SHA256:
        raise ValueError(
            "selected generator changed; re-run the prototype review and update its source pin"
        )

    # A complete four-relation truth table is guaranteed by the selected sampler,
    # so OR and XOR differ on the overlap cells of every pair.
    grids = [generator.generate(seed, index, difficulty="medium") for index in range(4)]
    programs = {name: materialize_program(name, root=root_path) for name in MODES}
    outputs = {
        name: [execute(bridge, programs[name], grid) for grid in grids]
        for name in MODES
    }
    for name in MODES:
        expected = [python_apply(grid, name) for grid in grids]
        if outputs[name] != expected:
            raise AssertionError(f"Racket/Python disagreement for boolean_mode={name}")

    separating = [
        index
        for index in range(len(grids))
        if outputs["or"][index] != outputs["xor"][index]
    ]
    if separating != list(range(len(grids))):
        raise ValueError("every demonstration and query must distinguish OR from XOR")

    pairs = [
        {"input": deepcopy(grid), "output": deepcopy(outputs[chosen][index])}
        for index, grid in enumerate(grids)
    ]
    alternative = "xor" if chosen == "or" else "or"
    return {
        "schema": PROTOTYPE_SCHEMA,
        "task_id": TASK_ID,
        "seed": seed,
        "parameter": {"boolean_mode": chosen},
        "parameter_domain": {"boolean_mode": list(MODES)},
        "canonical_setting": {"boolean_mode": CANONICAL_MODE},
        "program": programs[chosen],
        "program_sha256": _sha256_text(programs[chosen]),
        "generator_sha256": source_hash,
        "train": pairs[:3],
        "test": pairs[3:],
        "alternative_setting": {"boolean_mode": alternative},
        "alternative_outputs": deepcopy(outputs[alternative]),
        "separating_pair_indices": separating,
        "all_pairs_separate_settings": True,
        "variant_approved": False,
        "production_parametric_api": False,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def _find_seed_per_mode(seed_start: int, limit: int = 64) -> dict[str, int]:
    if type(seed_start) is not int or seed_start < 0:
        raise ValueError("seed_start must be a nonnegative literal integer")
    found: dict[str, int] = {}
    for seed in range(seed_start, seed_start + limit):
        found.setdefault(choose_mode(seed), seed)
        if set(found) == set(MODES):
            return found
    raise RuntimeError(f"did not observe both modes in {limit} deterministic seeds")


def build_evidence(
    out: Path,
    *,
    seed_start: int = 31,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Materialize bounded, replayable private/public evidence for both settings."""
    root_path = Path(root) if root is not None else find_root(__file__)
    if out.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {out}")
    out.mkdir(parents=True)

    seed_by_mode = _find_seed_per_mode(seed_start)
    programs = {name: materialize_program(name, root=root_path) for name in MODES}
    anchors = canonical_pairs(TASK_ID, root=root_path)
    with RacketBridge(timeout=15, startup_timeout=60) as bridge:
        for pair in anchors:
            if execute(bridge, programs["or"], pair["input"]) != pair["output"]:
                raise AssertionError("canonical OR program failed a canonical pair")
        episodes = [
            generate_episode(seed_by_mode[name], bridge=bridge, root=root_path)
            for name in MODES
        ]

    for name, program in programs.items():
        rule_path = out / "private" / "rules" / f"{name}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(program)

    for index, episode in enumerate(episodes):
        _write_json(out / "private" / f"episode-{index:03d}.json", episode)
        _write_json(out / "public" / f"episode-{index:03d}.json", public_challenge(episode))

    witness_grid = deepcopy(episodes[0]["train"][0]["input"])
    witness_outputs = {name: python_apply(witness_grid, name) for name in MODES}
    differing_cells = [
        {
            "row": row,
            "column": col,
            "or": witness_outputs["or"][row][col],
            "xor": witness_outputs["xor"][row][col],
        }
        for row in range(len(witness_outputs["or"]))
        for col in range(len(witness_outputs["or"][0]))
        if witness_outputs["or"][row][col] != witness_outputs["xor"][row][col]
    ]
    _write_json(
        out / "private" / "differing-witness.json",
        {
            "task_id": TASK_ID,
            "input": witness_grid,
            "outputs": witness_outputs,
            "differing_cells": differing_cells,
        },
    )

    canonical_file = canonical_path(root_path)
    report = {
        "schema": "arcpuzzles-separated-panel-boolean-mode-verification-v1",
        "task_id": TASK_ID,
        "prototype_source_sha256": _sha256_bytes(Path(__file__).read_bytes()),
        "generator_sha256": GENERATOR_SHA256,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_ledger_sha256": _sha256_bytes(canonical_file.read_bytes()),
        "parameters": {
            "boolean_mode": {
                "allowed": list(MODES),
                "canonical_default": CANONICAL_MODE,
                "chosen_once_per_episode": True,
            }
        },
        "seed_search": {
            "start": seed_start,
            "limit": 64,
            "selected_private_seeds": seed_by_mode,
        },
        "canonical_pairs_executed": len(anchors),
        "episodes": len(episodes),
        "pairs_per_episode": {"demonstrations": 3, "queries": 1},
        "racket_evaluations": len(anchors) + len(episodes) * len(MODES) * 4,
        "all_pairs_separate_settings": all(
            episode["all_pairs_separate_settings"] for episode in episodes
        ),
        "all_racket_labels_match_independent_python": True,
        "differing_witness_cells": len(differing_cells),
        "runtime": racket_runtime_status(),
        "variant_approved": False,
        "production_parametric_api": False,
        "command": list(sys.argv),
        "limits": (
            "Two deterministic settings and two complete episodes; finite evidence only. "
            "The prototype tests OR versus XOR on the selected generator's bounded grammar; "
            "it does not prove universal identifiability or training improvement."
        ),
    }
    _write_json(out / "report.json", report)

    files = [
        {
            "path": str(path.relative_to(out)),
            "sha256": _sha256_bytes(path.read_bytes()),
            "bytes": path.stat().st_size,
        }
        for path in sorted(out.rglob("*"))
        if path.is_file()
    ]
    _write_json(
        out / "manifest.json",
        {
            "schema": "arcpuzzles-parametric-evidence-manifest-v1",
            "task_id": TASK_ID,
            "files": files,
        },
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=31)
    args = parser.parse_args()
    report = build_evidence(args.out, seed_start=args.seed_start)
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "episodes": report["episodes"],
                "canonical_pairs_executed": report["canonical_pairs_executed"],
                "all_pairs_separate_settings": report["all_pairs_separate_settings"],
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
