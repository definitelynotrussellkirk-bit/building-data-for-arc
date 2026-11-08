#!/usr/bin/env python3
"""Proposed encoding-power episodes for ARC family e048c9ed.

The canonical object roles and reasoning stay fixed: locate the color-5 marker,
measure alternating horizontal bars, infer the repeated non-5 length when one
exists, and write a code at the marker column.  One hidden episode-level rule
parameter changes only the final code:

* ``encoding_power=2`` (canonical/default): ``abs(base) ** 2 mod 10``;
* ``encoding_power=1`` (proposed): ``abs(base) ** 1 mod 10``.

The selected production generator remains canonical.  This task-local prototype
chooses the parameter once per episode and executes every selected and rival
label with the packet's Racket bridge.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

REPO = Path(__file__).resolve().parents[4]
DEPENDENCY_ROOT = (
    REPO
    if (REPO / "RUNTIME_MANIFEST.json").is_file()
    else REPO / "shared" / "runtime"
)
sys.path.insert(0, str(DEPENDENCY_ROOT))

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.base import stable_rng
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "9fe97c2dd8a4"
PROTOTYPE_VERSION = "encoding-power-v1"
ALLOWED_POWERS = (1, 2)
DEFAULT_POWER = 2
MAX_ATTEMPTS_PER_PAIR = 256
CANONICAL_FRAGMENT = "(remainder (* base base) 10)"
LINEAR_FRAGMENT = "(remainder (abs base) 10)"
PARAMETER_SPEC = {
    "encoding_power": {
        "allowed": list(ALLOWED_POWERS),
        "canonical_default": DEFAULT_POWER,
        "chosen_once_per_episode": True,
        "input_constraints": [
            "inputs remain lawful under the selected canonical generator",
            "every retained pair gives different Racket outputs for powers 1 and 2",
            "all demonstrations therefore refute the other declared setting",
        ],
    }
}


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_power(power: int) -> int:
    if type(power) is not int or power not in ALLOWED_POWERS:
        raise ValueError(f"encoding_power must be one of {ALLOWED_POWERS}")
    return power


def canonical_program(*, root: Path | str | None = None) -> str:
    """Return the selected canonical Racket authority text unchanged."""
    resolved_root = Path(root).resolve() if root is not None else find_root(__file__)
    found: list[str] = []
    with canonical_path(resolved_root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if not isinstance(program, str) or not program.strip():
                    raise ValueError(f"canonical task {TASK_ID} has no program_solution")
                found.append(program)
    if len(found) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}, found {len(found)}")
    return found[0]


def render_program(
    encoding_power: int = DEFAULT_POWER,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize exact Racket for one bounded parameter setting."""
    power = _validate_power(encoding_power)
    canonical = canonical_program(root=root)
    count = canonical.count(CANONICAL_FRAGMENT)
    if count != 1:
        raise ValueError(
            "canonical rule drift: expected exactly one squared-code fragment, "
            f"found {count}"
        )
    if power == DEFAULT_POWER:
        return canonical
    return canonical.replace(CANONICAL_FRAGMENT, LINEAR_FRAGMENT, 1)


