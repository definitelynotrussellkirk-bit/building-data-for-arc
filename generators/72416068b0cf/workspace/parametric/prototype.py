#!/usr/bin/env python3
"""Task-local composition-order prototype for ARC generator 72416068b0cf.

This is deliberately separate from the selected canonical generator.  It keeps
all input-generation logic fixed and chooses one hidden rule parameter once per
episode:

* ``forward`` (canonical/default): apply header step1, then step2.
* ``reverse`` (proposed variant): apply header step2, then step1.

Every retained output is produced by the included Racket bridge.  Python mirrors
are used only to find a compact episode whose demonstrations and query distinguish
the two settings; the bridge results are then checked against both mirrors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from pathlib import Path
from typing import Any, Iterable

from puzzle_generators.base import stable_rng
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "72416068b0cf"
PROTOTYPE_VERSION = "parametric-v1"
ORDER_VALUES = ("forward", "reverse")
CANONICAL_DEFAULT = "forward"
N_TRAIN = 4
N_TEST = 1
MAX_START_PROBES = 64

# The canonical ledger contains this expression exactly once.  The alternative
# program changes only the two applications' order; selector, crop, transforms,
# and all error behavior stay unchanged.
FORWARD_FRAGMENT = (
    "(s17b-transform-code (s17b-transform-code "
    "(s17b-object-crop work hit) step1) step2)"
)
REVERSE_FRAGMENT = (
    "(s17b-transform-code (s17b-transform-code "
    "(s17b-object-crop work hit) step2) step1)"
)

PARAMETER_SPEC = {
    "composition_order": {
        "allowed": list(ORDER_VALUES),
        "canonical_default": CANONICAL_DEFAULT,
        "chosen_once_per_episode": True,
        "input_constraints": [
            "four generated demonstrations",
            "at least one demonstration has different forward/reverse Racket outputs",
            "the held-out query also has different forward/reverse Racket outputs",
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
    if len(rows) != 1:
        raise ValueError(f"expected exactly one canonical row for {TASK_ID}, found {len(rows)}")
    program = rows[0].get("program_solution")
    if not isinstance(program, str) or not program.strip():
        raise ValueError(f"canonical row for {TASK_ID} has no program_solution")
    return rows[0]


def program_for(order: str = CANONICAL_DEFAULT, *, root: Path | str | None = None) -> str:
    """Materialize the exact Racket program for one bounded parameter value."""
    if order not in ORDER_VALUES:
        raise ValueError(f"composition_order must be one of {ORDER_VALUES}, got {order!r}")
    resolved_root = Path(root).resolve() if root is not None else find_root(__file__)
    canonical = _canonical_row(resolved_root)["program_solution"]
    count = canonical.count(FORWARD_FRAGMENT)
    if count != 1:
        raise ValueError(
            f"canonical rule drift: expected one forward-order fragment, found {count}"
        )
    if REVERSE_FRAGMENT in canonical:
        raise ValueError("canonical rule unexpectedly already contains reverse fragment")
    if order == "forward":
        return canonical
    return canonical.replace(FORWARD_FRAGMENT, REVERSE_FRAGMENT, 1)


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose the hidden parameter once from the episode seed."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    rng = stable_rng(
        seed,
        f"{TASK_ID}|composition_order",
        PROTOTYPE_VERSION,
    )
    return {"composition_order": ORDER_VALUES[rng.randrange(len(ORDER_VALUES))]}


def _candidate_starts(seed: int) -> Iterable[int]:
    rng = stable_rng(seed, f"{TASK_ID}|parametric_start", PROTOTYPE_VERSION)
    first = rng.randrange(32)
    for offset in range(MAX_START_PROBES):
        yield first + offset


def _racket_outputs(program: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    # The task's canonical source is a plain `(rule! BODY)` with no comments,
    # dict literals, or for-shorthand.  Evaluate that exact BODY against `g`
    # directly, as the generic parity helpers do.  This avoids the general
    # wrapper's repository-only `scripts.comment_solutions` dependency and
    # keeps the README command portable in the packet source tree.
    body = strip_rule_wrapper(program)
    bridge = RacketBridge()
    try:
        results = []
        for grid in grids:
            bridge.define_grid("g", grid)
            results.append(bridge.eval_text(body))
        return results
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
        # Hidden parameter, Racket source, and query answers are intentionally absent.
        "test": [{"input": grid} for grid in grids[N_TRAIN:]],
    }


def materialize_episode(
    seed: int,
    *,
    difficulty: str = "medium",
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Build one source-bound episode and execute both parameter settings in Racket."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")

    resolved_root = Path(root).resolve() if root is not None else find_root(__file__)
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID,
        root=resolved_root,
    )
    order = choose_parameters(seed)["composition_order"]
    rival_order = "reverse" if order == "forward" else "forward"

    selected_start: int | None = None
    grids: list[list[list[int]]] | None = None
    # This is a selection constraint, not a source of labels.  It guarantees the
    # public demonstrations identify the hidden setting before the held-out query.
    for start in _candidate_starts(seed):
        candidate = [
            generator.generate(seed, start + index, difficulty=difficulty)
            for index in range(N_TRAIN + N_TEST)
        ]
        mirror_disagreements = [
            generator._solve(grid) != generator._rival_reverse_order(grid)
            for grid in candidate
        ]
        if any(mirror_disagreements[:N_TRAIN]) and all(
            mirror_disagreements[N_TRAIN:]
        ):
            selected_start = start
            grids = candidate
            break
    if selected_start is None or grids is None:
        raise RuntimeError(
            f"no order-distinguishing {N_TRAIN}+{N_TEST} episode found in "
            f"{MAX_START_PROBES} starts for seed {seed}"
        )

    programs = {name: program_for(name, root=resolved_root) for name in ORDER_VALUES}
    outputs = {name: _racket_outputs(programs[name], grids) for name in ORDER_VALUES}

    forward_mirror = [generator._solve(grid) for grid in grids]
    reverse_mirror = [generator._rival_reverse_order(grid) for grid in grids]
    if outputs["forward"] != forward_mirror:
        raise AssertionError("forward Racket output disagrees with canonical Python mirror")
    if outputs["reverse"] != reverse_mirror:
        raise AssertionError("reverse Racket output disagrees with proposed Python mirror")

    differences = [
        outputs["forward"][index] != outputs["reverse"][index]
        for index in range(len(grids))
    ]
    demonstration_difference_indices = [
        index for index, differs in enumerate(differences[:N_TRAIN]) if differs
    ]
    query_difference_indices = [
        index for index, differs in enumerate(differences[N_TRAIN:]) if differs
    ]
    if not demonstration_difference_indices or len(query_difference_indices) != N_TEST:
        raise AssertionError("retained Racket episode does not satisfy distinction constraints")

    selected_outputs = outputs[order]
    rival_outputs = outputs[rival_order]
    public = _public_episode(grids, selected_outputs)
    private = {
        "train": [
            {
                "input": grids[index],
                "output": selected_outputs[index],
                "rival_output": rival_outputs[index],
                "settings_disagree": differences[index],
            }
            for index in range(N_TRAIN)
        ],
        "test": [
            {
                "input": grids[index],
                "output": selected_outputs[index],
                "rival_output": rival_outputs[index],
                "settings_disagree": differences[index],
            }
            for index in range(N_TRAIN, N_TRAIN + N_TEST)
        ],
    }

    prototype_path = Path(__file__).resolve()
    canonical_path_value = canonical_path(resolved_root)
    return {
        "schema": "arc-parametric-prototype-evidence-v1",
        "task_id": TASK_ID,
        "prototype_status": "proposed",
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "difficulty": difficulty,
        "sample_start": selected_start,
        "parameter": {
            "composition_order": order,
            "allowed": list(ORDER_VALUES),
            "canonical_default": CANONICAL_DEFAULT,
        },
        "parameter_spec": PARAMETER_SPEC,
        "rival_setting": rival_order,
        "demonstration_difference_indices": demonstration_difference_indices,
        "query_difference_indices": query_difference_indices,
        "racket_verified": True,
        "programs": {
            name: {"text": text, "sha256": _sha256_text(text)}
            for name, text in programs.items()
        },
        "sources": {
            "prototype_path": str(prototype_path),
            "prototype_sha256": _sha256_file(prototype_path),
            "generator_path": str(generator_path),
            "generator_sha256": generator_sha256,
            "canonical_path": str(canonical_path_value),
            "canonical_sha256": _sha256_file(canonical_path_value),
        },
        "public": public,
        "private": private,
        "limitations": [
            "prototype only; the selected canonical execution path remains fixed forward order",
            "bounded evidence for the retained seeds and one generated episode per seed",
            "forward/reverse is not a universal parameter family proof for every seed or input",
        ],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[2, 0])
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="easy")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    root = find_root(__file__)
    out_dir = args.out_dir.resolve()
    records: list[dict[str, Any]] = []
    for seed in args.seeds:
        evidence = materialize_episode(seed, difficulty=args.difficulty, root=root)
        public_path = out_dir / f"seed-{seed}-public.json"
        private_path = out_dir / f"seed-{seed}-private.json"
        _write_json(public_path, evidence["public"])
        private_document = dict(evidence)
        private_document.pop("public")
        _write_json(private_path, private_document)
        records.append(
            {
                "seed": seed,
                "composition_order": evidence["parameter"]["composition_order"],
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

    observed = {record["composition_order"] for record in records}
    if observed != set(ORDER_VALUES):
        raise RuntimeError(
            f"retained seeds must demonstrate both settings; observed {sorted(observed)}"
        )
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
