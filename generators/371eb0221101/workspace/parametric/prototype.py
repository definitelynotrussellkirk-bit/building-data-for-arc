#!/usr/bin/env python3
"""Proposed episode-level rotation-direction prototype for 371eb0221101.

This file is intentionally separate from the selected canonical generator.  It
chooses one hidden ``quarter_turns`` value once per episode, generates all inputs
with the repaired canonical sampler, and labels every pair by executing the exact
materialized Racket program through the included bridge.
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

TASK_ID = "371eb0221101"
PROTOTYPE_VERSION = "rotation-quarter-turns-v1"
TURN_VALUES = (1, 3)
CANONICAL_DEFAULT = 1
N_TRAIN = 3
N_TEST = 1
FORWARD_FRAGMENT = "(t3b-rotate-offsets offs 1)"

PARAMETER_SPEC = {
    "quarter_turns": {
        "allowed": list(TURN_VALUES),
        "canonical_default": CANONICAL_DEFAULT,
        "chosen_once_per_episode": True,
        "meaning": {"1": "90 degrees clockwise", "3": "90 degrees counterclockwise"},
        "input_constraints": [
            "every object is an isolated L-triomino in a tight 2x2 box",
            "at least one demonstration is present; every L distinguishes 1 from 3 turns",
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
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    if len(rows) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}, found {len(rows)}")
    if not isinstance(rows[0].get("program_solution"), str):
        raise ValueError("canonical row has no Racket program_solution")
    return rows[0]


def program_for(quarter_turns: int = CANONICAL_DEFAULT, *, root: Path | str | None = None) -> str:
    """Return the exact Racket program for one bounded parameter value."""
    if type(quarter_turns) is not int or quarter_turns not in TURN_VALUES:
        raise ValueError(f"quarter_turns must be one of {TURN_VALUES}")
    resolved = Path(root).resolve() if root is not None else find_root(__file__)
    canonical = _canonical_row(resolved)["program_solution"]
    count = canonical.count(FORWARD_FRAGMENT)
    if count != 1:
        raise ValueError(f"canonical rule drift: expected one rotation fragment, found {count}")
    if quarter_turns == CANONICAL_DEFAULT:
        return canonical
    return canonical.replace(
        FORWARD_FRAGMENT,
        f"(t3b-rotate-offsets offs {quarter_turns})",
        1,
    )


def choose_parameters(seed: int) -> dict[str, int]:
    """Choose the hidden rule once from the episode seed."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    rng = stable_rng(seed, f"{TASK_ID}|quarter_turns", PROTOTYPE_VERSION)
    return {"quarter_turns": TURN_VALUES[rng.randrange(len(TURN_VALUES))]}


def _racket_outputs(program: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    body = strip_rule_wrapper(program)
    bridge = RacketBridge()
    try:
        outputs = []
        for grid in grids:
            bridge.define_grid("g", grid)
            outputs.append(bridge.eval_text(body))
        return outputs
    finally:
        bridge.shutdown()


def _mirror(generator, grid, quarter_turns: int):
    out = [[0] * len(grid[0]) for _ in grid]
    for color, cells in generator._components(grid):
        target = cells
        for _ in range(quarter_turns):
            target = generator._rotate_cells_cw(target)
        for r, c in target:
            out[r][c] = color
    return out


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
    turns = choose_parameters(seed)["quarter_turns"]
    rival_turns = 3 if turns == 1 else 1
    start = stable_rng(seed, f"{TASK_ID}|episode_start", PROTOTYPE_VERSION).randrange(10_000)
    grids = [
        generator.generate(seed, start + index, difficulty=difficulty)
        for index in range(N_TRAIN + N_TEST)
    ]
    programs = {value: program_for(value, root=resolved) for value in TURN_VALUES}
    outputs = {value: _racket_outputs(programs[value], grids) for value in TURN_VALUES}
    for value in TURN_VALUES:
        mirrors = [_mirror(generator, grid, value) for grid in grids]
        if outputs[value] != mirrors:
            raise AssertionError(f"Racket output disagrees with {value}-turn Python mirror")

    differences = [outputs[1][i] != outputs[3][i] for i in range(len(grids))]
    demo_differences = [i for i, differs in enumerate(differences[:N_TRAIN]) if differs]
    query_differences = [i for i, differs in enumerate(differences[N_TRAIN:]) if differs]
    if len(demo_differences) != N_TRAIN or query_differences != [0]:
        raise AssertionError("episode failed to distinguish both parameter settings")

    selected = outputs[turns]
    rival = outputs[rival_turns]
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
        "sample_start": start,
        "parameter": {
            "quarter_turns": turns,
            "allowed": list(TURN_VALUES),
            "canonical_default": CANONICAL_DEFAULT,
        },
        "parameter_spec": PARAMETER_SPEC,
        "rival_setting": rival_turns,
        "demonstration_difference_indices": demo_differences,
        "query_difference_indices": query_differences,
        "racket_verified": True,
        "programs": {
            str(value): {"text": text, "sha256": _sha256_text(text)}
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
            "prototype only; production remains bound to the canonical one-turn Racket rule",
            "bounded evidence for retained seeds and generated episodes, not all seeds or hypotheses",
            "only L-triomino inputs were assessed; no general arbitrary-object parameter API is proposed",
        ],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 2])
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="easy")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    root = find_root(__file__)
    out_dir = args.out_dir.resolve()
    records = []
    observed = set()
    for seed in args.seeds:
        evidence = materialize_episode(seed, difficulty=args.difficulty, root=root)
        turns = evidence["parameter"]["quarter_turns"]
        observed.add(turns)
        public_path = out_dir / f"seed-{seed}-public.json"
        private_path = out_dir / f"seed-{seed}-private.json"
        _write_json(public_path, evidence["public"])
        private_document = dict(evidence)
        private_document.pop("public")
        _write_json(private_path, private_document)
        rules_dir = out_dir / "rules"
        for value, record in evidence["programs"].items():
            rule_path = rules_dir / f"quarter-turns-{value}.rkt"
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            rule_path.write_text(record["text"] + "\n", encoding="utf-8")
        records.append({
            "seed": seed,
            "quarter_turns": turns,
            "sample_start": evidence["sample_start"],
            "demonstration_difference_indices": evidence["demonstration_difference_indices"],
            "query_difference_indices": evidence["query_difference_indices"],
            "public_path": str(public_path),
            "public_sha256": _sha256_file(public_path),
            "private_path": str(private_path),
            "private_sha256": _sha256_file(private_path),
        })
    if observed != set(TURN_VALUES):
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
