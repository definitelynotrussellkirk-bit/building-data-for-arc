#!/usr/bin/env python3
"""Task-local straight-block-position prototype for ARC task f6b9f647b109.

The selected production generator and canonical Racket rule remain unchanged.
This prototype varies one hidden rule parameter once per episode while preserving
red/blue endpoint roles, the shortest Chebyshev path, and a contiguous block of
all dominant-axis steps:

* ``after_first_diagonal`` (canonical/default): one diagonal, all straights,
  then the remaining diagonals.
* ``before_diagonals`` (proposed): all straights first, then all diagonals.

Every retained label is produced by the included Racket bridge.  Python mirrors
are used only to select an identifying episode and verify bridge parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.base import stable_rng
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "f6b9f647b109"
PROTOTYPE_VERSION = "straight-block-position-v1"
PARAMETER_NAME = "straight_block_position"
POSITION_VALUES = ("after_first_diagonal", "before_diagonals")
CANONICAL_DEFAULT = "after_first_diagonal"
N_TRAIN = 4
N_TEST = 1
MAX_START_PROBES = 32

CANONICAL_PHASE_FRAGMENT = """                       (cond
                         ;; Phase 1: the mandatory first diagonal.
                         ((= step 1) (list (+ cur-r drow) (+ cur-c dcol)))
                         ;; Phase 2: contiguous dominant-axis steps.
                         ((<= step (+ 1 straights))
                          (if is-vert
                              (list (+ cur-r drow) cur-c)
                              (list cur-r (+ cur-c dcol))))
                         ;; Phase 3: trailing diagonals.
                         (else (list (+ cur-r drow) (+ cur-c dcol))))"""

STRAIGHT_FIRST_PHASE_FRAGMENT = """                       (cond
                         ;; Proposed variant: take the dominant-axis block first.
                         ((<= step straights)
                          (if is-vert
                              (list (+ cur-r drow) cur-c)
                              (list cur-r (+ cur-c dcol))))
                         ;; Then take all diagonal steps toward blue.
                         (else (list (+ cur-r drow) (+ cur-c dcol))))"""

PARAMETER_SPEC = {
    PARAMETER_NAME: {
        "allowed": list(POSITION_VALUES),
        "canonical_default": CANONICAL_DEFAULT,
        "chosen_once_per_episode": True,
        "input_constraints": [
            "one red endpoint and one blue endpoint on a zero background",
            "unequal nonzero row/column gaps so the straight block is visible",
            "four demonstrations include at least one output disagreement between settings",
            "the held-out query also differs between settings",
        ],
    }
}


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_row(root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    program_rows = [
        row
        for row in rows
        if isinstance(row.get("program_solution"), str)
        and row["program_solution"].strip()
    ]
    if not program_rows:
        raise ValueError(f"canonical ledger has no program_solution for {TASK_ID}")

    programs = {row["program_solution"] for row in program_rows}
    if len(programs) != 1:
        raise ValueError(
            f"canonical ledger has {len(programs)} conflicting programs for {TASK_ID}"
        )
    return program_rows[0]


def program_for(
    position: str = CANONICAL_DEFAULT,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize the exact Racket program for one bounded parameter value."""
    if position not in POSITION_VALUES:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {POSITION_VALUES}, got {position!r}"
        )
    resolved_root = Path(root).resolve() if root is not None else find_root(__file__)
    canonical = _canonical_row(resolved_root)["program_solution"]
    count = canonical.count(CANONICAL_PHASE_FRAGMENT)
    if count != 1:
        raise ValueError(
            "canonical rule drift: expected one canonical phase fragment, "
            f"found {count}"
        )
    if STRAIGHT_FIRST_PHASE_FRAGMENT in canonical:
        raise ValueError("canonical rule unexpectedly already contains the proposed fragment")
    if position == CANONICAL_DEFAULT:
        return canonical
    return canonical.replace(
        CANONICAL_PHASE_FRAGMENT,
        STRAIGHT_FIRST_PHASE_FRAGMENT,
        1,
    )


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose the hidden rule setting once from the episode seed."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    rng = stable_rng(seed, f"{TASK_ID}|{PARAMETER_NAME}", PROTOTYPE_VERSION)
    return {PARAMETER_NAME: POSITION_VALUES[rng.randrange(len(POSITION_VALUES))]}


