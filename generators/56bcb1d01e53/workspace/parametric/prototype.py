#!/usr/bin/env python3
"""Proposed episode-level square-closure parameter for 56bcb1d01e53.

Production remains bound to the canonical quarter-turn rotational closure.  This
separate prototype chooses either rotational or full dihedral square closure once
per episode, emits the exact Racket program for that setting, and derives every
label by executing Racket.  It is proposed authoring evidence, not production
approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "56bcb1d01e53"
ROOT = find_root(__file__)
MODES = ("rotation", "dihedral")
DEFAULT_MODE = "rotation"
STATUS = "proposed prototype; canonical production remains rotation-only"

# The exact square-partner list in the selected canonical Racket program.
_ROTATION_PARTNERS = (
    "(list "
    "(list (inexact->exact (round (+ cr (- c cc)))) (inexact->exact (round (- cc (- r cr))))) "
    "(list (inexact->exact (round (- cr (- r cr)))) (inexact->exact (round (- cc (- c cc))))) "
    "(list (inexact->exact (round (- cr (- c cc)))) (inexact->exact (round (+ cc (- r cr))))))"
)
_DIHEDRAL_PARTNERS = (
    "(list "
    "(list (inexact->exact (round (+ cr (- c cc)))) (inexact->exact (round (- cc (- r cr))))) "
    "(list (inexact->exact (round (- cr (- r cr)))) (inexact->exact (round (- cc (- c cc))))) "
    "(list (inexact->exact (round (- cr (- c cc)))) (inexact->exact (round (+ cc (- r cr))))) "
    "(list (inexact->exact (round (- cr (- r cr)))) (inexact->exact (round (+ cc (- c cc))))) "
    "(list (inexact->exact (round (+ cr (- r cr)))) (inexact->exact (round (- cc (- c cc))))) "
    "(list (inexact->exact (round (+ cr (- c cc)))) (inexact->exact (round (+ cc (- r cr))))) "
    "(list (inexact->exact (round (- cr (- c cc)))) (inexact->exact (round (- cc (- r cr))))))"
)

# This lawful 7x7 icon has two raw 8-components joined by a one-cell cardinal
# bridge.  Quarter-turn closure fills its center through diagonal support and
# leaves four reflected cells blank; full D4 closure paints those four cells.
_BASE_CELLS = frozenset(
    {
        (0, 3),
        (1, 2),
        (2, 2),
        (2, 4),
        (2, 5),
        (3, 0),
        (3, 1),
        (3, 6),
        (4, 2),
        (5, 3),
        (6, 3),
    }
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_record(*, root: Path | str = ROOT) -> dict:
    root = Path(root)
    with canonical_path(root).open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise ValueError(f"canonical task not found: {TASK_ID}")


def _validate_mode(mode: str) -> None:
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"square_closure must be one of {MODES}")


def program_for(mode: str = DEFAULT_MODE, *, root: Path | str = ROOT) -> str:
    """Return the exact canonical rule or its one-branch D4 variant."""
    _validate_mode(mode)
    canonical = canonical_record(root=root)["program_solution"]
    if canonical.count(_ROTATION_PARTNERS) != 1:
        raise ValueError("canonical square-partner anchor changed; prototype needs review")
    if mode == DEFAULT_MODE:
        return canonical
    return canonical.replace(_ROTATION_PARTNERS, _DIHEDRAL_PARTNERS, 1)


def _callable_text(program: str) -> str:
    # Canonical records already wrap their body as ``(lambda (g) ...)``.
    # Returning that callable directly avoids an accidental lambda-of-lambda.
    return strip_rule_wrapper(program)


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def application(program: str, grid: list[list[int]]) -> str:
    return f"({_callable_text(program)} {_grid_literal(grid)})"


def execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(application(program, grid))


def _transform(cells: Iterable[tuple[int, int]], code: int) -> frozenset[tuple[int, int]]:
    transformed = set()
    for row, col in cells:
        if code >= 4:
            col = 6 - col
        for _ in range(code % 4):
            row, col = col, 6 - row
        transformed.add((row, col))
    return frozenset(transformed)


def _colors(seed: int, pair_index: int) -> tuple[int, int]:
    palette = (1, 8, 4, 2, 6, 3, 9, 5, 7)
    background = palette[(seed + 2 * pair_index) % len(palette)]
    foreground = palette[(seed + 2 * pair_index + 3) % len(palette)]
    if foreground == background:  # Defensive; current offset already prevents this.
        foreground = palette[(palette.index(background) + 1) % len(palette)]
    return background, foreground


def witness_input(seed: int, pair_index: int) -> list[list[int]]:
    """Create one deterministic lawful chiral-square input."""
    if type(seed) is not int:
        raise ValueError("seed must be a Python int")
    if type(pair_index) is not int or not 0 <= pair_index <= 2:
        raise ValueError("pair_index must be an integer in 0..2")
    h, w = ((11, 12), (12, 13), (13, 11))[pair_index]
    code = (seed * 5 + pair_index * 3) % 8
    cells = _transform(_BASE_CELLS, code)
    max_top, max_left = h - 7, w - 7
    top = (seed * 7 + pair_index * 2) % (max_top + 1)
    left = (seed * 11 + pair_index * 3) % (max_left + 1)
    background, foreground = _colors(seed, pair_index)
    grid = [[background for _ in range(w)] for _ in range(h)]
    for row, col in cells:
        grid[top + row][left + col] = foreground
    return grid


def shared_witness(seed: int = 0) -> list[list[int]]:
    return witness_input(seed, 0)


def generate_episode(
    seed: int,
    bridge: RacketBridge,
    *,
    square_closure: str | None = None,
    root: Path | str = ROOT,
) -> tuple[dict, dict]:
    """Create a model-visible episode plus evaluator-only parameter evidence."""
    if type(seed) is not int:
        raise ValueError("seed must be a Python int")
    selected = MODES[seed % len(MODES)] if square_closure is None else square_closure
    _validate_mode(selected)
    programs = {mode: program_for(mode, root=root) for mode in MODES}
    grids = [witness_input(seed, pair_index) for pair_index in range(3)]
    selected_outputs = [execute(bridge, programs[selected], grid) for grid in grids]

    public = {
        "train": [
            {"input": grid, "output": output}
            for grid, output in zip(grids[:2], selected_outputs[:2])
        ],
        "test": [{"input": grids[2]}],
    }

    rival_checks = {}
    executions = []
    for mode in MODES:
        predictions = []
        for pair_index, grid in enumerate(grids):
            prediction = execute(bridge, programs[mode], grid)
            predictions.append(prediction)
            executions.append(
                {
                    "square_closure": mode,
                    "pair_index": pair_index,
                    "application_sha256": digest(application(programs[mode], grid).encode()),
                    "output": prediction,
                }
            )
        differing = [
            index for index in range(2) if predictions[index] != selected_outputs[index]
        ]
        rival_checks[mode] = {
            "matches_all_demonstrations": not differing,
            "distinguishing_demo_indices": differing,
            "demonstration_predictions": predictions[:2],
            "query_predictions": predictions[2:],
        }

    survivors = [
        mode for mode, check in rival_checks.items() if check["matches_all_demonstrations"]
    ]
    if survivors != [selected]:
        raise ValueError(f"demonstrations do not identify square_closure: {survivors}")

    private = {
        "schema": "56bcb1d01e53-parametric-square-closure-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameter_seed": seed,
        "parameter": {"square_closure": selected},
        "program_sha256": digest(programs[selected].encode()),
        "query_answers": selected_outputs[2:],
        "rival_checks": rival_checks,
        "executions": executions,
    }
    return public, private


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_evidence(
    out: Path | str,
    *,
    seeds: list[int] | tuple[int, ...] = (0, 1),
    root: Path | str = ROOT,
) -> dict:
    """Materialize public/private episodes, exact rules, and source bindings."""
    out = Path(out)
    root = Path(root)
    for folder in ("public", "private", "rules"):
        (out / folder).mkdir(parents=True, exist_ok=True)

    programs = {mode: program_for(mode, root=root) for mode in MODES}
    for mode, program in programs.items():
        (out / "rules" / f"square-closure-{mode}.rkt").write_text(program, encoding="utf-8")

    episode_rows = []
    with RacketBridge(max_calls_before_restart=128) as bridge:
        runtime_identity = bridge.runtime_identity
        for index, seed in enumerate(seeds):
            public, private = generate_episode(seed, bridge, root=root)
            name = f"episode-{index:03d}.json"
            _write_json(out / "public" / name, public)
            _write_json(out / "private" / name, private)
            episode_rows.append(
                {"file": name, "seed": seed, "parameter": private["parameter"]}
            )

        canonical_checks = []
        for pair_index, pair in enumerate(canonical_pairs(TASK_ID, root=root, labeled_only=True)):
            actual = execute(bridge, programs[DEFAULT_MODE], pair["input"])
            if actual != pair["output"]:
                raise ValueError(f"default program failed canonical pair {pair_index}")
            canonical_checks.append(
                {"pair_index": pair_index, "expected": pair["output"], "actual": actual}
            )
        _write_json(out / "private" / "canonical-checks.json", canonical_checks)

        witness = shared_witness(0)
        witness_outputs = {
            mode: execute(bridge, program, witness) for mode, program in programs.items()
        }
        if witness_outputs["rotation"] == witness_outputs["dihedral"]:
            raise ValueError("shared witness failed to distinguish square-closure modes")
        _write_json(
            out / "private" / "shared-witness.json",
            {"input": witness, "outputs": witness_outputs},
        )

    _, generator_source, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    prototype_source = Path(__file__).resolve()
    canonical = canonical_record(root=root)["program_solution"]
    manifest = {
        "schema": "56bcb1d01e53-parametric-square-closure-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameter": {
            "name": "square_closure",
            "allowed": list(MODES),
            "default": DEFAULT_MODE,
        },
        "input_constraints": (
            "one nonzero-background incomplete chiral 7x7 square icon; "
            "the same mode applies to every pair in an episode"
        ),
        "canonical_default_unchanged": programs[DEFAULT_MODE] == canonical,
        "program_sha256": {mode: digest(program.encode()) for mode, program in programs.items()},
        "episodes": episode_rows,
        "generator_source": str(Path(generator_source).relative_to(root)),
        "generator_sha256": generator_sha256,
        "prototype_source_sha256": digest(prototype_source.read_bytes()),
        "racket_runtime": runtime_identity,
        "limitations": [
            "prototype only; production remains pinned to canonical rotational closure",
            "bounded evidence covers the materialized seeds and two declared modes",
            "the prototype isolates the square branch rather than sampling the full canonical curriculum",
        ],
    }
    _write_json(out / "manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    args = parser.parse_args(argv)
    manifest = write_evidence(args.out, seeds=args.seeds)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
