#!/usr/bin/env python3
"""Proposed episode-level disagreement-action variants for ARC family e84fef15.

The original reasoning is unchanged in both settings: split the 29x29 input into
25 aligned 5x5 copies and combine corresponding coordinates across copies.

* ``mark`` (canonical/default) returns unanimous values and writes color 1 at
  disagreement coordinates.
* ``restore`` (proposed) resolves every coordinate to its modal copy value.

This is a task-local authoring prototype.  Production remains fixed to the
canonical ``mark`` rule and its pinned rule hash.
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
    REPO if (REPO / "RUNTIME_MANIFEST.json").is_file() else REPO / "shared" / "runtime"
)
if str(DEPENDENCY_ROOT) not in sys.path:
    sys.path.insert(0, str(DEPENDENCY_ROOT))

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.base import stable_rng
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "8b320727aa72"
PROTOTYPE_VERSION = "disagreement-action-v1"
STATUS = "proposed prototype; not production-approved"
ALLOWED_ACTIONS = ("mark", "restore")
DEFAULT_ACTION = "mark"
PARAMETER_SPEC = {
    "disagreement_action": {
        "allowed": list(ALLOWED_ACTIONS),
        "canonical_default": DEFAULT_ACTION,
        "chosen_once_per_episode": True,
        "input_constraints": [
            "input remains in the selected 24-consensus-plus-one-erasure grammar",
            "at least one copy disagreement is present in every pair",
            "demonstrations must distinguish mark from restore",
        ],
    }
}

_CANONICAL_DECISION = """(cond
                             ((= (length unique-vals) 1) (first unique-vals))
                             (else 1))"""
_RESTORE_DECISION = "(mode-list values)"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_action(action: str) -> str:
    if type(action) is not str or action not in ALLOWED_ACTIONS:
        raise ValueError(f"disagreement_action must be one of {ALLOWED_ACTIONS}")
    return action


def canonical_program(*, root: Path | str | None = None) -> str:
    """Return the one unique canonical program text across task variants."""
    resolved_root = Path(root).resolve() if root is not None else find_root(__file__)
    programs: set[str] = set()
    with canonical_path(resolved_root).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            program = row.get("program_solution")
            if not isinstance(program, str) or not program.strip():
                raise ValueError(f"canonical task {TASK_ID} has no program_solution")
            programs.add(program)
    if len(programs) != 1:
        raise ValueError(
            f"expected one unique canonical program for {TASK_ID}, found {len(programs)}"
        )
    return next(iter(programs))


def rule_for(
    disagreement_action: str = DEFAULT_ACTION,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize exact Racket for one bounded disagreement action."""
    action = _validate_action(disagreement_action)
    canonical = canonical_program(root=root)
    count = canonical.count(_CANONICAL_DECISION)
    if count != 1:
        raise ValueError(
            "canonical rule drift: expected exactly one disagreement decision, "
            f"found {count}"
        )
    if action == DEFAULT_ACTION:
        return canonical
    return canonical.replace(_CANONICAL_DECISION, _RESTORE_DECISION, 1)


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose the hidden rule once from the episode seed."""
    if type(seed) is not int:
        raise ValueError("seed must be an integer (bool is not accepted)")
    rng = stable_rng(seed, f"{TASK_ID}|disagreement_action", PROTOTYPE_VERSION)
    return {"disagreement_action": ALLOWED_ACTIONS[rng.randrange(len(ALLOWED_ACTIONS))]}


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")"


def execute_rule(
    program: str,
    grid: list[list[int]],
    bridge: RacketBridge,
) -> list[list[int]]:
    """Execute the exact materialized Racket rule on one grid."""
    callable_text = strip_rule_wrapper(strip_line_comments(program))
    return bridge.eval_text(f"({callable_text} {_grid_literal(grid)})")


def materialize_episode(
    seed: int,
    *,
    disagreement_action: str | None = None,
    difficulty: str = "medium",
    n_demos: int = 2,
    n_queries: int = 1,
    bridge: RacketBridge | None = None,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Build one complete private episode, with every label executed in Racket."""
    if type(seed) is not int:
        raise ValueError("seed must be an integer (bool is not accepted)")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")
    if any(type(value) is not int or not 1 <= value <= 10 for value in (n_demos, n_queries)):
        raise ValueError("n_demos and n_queries must each be integers in 1..10")

    selected = (
        choose_parameters(seed)["disagreement_action"]
        if disagreement_action is None
        else _validate_action(disagreement_action)
    )
    rival = next(action for action in ALLOWED_ACTIONS if action != selected)
    resolved_root = Path(root).resolve() if root is not None else find_root(__file__)
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID,
        root=resolved_root,
    )
    programs = {action: rule_for(action, root=resolved_root) for action in ALLOWED_ACTIONS}

    owns_bridge = bridge is None
    active_bridge = bridge if bridge is not None else RacketBridge()
    pairs: list[dict[str, Any]] = []
    try:
        for sample_index in range(n_demos + n_queries):
            grid = generator.generate(seed, sample_index, difficulty=difficulty)
            errors = generator.self_check(grid, difficulty=difficulty)
            if errors:
                raise ValueError(
                    f"selected generator emitted an invalid pair at {sample_index}: {errors}"
                )
            outputs = {
                action: execute_rule(programs[action], grid, active_bridge)
                for action in ALLOWED_ACTIONS
            }
            if outputs["mark"] != generator._canonical_mark_output(grid):
                raise AssertionError("canonical Racket output disagrees with mark mirror")
            if outputs["restore"] != generator._restore_consensus_output(grid):
                raise AssertionError("restore Racket output disagrees with restore mirror")
            if outputs["mark"] == outputs["restore"]:
                raise AssertionError(
                    f"pair {sample_index} does not distinguish the declared actions"
                )
            pairs.append(
                {
                    "sample_index": sample_index,
                    "input": grid,
                    "selected_output": outputs[selected],
                    "rival_output": outputs[rival],
                    "settings_disagree": True,
                }
            )
    finally:
        if owns_bridge:
            active_bridge.shutdown()

    prototype_path = Path(__file__).resolve()
    canonical_data_path = canonical_path(resolved_root)
    return {
        "schema": "8b320727aa72-parametric-disagreement-action-v1",
        "status": STATUS,
        "prototype_version": PROTOTYPE_VERSION,
        "task_id": TASK_ID,
        "seed": seed,
        "difficulty": difficulty,
        "parameters": {"disagreement_action": selected},
        "parameter_spec": PARAMETER_SPEC,
        "program": programs[selected],
        "program_sha256": _sha256_text(programs[selected]),
        "rival_program_sha256": _sha256_text(programs[rival]),
        "demonstrations_refute": [rival],
        "train": pairs[:n_demos],
        "test": pairs[n_demos:],
        "query_answers": [deepcopy(pair["selected_output"]) for pair in pairs[n_demos:]],
        "all_labels_executed_in_racket": True,
        "sources": {
            "prototype_path": str(prototype_path),
            "prototype_sha256": _sha256_file(prototype_path),
            "generator_path": str(generator_path),
            "generator_sha256": generator_sha256,
            "canonical_path": str(canonical_data_path),
            "canonical_sha256": _sha256_file(canonical_data_path),
        },
        "limitations": [
            "prototype only; selected production execution remains canonical mark",
            "only mark and restore are declared",
            "finite materialized episodes do not establish universal identifiability",
            "production inputs remain erasure-only and do not test arbitrary substitutions",
        ],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return an ARC-style public view with hidden semantics/query labels removed."""
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "train": [
            {
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["selected_output"]),
            }
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_evidence(
    out: Path | str,
    *,
    mark_seed: int = 10,
    restore_seed: int = 11,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Materialize programs, complete episodes, public views, and a shared witness."""
    out = Path(out)
    resolved_root = Path(root).resolve() if root is not None else find_root(__file__)
    for folder in ("rules", "private", "public"):
        (out / folder).mkdir(parents=True, exist_ok=True)

    programs = {action: rule_for(action, root=resolved_root) for action in ALLOWED_ACTIONS}
    for action, program in programs.items():
        (out / "rules" / f"{action}.rkt").write_text(program, encoding="utf-8")

    episode_rows = []
    with RacketBridge(max_calls_before_restart=128) as bridge:
        runtime_identity = bridge.runtime_identity
        for action, seed in (("mark", mark_seed), ("restore", restore_seed)):
            episode = materialize_episode(
                seed,
                disagreement_action=action,
                bridge=bridge,
                root=resolved_root,
            )
            _write_json(out / "private" / f"episode-{action}.json", episode)
            _write_json(
                out / "public" / f"episode-{action}.json",
                public_challenge(episode),
            )
            episode_rows.append(
                {
                    "action": action,
                    "seed": seed,
                    "private": f"private/episode-{action}.json",
                    "public": f"public/episode-{action}.json",
                    "program_sha256": episode["program_sha256"],
                    "demonstrations_refute": episode["demonstrations_refute"],
                }
            )

        generator, generator_path, generator_sha256 = load_selected_generator(
            TASK_ID,
            root=resolved_root,
        )
        witness_input = generator.generate(20261023, 0, difficulty="medium")
        witness_outputs = {
            action: execute_rule(programs[action], witness_input, bridge)
            for action in ALLOWED_ACTIONS
        }
        if witness_outputs["mark"] == witness_outputs["restore"]:
            raise AssertionError("shared witness failed to distinguish settings")
        _write_json(
            out / "private" / "shared-witness.json",
            {
                "input": witness_input,
                "outputs": witness_outputs,
                "generator_seed": 20261023,
                "sample_index": 0,
                "difficulty": "medium",
            },
        )

    prototype_path = Path(__file__).resolve()
    canonical_data_path = canonical_path(resolved_root)
    manifest = {
        "schema": "8b320727aa72-parametric-disagreement-action-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameter_spec": PARAMETER_SPEC,
        "canonical_default_unchanged": programs[DEFAULT_ACTION]
        == canonical_program(root=resolved_root),
        "program_sha256": {
            action: _sha256_text(program) for action, program in programs.items()
        },
        "episodes": episode_rows,
        "shared_witness": "private/shared-witness.json",
        "all_labels_and_rivals_executed_in_racket": True,
        "sources": {
            "prototype": str(prototype_path.relative_to(resolved_root)),
            "prototype_sha256": _sha256_file(prototype_path),
            "generator": str(Path(generator_path).relative_to(resolved_root)),
            "generator_sha256": generator_sha256,
            "canonical": str(canonical_data_path.relative_to(resolved_root)),
            "canonical_sha256": _sha256_file(canonical_data_path),
        },
        "racket_runtime": runtime_identity,
        "command": (
            "python3 review.py run python3 "
            "generators/8b320727aa72/workspace/parametric/prototype.py "
            "--out ../checks/parametric"
        ),
        "limitations": [
            "proposed task-local prototype; no production parametric API",
            "bounded to two actions and two retained complete episodes",
            "finite rival checks do not prove uniqueness against undeclared rules",
            "erasure-only input grammar leaves oracle totality beyond that grammar untested",
        ],
    }
    _write_json(out / "manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mark-seed", type=int, default=10)
    parser.add_argument("--restore-seed", type=int, default=11)
    args = parser.parse_args(argv)
    manifest = write_evidence(
        args.out,
        mark_seed=args.mark_seed,
        restore_seed=args.restore_seed,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