def _candidate_starts(seed: int) -> Iterable[int]:
    rng = stable_rng(seed, f"{TASK_ID}|parametric_start", PROTOTYPE_VERSION)
    first = rng.randrange(16)
    for offset in range(MAX_START_PROBES):
        yield first + offset


def _racket_outputs(program: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    body = strip_rule_wrapper(program)
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    bridge = RacketBridge()
    try:
        outputs: list[list[list[int]]] = []
        for grid in grids:
            bridge.define_grid("g", grid)
            output = bridge.eval_text(expression)
            if (
                not isinstance(output, list)
                or not output
                or not isinstance(output[0], list)
                or not output[0]
                or any(
                    not isinstance(row, list) or len(row) != len(output[0])
                    for row in output
                )
                or any(
                    type(value) is not int or not 0 <= value <= 9
                    for row in output
                    for value in row
                )
            ):
                raise ValueError("Racket program did not return a rectangular ARC grid")
            outputs.append(output)
        return outputs
    finally:
        bridge.shutdown()


def _public_episode(
    grids: list[list[list[int]]],
    selected_outputs: list[list[list[int]]],
) -> dict[str, Any]:
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "train": [
            {"input": grid, "output": output}
            for grid, output in zip(
                grids[:N_TRAIN],
                selected_outputs[:N_TRAIN],
                strict=True,
            )
        ],
        # The hidden parameter, programs, and held-out answer stay private.
        "test": [{"input": grid} for grid in grids[N_TRAIN:]],
    }


def materialize_episode(
    seed: int,
    *,
    difficulty: str = "medium",
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Build one complete episode and execute both settings in Racket."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")

    resolved_root = Path(root).resolve() if root is not None else find_root(__file__)
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID,
        root=resolved_root,
    )
    selected_position = choose_parameters(seed)[PARAMETER_NAME]

    selected_start: int | None = None
    grids: list[list[list[int]]] | None = None
    canonical_mirror: list[list[list[int]]] | None = None
    straight_first_mirror: list[list[list[int]]] | None = None
    for start in _candidate_starts(seed):
        candidate = [
            generator.generate(seed, start + index, difficulty=difficulty)
            for index in range(N_TRAIN + N_TEST)
        ]
        candidate_canonical = [generator.rule_mirror(grid) for grid in candidate]
        rival = generator.SEMANTIC_RIVALS["straight_then_all_diagonals"]
        candidate_straight_first = [rival(grid) for grid in candidate]
        differences = [
            left != right
            for left, right in zip(
                candidate_canonical,
                candidate_straight_first,
                strict=True,
            )
        ]
        if any(differences[:N_TRAIN]) and all(differences[N_TRAIN:]):
            selected_start = start
            grids = candidate
            canonical_mirror = candidate_canonical
            straight_first_mirror = candidate_straight_first
            break

    if (
        selected_start is None
        or grids is None
        or canonical_mirror is None
        or straight_first_mirror is None
    ):
        raise RuntimeError(
            f"no identifying {N_TRAIN}+{N_TEST} episode found in "
            f"{MAX_START_PROBES} starts for seed {seed}"
        )

    programs = {name: program_for(name, root=resolved_root) for name in POSITION_VALUES}
    outputs = {name: _racket_outputs(programs[name], grids) for name in POSITION_VALUES}
    mirrors = {
        "after_first_diagonal": canonical_mirror,
        "before_diagonals": straight_first_mirror,
    }
    for name in POSITION_VALUES:
        if outputs[name] != mirrors[name]:
            raise AssertionError(f"{name} Racket output disagrees with its Python mirror")

    differences = [
        outputs[POSITION_VALUES[0]][index] != outputs[POSITION_VALUES[1]][index]
        for index in range(len(grids))
    ]
    demonstration_difference_indices = [
        index for index, differs in enumerate(differences[:N_TRAIN]) if differs
    ]
    query_difference_indices = [
        index for index, differs in enumerate(differences[N_TRAIN:]) if differs
    ]
    if not demonstration_difference_indices:
        raise AssertionError("demonstrations do not identify the hidden setting")
    if query_difference_indices != list(range(N_TEST)):
        raise AssertionError("the held-out query does not distinguish every setting")

    selected_outputs = outputs[selected_position]
    private_train = []
    for index in range(N_TRAIN):
        private_train.append(
            {
                "input": grids[index],
                "output": selected_outputs[index],
                "outputs_by_setting": {
                    name: outputs[name][index] for name in POSITION_VALUES
                },
            }
        )
    private_test = []
    for local_index in range(N_TEST):
        index = N_TRAIN + local_index
        private_test.append(
            {
                "input": grids[index],
                "output": selected_outputs[index],
                "outputs_by_setting": {
                    name: outputs[name][index] for name in POSITION_VALUES
                },
            }
        )

    first_witness = demonstration_difference_indices[0]
    public = _public_episode(grids, selected_outputs)
    return {
        "schema": "f6b9f647b109-parametric-evidence-v1",
        "task_id": TASK_ID,
        "prototype_status": "proposed",
        "prototype_version": PROTOTYPE_VERSION,
        "parameter_spec": PARAMETER_SPEC,
        "parameter": {
            PARAMETER_NAME: selected_position,
            "allowed": list(POSITION_VALUES),
            "canonical_default": CANONICAL_DEFAULT,
        },
        "seed": seed,
        "difficulty": difficulty,
        "sample_start": selected_start,
        "generator": {
            "path": str(generator_path),
            "sha256": generator_sha256,
        },
        "programs": {
            name: {"text": program, "sha256": _sha256_text(program)}
            for name, program in programs.items()
        },
        "racket_verified": True,
        "demonstration_difference_indices": demonstration_difference_indices,
        "query_difference_indices": query_difference_indices,
        "same_input_witness": {
            "pair_kind": "demonstration",
            "index": first_witness,
            "input": grids[first_witness],
            "outputs_by_setting": {
                name: outputs[name][first_witness] for name in POSITION_VALUES
            },
        },
        "public": public,
        "private": {
            "train": private_train,
            "test": private_test,
        },
        "limitations": [
            "prototype only; production remains fixed to after_first_diagonal",
            "bounded evidence for retained seeds and one generated episode per seed",
            "two settings do not establish a complete family of path phase orders",
            "ordinary inputs retain unequal gaps; balanced pure diagonals remain out of scope",
        ],
    }


