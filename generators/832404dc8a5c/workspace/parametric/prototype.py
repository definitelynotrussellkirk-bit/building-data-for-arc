"""Proposed episode-level direction scope for task 832404dc8a5c.

This task-local authoring prototype does not replace the canonical generator or
its rule. Every label and finite-rival comparison executes materialized Racket.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import random
import sys
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)


TASK_ID = "832404dc8a5c"
SCOPES = ("union", "rows", "columns")
DEFAULT_SCOPE = "union"
ROOT = find_root(__file__)


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _validate_seed(seed):
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")


def _validate_scope(scope):
    if scope not in SCOPES:
        raise ValueError(f"direction_scope must be one of {SCOPES!r}")
    return scope


def choose_scope(seed):
    """Choose one episode setting; input draws use a separate seed stream."""
    _validate_seed(seed)
    return random.Random(f"{TASK_ID}:direction_scope:{seed}").choice(SCOPES)


def materialize_program(scope=DEFAULT_SCOPE):
    """Return the complete exact rule text, with no unresolved placeholders."""
    _validate_scope(scope)
    selector = {
        "union": "(or row-selected? column-selected?)",
        "rows": "row-selected?",
        "columns": "column-selected?",
    }[scope]
    return f"""(rule! (lambda (g)
  (let ((h (rows g)) (w (cols g)))
    (grid-from-fn h w
      (lambda (r c)
        (let ((v (at g r c))
              (row-selected? (and (= 4 (at g r 0)) (= 4 (at g r (- w 1)))))
              (column-selected? (and (= 4 (at g 0 c)) (= 4 (at g (- h 1) c)))))
          (if {selector}
              (cond ((zero? v) 8)
                    ((= v 8) 0)
                    ((= v 6) 7)
                    ((= v 7) 6)
                    (else v))
              v)))))))
