#!/usr/bin/env python3
"""Proposed base-edge rule parameter for the column-to-pyramid family.

This authoring prototype does not change the production generator or its rule
authority. All labels and parameter-rival predictions execute exact Racket.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import random
import sys

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)


TASK_ID = "cde6cd1740f9"
VERSION = "proposed-base-edge-v1"
BASE_EDGES = ("bottom", "top")
DEFAULT_BASE_EDGE = "bottom"
CANONICAL_RULE_HASH = "027335bb451f"
CANONICAL_SHA256 = "1eabf7f4ae2d7acbaa8ba9db677c140a76bfabce59d672ea30d1ba06cbd3fae5"
BOTTOM_ROW = "(row (- (- h 1) i))"
TOP_ROW = "(row i)"


def sha256(value):
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def grid_sha256(grid):
    return sha256(json.dumps(normalize_grid(grid), separators=(",", ":")))


def _check_canonical_source(source):
    if not isinstance(source, str) or sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned program")
    if source.count(BOTTOM_ROW) != 1 or TOP_ROW in source:
        raise ValueError("canonical program must have one unambiguous row-placement site")
    return source


def canonical_source(*, root=None):
    root = find_root(__file__) if root is None else Path(root)
    sources = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    sources.add(row.get("program_solution"))
    if len(sources) != 1:
        raise ValueError(f"expected exactly one canonical program for {TASK_ID}")
    return _check_canonical_source(sources.pop())


def materialize_rule(base_edge=DEFAULT_BASE_EDGE, *, root=None, source=None):
    """Preserve canonical bytes for bottom; alter only the row expression for top."""
    if type(base_edge) is not str or base_edge not in BASE_EDGES:
        raise ValueError("base_edge must be 'bottom' or 'top'")
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    return canonical if base_edge == "bottom" else canonical.replace(BOTTOM_ROW, TOP_ROW, 1)


def execute_rule(source, grid, *, bridge=None):
    """Apply one of this prototype's exact rule programs through RacketBridge."""
    if not isinstance(source, str):
        raise ValueError("canonical or materialized Racket source must be text")
    _check_canonical_source(source.replace(TOP_ROW, BOTTOM_ROW, 1))
    if not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    body = source[len("(rule! ") : -1]
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in normalized) + ")"
    with RacketBridge() if bridge is None else nullcontext(bridge) as live:
        return normalize_grid(live.eval_text(f"({body} {literal})"))


def choose_base_edge(seed):
    """Select one hidden setting for the complete episode without global RNG use."""
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1")
    return random.Random(seed).choice(BASE_EDGES)


def _source_files(root, generator_path):
    paths = {
        "prototype.py": Path(__file__),
        "generator.py": Path(generator_path),
        "test_parametric_cde6cd1740f9.py": Path(root) / "generators" / TASK_ID / "tests/test_parametric_cde6cd1740f9.py",
    }
    readme = Path(__file__).with_name("README.md")
    if readme.is_file():
        paths["README.md"] = readme
    return {name: path.read_bytes() for name, path in paths.items()}


