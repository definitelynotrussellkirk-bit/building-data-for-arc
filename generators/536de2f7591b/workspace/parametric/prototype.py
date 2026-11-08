#!/usr/bin/env python3
"""Proposed episode-level slide-direction variant for task 536de2f7591b.

The selected production generator and canonical authority remain unchanged except
for their separate call-validation repair.  This authoring prototype chooses one
hidden direction once per episode, creates inputs lawful under the selected
canonical generator, and labels every pair by executing the exact materialized
Racket program through the included bridge.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
import types
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.base import stable_rng
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "536de2f7591b"
PROTOTYPE_VERSION = "slide-direction-v1"
DIRECTIONS = ("left", "right")
CANONICAL_DEFAULT = "left"
N_TRAIN = 4
N_TEST = 1
DEFAULT_EVIDENCE_SEEDS = (0, 2)

PARAMETER_SPEC = {
    "direction": {
        "allowed": list(DIRECTIONS),
        "canonical_default": CANONICAL_DEFAULT,
        "chosen_once_per_episode": True,
        "meaning": {
            "left": "slide each green row block toward the nearest cyan wall on its left, or the left edge",
            "right": "slide each green row block toward the nearest cyan wall on its right, or the right edge",
        },
        "input_constraints": [
            "one contiguous color-3 block of length 1..3 on each active row",
            "each active row leaves at least one empty step toward both candidate destinations",
            "nonmarker cells never occupy either direction's final block footprint",
            "the demonstrations make left and right produce different outputs",
        ],
    }
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_row(root: Path) -> dict[str, Any]:
    rows = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    if len(rows) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}, found {len(rows)}")
    if not isinstance(rows[0].get("program_solution"), str):
        raise ValueError("canonical row has no Racket program_solution")
    return rows[0]


def _replace_once(source: str, old: str, new: str, *, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"canonical rule drift at {label}: expected one fragment, found {count}")
    return source.replace(old, new, 1)


def program_for(direction: str = CANONICAL_DEFAULT, *, root: Path | str | None = None) -> str:
    """Return the exact Racket program for one bounded direction setting."""
    if direction not in DIRECTIONS:
        raise ValueError(f"direction must be one of {DIRECTIONS}")
    resolved = Path(root).resolve() if root is not None else find_root(__file__)
    canonical = _canonical_row(resolved)["program_solution"]
    if direction == CANONICAL_DEFAULT:
        return canonical

    program = _replace_once(
        canonical,
        "(reverse (range 0 gc1))",
        "(range (+ gc2 1) w)",
        label="right-side wall scan",
    )
    program = _replace_once(
        program,
        "(+ (first stops) 1)",
        "(- (first stops) glen)",
        label="right-side wall destination",
    )
    program = _replace_once(
        program,
        "(dest (if stop stop 0))",
        "(dest (if stop stop (- w glen)))",
        label="right-edge fallback",
    )
    program = _replace_once(
        program,
        "                                         (range 0 glen)",
        "                                         (reverse (range 0 glen))",
        label="overlap-safe rightward write order",
    )
    return program


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose one hidden direction deterministically for the whole episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    rng = stable_rng(seed, f"{TASK_ID}|direction", PROTOTYPE_VERSION)
    return {"direction": DIRECTIONS[rng.randrange(len(DIRECTIONS))]}


def _band_shape(rng, difficulty: str) -> tuple[int, int]:
    choices = {
        "easy": ((7, 8), (7, 9), (9, 8), (9, 9)),
        "medium": ((8, 10), (9, 12), (11, 12), (12, 14)),
        "hard": ((13, 14), (14, 17), (16, 18), (18, 20)),
    }
    return choices[difficulty][rng.randrange(len(choices[difficulty]))]


def _build_input(seed: int, pair_index: int, difficulty: str) -> list[list[int]]:
    """Create a row-local motion input that is lawful for both directions."""
    rng = stable_rng(seed, f"{TASK_ID}|parametric-input|{pair_index}", PROTOTYPE_VERSION)
    h, w = _band_shape(rng, difficulty)
    grid = [[0 for _ in range(w)] for _ in range(h)]
    active_count = min(h - 1, 2 + rng.randrange(3))
    active_rows = rng.sample(range(h), active_count)

    for ordinal, r in enumerate(active_rows):
        length = 1 + rng.randrange(min(3, w - 5))
        start = rng.randrange(2, w - length - 2)

        # Cycle edge fallbacks and two-wall cases while retaining room to move.
        mode = (pair_index + ordinal) % 3
        left_wall = None if mode == 1 else rng.randrange(0, start - 1)
        right_wall = None if mode == 2 else rng.randrange(start + length + 1, w)

        if left_wall is not None:
            grid[r][left_wall] = 8
        if right_wall is not None:
            grid[r][right_wall] = 8
        for c in range(start, start + length):
            grid[r][c] = 3

    # Texture is confined to inactive rows, so neither directional path or
    # destination can overwrite an unrelated object.
    inactive = [r for r in range(h) if r not in active_rows]
    texture_slots = [(r, c) for r in inactive for c in range(w)]
    texture_count = min(len(texture_slots), max(1, round(0.16 * h * w)))
    for r, c in rng.sample(texture_slots, texture_count):
        grid[r][c] = 8
    return grid


def _blocks(grid: list[list[int]]):
    for r, row in enumerate(grid):
        cols = [c for c, value in enumerate(row) if value == 3]
        if cols:
            yield r, cols[0], cols[-1]


def _apply_python(grid: list[list[int]], direction: str) -> list[list[int]]:
    if direction not in DIRECTIONS:
        raise ValueError(direction)
    out = [list(row) for row in grid]
    width = len(grid[0])
    for r, first, last in _blocks(grid):
        length = last - first + 1
        if direction == "left":
            walls = [c for c in range(first) if grid[r][c] == 8]
            dest = max(walls, default=-1) + 1
        else:
            walls = [c for c in range(last + 1, width) if grid[r][c] == 8]
            dest = (min(walls) - length) if walls else width - length
        for c in range(first, last + 1):
            out[r][c] = 0
        for c in range(dest, dest + length):
            out[r][c] = 3
    return out


def _racket_outputs(program: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    root = find_root(__file__)
    names = ("scripts", "scripts.comment_solutions")
    previous = {name: sys.modules.get(name) for name in names}
    package = types.ModuleType("scripts")
    package.__path__ = [str(root / "shared/tools")]
    sys.modules["scripts"] = package
    sys.modules.pop("scripts.comment_solutions", None)
    try:
        callable_text = wrap_rule(program)
    finally:
        for name in names:
            if previous[name] is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous[name]
    bridge = RacketBridge()
    try:
        fn_name = "__parametric_rule"
        bridge.eval_text(f"(define {fn_name} {callable_text})")
        outputs = []
        for grid in grids:
            bridge.define_grid("g", grid)
            outputs.append(bridge.eval_text(f"({fn_name} g)"))
        return outputs
    finally:
        bridge.shutdown()


def _public_episode(grids, selected_outputs):
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "train": [
            {"input": grid, "output": output}
            for grid, output in zip(
                grids[:N_TRAIN], selected_outputs[:N_TRAIN], strict=True
            )
        ],
        # Hidden parameter, Racket source and query answer are omitted.
        "test": [{"input": grid} for grid in grids[N_TRAIN:]],
    }


def materialize_episode(
    seed: int,
    *,
    difficulty: str = "medium",
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Generate and Racket-label one complete parameter-consistent episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    resolved = Path(root).resolve() if root is not None else find_root(__file__)
    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=resolved)
    direction = choose_parameters(seed)["direction"]
    rival_direction = "right" if direction == "left" else "left"
    grids = [_build_input(seed, index, difficulty) for index in range(N_TRAIN + N_TEST)]
    validation = [generator.self_check(grid) for grid in grids]
    if any(validation):
        raise AssertionError(f"prototype input left selected-generator domain: {validation}")

    programs = {value: program_for(value, root=resolved) for value in DIRECTIONS}
    outputs = {value: _racket_outputs(programs[value], grids) for value in DIRECTIONS}
    for value in DIRECTIONS:
        mirrors = [_apply_python(grid, value) for grid in grids]
        if outputs[value] != mirrors:
            raise AssertionError(f"Racket output disagrees with {value} Python mirror")

    differences = [outputs["left"][i] != outputs["right"][i] for i in range(len(grids))]
    demo_differences = [i for i, differs in enumerate(differences[:N_TRAIN]) if differs]
    query_differences = [i for i, differs in enumerate(differences[N_TRAIN:]) if differs]
    if demo_differences != list(range(N_TRAIN)) or query_differences != list(range(N_TEST)):
        raise AssertionError("episode failed to distinguish both direction settings")

    selected = outputs[direction]
    rival = outputs[rival_direction]
    public = _public_episode(grids, selected)
    private = {
        "train": [
            {
                "input": grids[i],
                "output": selected[i],
                "rival_output": rival[i],
                "settings_disagree": differences[i],
            }
            for i in range(N_TRAIN)
        ],
        "test": [
            {
                "input": grids[i],
                "output": selected[i],
                "rival_output": rival[i],
                "settings_disagree": differences[i],
            }
            for i in range(N_TRAIN, N_TRAIN + N_TEST)
        ],
    }
    prototype_path = Path(__file__).resolve()
    ledger_path = canonical_path(resolved)
    return {
        "schema": "arc-parametric-prototype-evidence-v1",
        "task_id": TASK_ID,
        "prototype_status": "proposed",
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "difficulty": difficulty,
        "parameter": {
            "direction": direction,
            "allowed": list(DIRECTIONS),
            "canonical_default": CANONICAL_DEFAULT,
        },
        "parameter_spec": PARAMETER_SPEC,
        "rival_setting": rival_direction,
        "demonstration_difference_indices": demo_differences,
        "query_difference_indices": query_differences,
        "racket_verified": True,
        "selected_generator_self_check_passed": True,
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
        "public": public,
        "private": private,
        "limitations": [
            "prototype only; production remains bound to the canonical leftward Racket rule",
            "bounded evidence for retained seeds and generated episodes, not all seeds or hypotheses",
            "only row-local contiguous green blocks with collision-free destinations were assessed",
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
    for seed in args.seeds:
        evidence = materialize_episode(seed, difficulty=args.difficulty, root=root)
        direction = evidence["parameter"]["direction"]
        observed.add(direction)
        public_path = out_dir / f"seed-{seed}-public.json"
        private_path = out_dir / f"seed-{seed}-private.json"
        _write_json(public_path, evidence["public"])
        private_document = dict(evidence)
        private_document.pop("public")
        _write_json(private_path, private_document)
        rules_dir = out_dir / "rules"
        for value, record in evidence["programs"].items():
            rule_path = rules_dir / f"direction-{value}.rkt"
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            rule_path.write_text(record["text"] + "\n", encoding="utf-8")
        records.append({
            "seed": seed,
            "direction": direction,
            "demonstration_difference_indices": evidence["demonstration_difference_indices"],
            "query_difference_indices": evidence["query_difference_indices"],
            "public_path": str(public_path),
            "public_sha256": _sha256_file(public_path),
            "private_path": str(private_path),
            "private_sha256": _sha256_file(private_path),
        })
    if observed != set(DIRECTIONS):
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
