#!/usr/bin/env python3
"""Proposed task-local diagonal-axis episodes; no production API or approval change."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "shared/runtime"))
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper, strip_line_comments

ALLOWED_AXES = ("main_diagonal", "anti_diagonal")
DEFAULT_AXIS = "main_diagonal"
MAX_ATTEMPTS = 100


def render_program(reflection_axis=DEFAULT_AXIS):
    if reflection_axis not in ALLOWED_AXES:
        raise ValueError(f"reflection_axis must be one of {ALLOWED_AXES}")
    reflected = "(transpose g)" if reflection_axis == DEFAULT_AXIS else "(rotate-180 (transpose g))"
    return ("(rule!\n"
            ";; A square grid has sparse colored source cells on a zero background.\n"
            f";; Copy each source across the {reflection_axis.replace('_', ' ')} and keep the original.\n"
            ";; Inputs exclude occupied reflected targets, so colors never conflict.\n"
            f" (lambda (g) (overlay g {reflected})))\n")


def execute(grid, program, bridge):
    """Execute the exact materialized lambda after removing only the rule! marker/comments."""
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    callable_rule = strip_rule_wrapper(strip_line_comments(program))
    return bridge.eval_text(f"({callable_rule} {literal})")


def _draw_grid(rng):
    size = rng.randint(4, 10)
    grid = [[0] * size for _ in range(size)]
    candidates = [(r, c) for r in range(size) for c in range(size)
                  if r != c and r + c != size - 1]
    rng.shuffle(candidates)
    target = rng.randint(1, size)
    for r, c in candidates:
        if not grid[c][r] and not grid[size - 1 - c][size - 1 - r]:
            grid[r][c] = rng.randint(1, 9)
            target -= 1
            if target == 0:
                return grid
    raise RuntimeError("bounded input draw cannot satisfy collision constraints")


def generate_episode(seed, *, reflection_axis=None, n_train=3, n_test=2, bridge=None):
    """Choose the rule once, then execute it unchanged for all demonstrations/queries."""
    if reflection_axis is not None and reflection_axis not in ALLOWED_AXES:
        raise ValueError(f"unsupported reflection_axis: {reflection_axis!r}")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")
    if any(not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 10
           for n in (n_train, n_test)):
        raise ValueError("n_train and n_test must each be integers in 1..10")
    rng = random.Random(seed)
    axis = reflection_axis if reflection_axis is not None else rng.choice(ALLOWED_AXES)
    programs = {value: render_program(value) for value in ALLOWED_AXES}
    if bridge is None:
        with RacketBridge() as own_bridge:
            return _episode(seed, axis, rng, n_train, n_test, own_bridge, programs)
    return _episode(seed, axis, rng, n_train, n_test, bridge, programs)


def _episode(seed, axis, rng, n_train, n_test, bridge, programs):
    pairs, rivals = [], []
    for _ in range(n_train + n_test):
        for attempt in range(MAX_ATTEMPTS):
            grid = _draw_grid(rng)
            outputs = {value: execute(grid, program, bridge) for value, program in programs.items()}
            # A demonstration always exposes which diagonal; query inputs are
            # also informative. Rejection decisions use executed Racket labels.
            if outputs[ALLOWED_AXES[0]] != outputs[ALLOWED_AXES[1]]:
                pairs.append({"input": grid, "output": outputs[axis]})
                rivals.append({value: outputs[value] for value in ALLOWED_AXES if value != axis})
                break
        else:
            raise RuntimeError(f"no distinguishing input in {MAX_ATTEMPTS} bounded attempts")
    return {"schema": "e58027e9749f-parametric-prototype-v1", "seed": seed,
            "parameters": {"reflection_axis": axis}, "program": programs[axis],
            "program_sha256": hashlib.sha256(programs[axis].encode()).hexdigest(),
            "train": pairs[:n_train], "test": pairs[n_train:],
            "rival_outputs": {"train": rivals[:n_train], "test": rivals[n_train:]},
            "demonstrations_refute": [value for value in ALLOWED_AXES if value != axis]}


def public_challenge(episode):
    """Public ARC challenge: no rule, hidden choice, provenance, or query labels."""
    return {"train": deepcopy(episode["train"]),
            "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--axis", choices=ALLOWED_AXES)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    with RacketBridge() as bridge:
        episodes = [generate_episode(args.seed, reflection_axis=axis, bridge=bridge)
                    for axis in ((args.axis,) if args.axis else ALLOWED_AXES)]
        witness = [[0, 7, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        evidence = {"input": witness, "outputs": {
            axis: execute(witness, render_program(axis), bridge) for axis in ALLOWED_AXES}}
        runtime_identity = bridge.runtime_identity
    for index, episode in enumerate(episodes):
        # Neutral filenames disclose no hidden rule parameter.
        (args.out / f"public-{index}.json").write_text(json.dumps(public_challenge(episode), indent=2) + "\n")
        (args.out / f"private-{index}.json").write_text(json.dumps(episode, indent=2) + "\n")
        (args.out / f"program-{index}.rkt").write_text(episode["program"])
    source_files = [Path(__file__), REPO / "generators/e58027e9749f/tests/test_parametric_reflection.py"]
    receipt = {"status": "prototype", "seed": args.seed,
               "parameters": {"reflection_axis": list(ALLOWED_AXES)}, "default": DEFAULT_AXIS,
               "argv": sys.argv, "runtime_identity": runtime_identity,
               "source_sha256": {str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in source_files},
               "complete_episodes": len(episodes), "pairs_per_episode": {"train": 3, "test": 2},
               "all_labels_and_rivals_executed_in_racket": True,
               "all_demonstrations_refute_other_declared_setting": True,
               "limitations": ["Only two diagonal settings, square zero-background grids of size 4..10.",
                               "Every input excludes both diagonal fixed points and both reflected-target collisions.",
                               "One to grid-size colored source cells, colors 1..9; at most 100 input attempts per pair.",
                               "Only the declared parameter rival is exhaustively compared on these finite examples.",
                               "A task-local proposal, not production generation, approval, or universal seed proof."]}
    (args.out / "witness.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (args.out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "prototype", "complete_episodes": len(episodes),
                      "executed_pairs": 5 * len(episodes), "out": str(args.out)}))


if __name__ == "__main__":
    main()