def generate_episode(seed, *, root=None, difficulty="medium", start=0, bridge=None):
    """Return separate public challenge and private authoring evidence objects.

    Input constraints do not depend on base_edge. The selected generator supplies
    all inputs and its current EXAMPLES_NEEDED controls the demonstration count.
    No parameter is drawn inside the pair loop.
    """
    base_edge = choose_base_edge(seed)
    if type(start) is not int or start < 0:
        raise ValueError("start must be a nonnegative integer")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    root = find_root(__file__) if root is None else Path(root)
    generator, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    train_count = generator.EXAMPLES_NEEDED
    if type(train_count) is not int or train_count < 1:
        raise ValueError("selected generator must declare a positive EXAMPLES_NEEDED")
    sources = _source_files(root, generator_path)
    if sha256(sources["generator.py"]) != generator_sha256:
        raise RuntimeError("selected generator changed while binding episode sources")
    canonical = canonical_source(root=root)
    rules = {edge: materialize_rule(edge, source=canonical) for edge in BASE_EDGES}
    inputs, accepted = [], []
    for position, sample_index in enumerate(range(start, start + train_count + 1)):
        grid = normalize_grid(generator.generate(seed, sample_index, difficulty=difficulty))
        errors = generator.self_check(grid)
        if errors:
            raise ValueError(f"unlawful selected-generator input at {sample_index}: {errors}")
        inputs.append(grid)
        accepted.append({
            "split": "train" if position < train_count else "test",
            "pair_position": position if position < train_count else 0,
            "sample_index": sample_index,
            "input_sha256": grid_sha256(grid),
        })
    with RacketBridge() if bridge is None else nullcontext(bridge) as live:
        predictions = {
            edge: [execute_rule(rule, grid, bridge=live) for grid in inputs]
            for edge, rule in rules.items()
        }
    outputs = predictions[base_edge]
    challenge = {
        "train": [{"input": grid, "output": output} for grid, output in zip(inputs[:train_count], outputs[:train_count])],
        "test": [{"input": inputs[-1]}],
    }
    rivals = {}
    for edge in BASE_EDGES:
        disagreements = [i for i in range(train_count) if predictions[edge][i] != outputs[i]]
        query_disagreements = [0] if predictions[edge][-1] != outputs[-1] else []
        rivals[edge] = {
            "status": "selected" if edge == base_edge else (
                "eliminated_by_demonstrations" if disagreements else (
                    "ambiguous_query" if query_disagreements else "survived_all"
                )
            ),
            "demo_disagreements": disagreements,
            "query_disagreements": query_disagreements,
            "rule_sha256": sha256(rules[edge]),
            "train_predictions": predictions[edge][:train_count],
            "query_predictions": predictions[edge][train_count:],
        }
    identifiable = all(rivals[edge]["demo_disagreements"] for edge in BASE_EDGES if edge != base_edge)
    private = {
        "schema": "cde6cd1740f9-base-edge-episode-v1",
        "status": "proposed_prototype",
        "task_id": TASK_ID,
        "version": VERSION,
        "seed": seed,
        "parameters": {"base_edge": base_edge},
        "sampling": {"difficulty": difficulty, "start": start, "train_count": train_count,
                     "query_count": 1, "accepted_pairs": accepted},
        "bindings": {"generator_sha256": generator_sha256,
                     "prototype_sha256": sha256(sources["prototype.py"]),
                     "test_sha256": sha256(sources["test_parametric_cde6cd1740f9.py"]),
                     "canonical_program_sha256": CANONICAL_SHA256,
                     "canonical_rule_hash": CANONICAL_RULE_HASH},
        "reference_rule": {"racket": rules[base_edge], "sha256": sha256(rules[base_edge])},
        "query_answers": [{"output": outputs[-1]}],
        "parameter_rivals": rivals,
        "identifiable_against_parameter_rivals": identifiable,
    }
    return {"challenge": challenge, "private": private}


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def retain_evidence(seeds, out, *, difficulty="medium", start=0):
    """Execute bounded replay, witness and complete episodes; save exact evidence."""
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError("out must be new or empty, so retained runs cannot mix")
    root = find_root(__file__)
    generator, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    sources = _source_files(root, generator_path)
    if sha256(sources["generator.py"]) != generator_sha256:
        raise RuntimeError("selected generator changed while binding evidence sources")
    rules = {edge: materialize_rule(edge, root=root) for edge in BASE_EDGES}
    private_dir = out / "private"
    for name, body in sources.items():
        path = private_dir / "source_snapshot" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    for edge, rule in rules.items():
        path = private_dir / "rules" / f"base-{edge}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rule, encoding="utf-8")

    with RacketBridge() as bridge:
        replay_rows = []
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute_rule(rules["bottom"], pair["input"], bridge=bridge)
            replay_rows.append({**pair, "actual_output": actual, "matches": actual == pair["output"]})
        replay = {"pairs": len(replay_rows), "failed": sum(not row["matches"] for row in replay_rows),
                  "unique_labelled_pairs": len({json.dumps([row["input"], row["output"]]) for row in replay_rows}),
                  "rule_sha256": sha256(rules["bottom"]), "results": replay_rows}
        _write_json(private_dir / "canonical_replay.json", replay)

        episodes = []
        for index, seed in enumerate(seeds):
            episode = generate_episode(seed, root=root, difficulty=difficulty, start=start, bridge=bridge)
            if episode["private"]["bindings"]["generator_sha256"] != generator_sha256:
                raise RuntimeError("selected generator changed during evidence run")
            public_path = out / "public" / f"episode-{index:03d}.json"
            private_path = private_dir / f"episode-{index:03d}.json"
            _write_json(public_path, episode["challenge"])
            private = episode["private"]
            private["public_file"] = public_path.relative_to(out).as_posix()
            private["public_file_sha256"] = sha256(public_path.read_bytes())
            _write_json(private_path, private)
            episodes.append({"seed": seed, "base_edge": private["parameters"]["base_edge"],
                             "public_file": public_path.relative_to(out).as_posix(),
                             "private_file": private_path.relative_to(out).as_posix(),
                             "train_count": private["sampling"]["train_count"],
                             "identifiable_against_parameter_rivals": private["identifiable_against_parameter_rivals"]})

        witness_input = normalize_grid(generator.generate(seeds[0], start, difficulty=difficulty))
        witness_outputs = {edge: execute_rule(rule, witness_input, bridge=bridge) for edge, rule in rules.items()}
        witness = {"seed": seeds[0], "sample_index": start, "difficulty": difficulty,
                   "input": witness_input, "input_constraint_errors": generator.self_check(witness_input),
                   "outputs": witness_outputs,
                   "outputs_differ": witness_outputs["bottom"] != witness_outputs["top"]}
        _write_json(private_dir / "distinguishing_witness.json", witness)
        runtime_identity = bridge.runtime_identity

    passed = (bool(replay_rows) and replay["failed"] == 0 and witness["outputs_differ"]
              and not witness["input_constraint_errors"]
              and all(episode["identifiable_against_parameter_rivals"] for episode in episodes))
    report = {
        "schema": "cde6cd1740f9-base-edge-evidence-v1",
        "status": "bounded_checks_passed" if passed else "bounded_checks_failed",
        "admission": "proposed prototype; no production approval",
        "parameter": {"name": "base_edge", "allowed": list(BASE_EDGES), "default": DEFAULT_BASE_EDGE},
        "settings_observed": sorted({episode["base_edge"] for episode in episodes}),
        "commands": {"payload_argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd())},
        "source_files": {name: sha256(body) for name, body in sources.items()},
        "generator_sha256": generator_sha256,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "rules": {edge: {"path": f"private/rules/base-{edge}.rkt", "sha256": sha256(rule)} for edge, rule in rules.items()},
        "canonical_replay": {key: value for key, value in replay.items() if key != "results"},
        "distinguishing_witness": {"path": "private/distinguishing_witness.json", "outputs_differ": witness["outputs_differ"]},
        "episodes": episodes,
        "runtime_identity": runtime_identity,
        "limitations": [
            "Only the requested seeds, band and start were executed; random support is not exhausted.",
            "Identifiability is tested against the declared bottom/top parameter rival, not every possible ARC rule.",
            "Inputs retain the canonical generator constraints for both settings, including source-row sampling asymmetry.",
            "Canonical repairs and any production admission remain separate from this authoring prototype.",
        ],
    }
    _write_json(private_dir / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        for seed in args.seeds:
            choose_base_edge(seed)
        if args.start < 0:
            raise ValueError("start must be nonnegative")
        report = retain_evidence(args.seeds, args.out, difficulty=args.difficulty, start=args.start)
    except (ValueError, RuntimeError) as exc:
        parser.exit(2, f"prototype error: {exc}\n")
    print(json.dumps({"status": report["status"], "episodes": len(report["episodes"]),
                      "settings_observed": report["settings_observed"],
                      "canonical_pairs": report["canonical_replay"]["pairs"],
                      "report": str(args.out / "private/report.json")}, sort_keys=True))
    return 0 if report["status"] == "bounded_checks_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