def _default_seeds() -> list[int]:
    found: dict[str, int] = {}
    for seed in range(64):
        setting = choose_parameters(seed)[PARAMETER_NAME]
        found.setdefault(setting, seed)
        if set(found) == set(POSITION_VALUES):
            return [found[name] for name in POSITION_VALUES]
    raise RuntimeError("could not find deterministic seed coverage for both settings")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+")
    parser.add_argument(
        "--difficulty",
        choices=("easy", "medium", "hard"),
        default="easy",
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    root = find_root(__file__)
    out_dir = args.out_dir.resolve()
    seeds = args.seeds if args.seeds is not None else _default_seeds()

    rule_records: dict[str, dict[str, str]] = {}
    for name in POSITION_VALUES:
        rule_path = out_dir / "rules" / f"{name}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(program_for(name, root=root) + "\n", encoding="utf-8")
        rule_records[name] = {
            "path": str(rule_path),
            "sha256": _sha256_file(rule_path),
        }

    records: list[dict[str, Any]] = []
    for seed in seeds:
        evidence = materialize_episode(seed, difficulty=args.difficulty, root=root)
        public_path = out_dir / "public" / f"seed-{seed}.json"
        private_path = out_dir / "private" / f"seed-{seed}.json"
        _write_json(public_path, evidence["public"])
        private_document = dict(evidence)
        private_document.pop("public")
        _write_json(private_path, private_document)
        records.append(
            {
                "seed": seed,
                PARAMETER_NAME: evidence["parameter"][PARAMETER_NAME],
                "sample_start": evidence["sample_start"],
                "demonstration_difference_indices": evidence[
                    "demonstration_difference_indices"
                ],
                "query_difference_indices": evidence["query_difference_indices"],
                "public_path": str(public_path),
                "public_sha256": _sha256_file(public_path),
                "private_path": str(private_path),
                "private_sha256": _sha256_file(private_path),
            }
        )

    observed = {record[PARAMETER_NAME] for record in records}
    if observed != set(POSITION_VALUES):
        raise RuntimeError(
            "retained seeds must demonstrate both settings; "
            f"observed {sorted(observed)}"
        )

    summary = {
        "schema": "arc-parametric-prototype-summary-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "prototype_status": "proposed",
        "parameter_spec": PARAMETER_SPEC,
        "command": " ".join(shlex.quote(part) for part in [sys.executable, *sys.argv]),
        "rules": rule_records,
        "episodes": records,
        "limitations": [
            "prototype evidence only; no production API or approval change",
            "finite retained episodes do not prove identifiability for every seed",
        ],
    }
    _write_json(out_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