"""


def execute_program(program, grid, bridge):
    """Execute the exact (rule! callable) through the included Racket bridge.

    rule! is the host DSL's registration form. The lexical identity binding
    obtains that callable without rewriting the materialized program body.
    """
    grid = normalize_grid(grid)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    value = bridge.eval_text(f"(let ((rule! (lambda (f) f))) ({program} {literal}))")
    output = normalize_grid(value)
    if len(output) != len(grid) or len(output[0]) != len(grid[0]):
        raise ValueError("materialized rule changed the grid dimensions")
    return output


def audit_demonstrations(demonstrations, bridge):
    """Exhaustively test the three declared parameter rivals on demonstrations."""
    if not demonstrations:
        raise ValueError("at least one demonstration is required")
    rivals = {}
    for scope in SCOPES:
        program = materialize_program(scope)
        mismatches = [
            index
            for index, pair in enumerate(demonstrations)
            if execute_program(program, pair["input"], bridge) != pair["output"]
        ]
        rivals[scope] = {"mismatching_demonstrations": mismatches}
    return {
        "rival_space": "all declared direction_scope values; no claim about arbitrary programs",
        "survivors": [scope for scope in SCOPES if not rivals[scope]["mismatching_demonstrations"]],
        "rivals": rivals,
    }


def generate_episode(seed, *, scope=None, bridge=None):
    """Build three demonstrations and one query with one fixed hidden rule."""
    _validate_seed(seed)
    if bridge is None:
        with RacketBridge() as runtime:
            return generate_episode(seed, scope=scope, bridge=runtime)
    chosen_scope = choose_scope(seed) if scope is None else _validate_scope(scope)

    selected, source_path, source_hash = load_selected_generator(TASK_ID, root=ROOT)
    program = materialize_program(chosen_scope)
    inputs = []
    input_rng = random.Random(f"{TASK_ID}:inputs:{seed}")
    schedule = ((1, 0, "swapped"), (0, 2, "base"), (1, 1, "swapped"), (2, 1, "base"))
    draws = []
    for index, (row_count, column_count, palette) in enumerate(schedule):
        overrides = {
            "grid_h": input_rng.randint(6, 13),
            "grid_w": input_rng.randint(8, 12),
            "n_anchored_rows": row_count,
            "n_anchored_cols": column_count,
            "lane_palette": palette,
        }
        grid = selected.generate(seed, index, difficulty="hard", **overrides)
        errors = selected.self_check(grid)
        if errors:
            raise ValueError(f"selected generator produced an unlawful input: {errors}")
        inputs.append(grid)
        draws.append({"sample_index": index, "difficulty": "hard", "overrides": overrides})

    outputs = [execute_program(program, grid, bridge) for grid in inputs]
    public = {
        "train": [{"input": grid, "output": output} for grid, output in zip(inputs[:3], outputs[:3])],
        "test": [{"input": inputs[3]}],
    }
    identifiability = audit_demonstrations(public["train"], bridge)
    if identifiability["survivors"] != [chosen_scope]:
        raise ValueError(f"demonstrations do not identify the episode setting: {identifiability}")
    return {
        "public": public,
        "private": {
            "schema": "task-local-parametric-episode-v1",
            "status": "prototype",
            "task_id": TASK_ID,
            "seed": seed,
            "parameters": {"direction_scope": chosen_scope},
            "parameter_selection": "deterministic_seed" if scope is None else "explicit_authoring_override",
            "program": program,
            "program_sha256": _sha256(program.encode()),
            "query_outputs": outputs[3:],
            "selected_generator": {"path": source_path.relative_to(ROOT).as_posix(), "sha256": source_hash},
            "input_draws": draws,
            "identifiability": identifiability,
        },
    }


def _canonical_program():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        rows = [row for line in handle if line.strip() if (row := json.loads(line)).get("task_id") == TASK_ID]
    if len(rows) != 1:
        raise ValueError(f"expected exactly one canonical row for {TASK_ID}, got {len(rows)}")
    return rows[0]["program_solution"]


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_evidence(out, seeds):
    """Retain complete episodes, a shared-input witness, and bounded checks."""
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    selected, source_path, source_hash = load_selected_generator(TASK_ID, root=ROOT)
    canonical_program = _canonical_program()
    canonical_checks, generated_checks, episodes = [], [], []
    source_files = [Path(__file__), Path(__file__).with_name("README.md"), Path(__file__).parents[2] / "tests/test_parametric_prototype.py"]
    source_identity = {path.relative_to(ROOT).as_posix(): _sha256(path.read_bytes()) for path in source_files}
    with RacketBridge() as bridge:
        runtime = bridge.runtime_identity
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            observed = execute_program(materialize_program(), pair["input"], bridge)
            original = execute_program(canonical_program, pair["input"], bridge)
            if observed != pair["output"] or original != pair["output"]:
                raise AssertionError("default setting or canonical program disagrees with canonical labels")
            canonical_checks.append({"variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"], "matched": True})
        for seed in (0, 1, 17, 113):
            for difficulty in ("easy", "medium", "hard"):
                grid = selected.generate(seed, 0, difficulty=difficulty)
                if selected.self_check(grid):
                    raise AssertionError("canonical generator self-check failed")
                observed = execute_program(materialize_program(), grid, bridge)
                original = execute_program(canonical_program, grid, bridge)
                if observed != original:
                    raise AssertionError("default setting differs from canonical program on generated input")
                generated_checks.append({"seed": seed, "sample_index": 0, "difficulty": difficulty, "matched": True})

        witness_input = None
        episode_specs = [(seed, scope) for seed in seeds for scope in SCOPES]
        # These bounded seeds exercise the ordinary seed-selected path for all
        # three settings. They differ from the default controlled-comparison
        # seeds, so each retained public challenge has distinct content.
        episode_specs += [(seed, None) for seed in (11, 2, 16)]
        for seed, scope in episode_specs:
            episode = generate_episode(seed, scope=scope, bridge=bridge)
            private = episode["private"]
            if private["selected_generator"]["sha256"] != source_hash:
                raise RuntimeError("selected generator changed during evidence run; rerun with stable source")
            public = episode["public"]
            # The identifier derives exclusively from already-public data.
            episode_id = _sha256(json.dumps(public, sort_keys=True).encode())[:16]
            public_path = f"public/challenge-{episode_id}.json"
            # Preserve each private provenance record even if a user explicitly
            # requests one of the additional seeded examples as a comparison.
            private_id = _sha256(json.dumps(private, sort_keys=True).encode())[:16]
            private_path = f"private/episode-{private_id}.json"
            _write_json(out / public_path, public)
            _write_json(out / private_path, private)
            episodes.append({"seed": seed, "parameters": private["parameters"], "parameter_selection": private["parameter_selection"], "public": public_path, "private": private_path, "surviving_rivals": private["identifiability"]["survivors"]})
            witness_input = witness_input or public["train"][2]["input"]

        witness_outputs = {scope: execute_program(materialize_program(scope), witness_input, bridge) for scope in SCOPES}
        differences = []
        for left, right in itertools.combinations(SCOPES, 2):
            cells = [[r, c] for r, row in enumerate(witness_outputs[left]) for c, value in enumerate(row) if value != witness_outputs[right][r][c]]
            if not cells:
                raise AssertionError(f"witness does not distinguish {left} and {right}")
            differences.append({"left": left, "right": right, "differing_cells": len(cells), "first_cell": cells[0]})
        _write_json(out / "private/witness.json", {"input": witness_input, "outputs": witness_outputs, "pairwise_differences": differences, "selected_generator_self_check": selected.self_check(witness_input)})

    rules = []
    for scope in SCOPES:
        program = materialize_program(scope)
        relative = f"private/rules/direction_scope_{scope}.rkt"
        (out / relative).parent.mkdir(parents=True, exist_ok=True)
        (out / relative).write_text(program, encoding="utf-8")
        rules.append({"parameters": {"direction_scope": scope}, "path": relative, "sha256": _sha256(program.encode())})
    report = {
        "schema": "task-local-parametric-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "original_task_id": "d2acf2cb",
        "parameter": {"name": "direction_scope", "allowed": list(SCOPES), "default": DEFAULT_SCOPE},
        "input_constraints": "Same for every setting: selected generator's lawful 6..13 by 8..12 grids, paired interior-lane anchors, 0/6 field, 7/8 restricted to anchored lanes. Demonstration schedule includes each orientation and a mixed example.",
        "selected_generator": {"path": source_path.relative_to(ROOT).as_posix(), "sha256": source_hash},
        "prototype_sources_sha256": source_identity,
        "canonical_program_sha256": _sha256(canonical_program.encode()),
        "runtime": runtime,
        "command": {"payload_argv": [sys.executable, *sys.argv], "effective_cwd": str(Path.cwd())},
        "canonical_default_checks": canonical_checks,
        "generated_default_checks": generated_checks,
        "episodes": episodes,
        "rules": rules,
        "witness": "private/witness.json",
        "counts": {
            "canonical_pairs_checked": len(canonical_checks),
            "generated_default_comparisons": len(generated_checks),
            "episodes": len(episodes),
            "distinct_public_challenges": len({episode["public"] for episode in episodes}),
            "seed_selected_episodes": sum(episode["parameter_selection"] == "deterministic_seed" for episode in episodes),
            "demonstrations": 3 * len(episodes),
            "queries": len(episodes),
            "finite_rival_demonstration_executions": 9 * len(episodes),
            "ambiguous_episodes": 0,
            "pairwise_witness_distinctions": len(differences),
            "racket_grid_evaluations": 2 * len(canonical_checks) + 2 * len(generated_checks) + 13 * len(episodes) + len(SCOPES),
        },
        "limitations": [
            "Proposed task-local prototype; no production parameter API or approval change.",
            "Finite identifiability covers only union, rows, columns; arbitrary competing programs remain possible.",
            "Evidence covers the retained seeds and bounded canonical/default comparisons, not all seeds.",
            "Forced demonstration orientations and mixed query are an authoring schedule, not a calibrated production distribution.",
            "The prototype samples the existing smaller envelope; its rule alone is additionally tested on 30x30 input.",
            "Public challenge directory is the only model-visible export; report, rules, witness and private files are controller-side authoring evidence.",
        ],
    }
    _write_json(out / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="new evidence directory")
    parser.add_argument("--seeds", type=int, nargs="+", default=[17, 113])
    args = parser.parse_args(argv)
    if len(set(args.seeds)) != len(args.seeds):
        parser.error("seeds must be unique")
    for seed in args.seeds:
        _validate_seed(seed)
    report = run_evidence(args.out, args.seeds)
    print(json.dumps({"status": report["status"], "report": str(Path(args.out).resolve() / "report.json"), "counts": report["counts"], "selected_generator": report["selected_generator"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