def choose_parameters(seed: int) -> dict[str, int]:
    """Choose the hidden parameter exactly once from the episode seed."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    rng = stable_rng(seed, f"{TASK_ID}|encoding_power", PROTOTYPE_VERSION)
    return {"encoding_power": ALLOWED_POWERS[rng.randrange(len(ALLOWED_POWERS))]}


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")"


def execute(
    grid: list[list[int]],
    program: str,
    bridge: RacketBridge,
) -> list[list[int]]:
    """Execute the exact materialized Racket lambda on one grid."""
    body = strip_rule_wrapper(strip_line_comments(program))
    return bridge.eval_text(f"({body} {_grid_literal(grid)})")


def _candidate_indices(seed: int) -> list[int]:
    rng = stable_rng(seed, f"{TASK_ID}|parametric-samples", PROTOTYPE_VERSION)
    start = rng.randrange(32)
    return list(range(start, start + MAX_ATTEMPTS_PER_PAIR))


def generate_episode(
    seed: int,
    *,
    encoding_power: int | None = None,
    difficulty: str = "medium",
    n_train: int = 3,
    n_test: int = 2,
    bridge: RacketBridge | None = None,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Build a complete source-bound episode with Racket labels for both settings."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")
    if any(type(value) is not int or not 1 <= value <= 10 for value in (n_train, n_test)):
        raise ValueError("n_train and n_test must each be integers in 1..10")
    selected_power = (
        choose_parameters(seed)["encoding_power"]
        if encoding_power is None
        else _validate_power(encoding_power)
    )
    rival_power = next(power for power in ALLOWED_POWERS if power != selected_power)
    resolved_root = Path(root).resolve() if root is not None else find_root(__file__)
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID,
        root=resolved_root,
    )
    programs = {
        power: render_program(power, root=resolved_root) for power in ALLOWED_POWERS
    }

    owns_bridge = bridge is None
    active_bridge = bridge if bridge is not None else RacketBridge()
    accepted: list[dict[str, Any]] = []
    rejected_equal = 0
    try:
        for sample_index in _candidate_indices(seed):
            grid = generator.generate(seed, sample_index, difficulty=difficulty)
            outputs = {
                power: execute(grid, programs[power], active_bridge)
                for power in ALLOWED_POWERS
            }
            if outputs[1] == outputs[2]:
                rejected_equal += 1
                continue
            if outputs[DEFAULT_POWER] != generator.rule_mirror(grid):
                raise AssertionError(
                    "canonical/default Racket output disagrees with selected Python mirror"
                )
            accepted.append(
                {
                    "sample_index": sample_index,
                    "input": grid,
                    "output": outputs[selected_power],
                    "rival_output": outputs[rival_power],
                    "settings_disagree": True,
                }
            )
            if len(accepted) == n_train + n_test:
                break
    finally:
        if owns_bridge:
            active_bridge.shutdown()

    if len(accepted) != n_train + n_test:
        raise RuntimeError(
            f"found {len(accepted)} distinguishing pairs, needed {n_train + n_test}, "
            f"within {MAX_ATTEMPTS_PER_PAIR} attempts"
        )

    prototype_path = Path(__file__).resolve()
    canonical_data_path = canonical_path(resolved_root)
    return {
        "schema": "9fe97c2dd8a4-parametric-encoding-power-v1",
        "prototype_status": "proposed",
        "prototype_version": PROTOTYPE_VERSION,
        "task_id": TASK_ID,
        "seed": seed,
        "difficulty": difficulty,
        "parameters": {"encoding_power": selected_power},
        "parameter_spec": PARAMETER_SPEC,
        "program": programs[selected_power],
        "program_sha256": _sha256_text(programs[selected_power]),
        "rival_program_sha256": _sha256_text(programs[rival_power]),
        "demonstrations_refute": [rival_power],
        "train": accepted[:n_train],
        "test": accepted[n_train:],
        "accepted_sample_indices": [pair["sample_index"] for pair in accepted],
        "rejected_equal_output_candidates": rejected_equal,
        "all_labels_and_rivals_executed_in_racket": True,
        "sources": {
            "prototype_path": str(prototype_path),
            "prototype_sha256": _sha256_file(prototype_path),
            "generator_path": str(generator_path),
            "generator_sha256": generator_sha256,
            "canonical_path": str(canonical_data_path),
            "canonical_sha256": _sha256_file(canonical_data_path),
        },
        "limitations": [
            "prototype only; selected production generation remains canonical power 2",
            "only powers 1 and 2 are declared and compared",
            "retained inputs are rejection-sampled to make the two settings observable",
            "finite retained episodes do not prove identifiability against undeclared rules",
        ],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return the public ARC view with hidden semantics and query labels removed."""
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--difficulty",
        choices=("easy", "medium", "hard"),
        default="medium",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    with RacketBridge() as bridge:
        episodes = [
            generate_episode(
                args.seed,
                encoding_power=power,
                difficulty=args.difficulty,
                bridge=bridge,
            )
            for power in ALLOWED_POWERS
        ]
        runtime_identity = bridge.runtime_identity

    for index, episode in enumerate(episodes):
        _write_json(out / f"public-{index}.json", public_challenge(episode))
        _write_json(out / f"private-{index}.json", episode)
        (out / f"program-{index}.rkt").write_text(
            episode["program"], encoding="utf-8"
        )

    witness_grid = [
        [0, 0, 0, 0, 5, 0],
        [0, 0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [3, 3, 3, 3, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    with RacketBridge() as bridge:
        witness = {
            "input": witness_grid,
            "outputs": {
                str(power): execute(witness_grid, render_program(power), bridge)
                for power in ALLOWED_POWERS
            },
        }
    _write_json(out / "witness.json", witness)

    test_path = REPO / "generators" / TASK_ID / "tests" / "test_parametric_encoding_power.py"
    receipt = {
        "schema": "arc-parametric-prototype-receipt-v1",
        "status": "proposed",
        "task_id": TASK_ID,
        "seed": args.seed,
        "difficulty": args.difficulty,
        "parameters": PARAMETER_SPEC,
        "default": DEFAULT_POWER,
        "argv": sys.argv,
        "runtime_identity": runtime_identity,
        "source_sha256": {
            str(Path(__file__).resolve().relative_to(REPO)): _sha256_file(Path(__file__).resolve()),
            str(test_path.relative_to(REPO)): _sha256_file(test_path),
        },
        "complete_episodes": len(episodes),
        "pairs_per_episode": {"train": 3, "test": 2},
        "all_labels_and_rivals_executed_in_racket": True,
        "all_demonstrations_refute_other_declared_setting": True,
        "limitations": episodes[0]["limitations"],
    }
    _write_json(out / "receipt.json", receipt)
    print(
        json.dumps(
            {
                "status": "proposed",
                "complete_episodes": len(episodes),
                "executed_pairs": 5 * len(episodes),
                "out": str(out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
