#!/usr/bin/env python3
"""Proposed target-colour parameter for the cyan-bbox recolouring family.

This is a task-local authoring prototype, not a production generator change.
All labels and parameter-rival predictions are executed by the included Racket
bridge from exact, hash-pinned rule text.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "113d9bb402d3"
VERSION = "proposed-target-colour-v1"
ALLOWED_TARGET_COLOURS = (3, 4)
DEFAULT_TARGET_COLOUR = 3
CANONICAL_RULE_HASH = "3b4315aa79fc"
CANONICAL_SHA256 = "6e7fd13287b51f1d00269aee4d794739d2bba148c8ddf16c6a927ab4eabc580d"
CANONICAL_RECOLOUR_SITE = "(= v 1)) 3 v"
ALTERNATIVE_RECOLOUR_SITE = "(= v 1)) 4 v"


def _sha256(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def grid_sha256(grid):
    return _sha256(_json(normalize_grid(grid)))


def _validate_seed(seed):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1")


def _check_canonical_source(source):
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CANONICAL_RECOLOUR_SITE) != 1:
        raise ValueError("canonical source must contain exactly one recolouring site")
    return source


def canonical_source(*, root=None):
    root = find_root(__file__) if root is None else Path(root)
    sources = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.add(row.get("program_solution"))
    if len(sources) != 1:
        raise ValueError(f"expected exactly one canonical source for {TASK_ID}")
    return _check_canonical_source(sources.pop())


def materialize_rule(target_colour=DEFAULT_TARGET_COLOUR, *, root=None, source=None):
    if type(target_colour) is not int or target_colour not in ALLOWED_TARGET_COLOURS:
        raise ValueError("target_colour must be the integer 3 or 4")
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if target_colour == DEFAULT_TARGET_COLOUR:
        return canonical
    return canonical.replace(
        CANONICAL_RECOLOUR_SITE,
        ALTERNATIVE_RECOLOUR_SITE,
        1,
    )


def rule_callable(source):
    """Convert one pinned `(rule! (lambda ...))` body to an executable lambda."""
    if not isinstance(source, str):
        raise ValueError("Racket source must be text")
    restored = source.replace(
        ALTERNATIVE_RECOLOUR_SITE,
        CANONICAL_RECOLOUR_SITE,
        1,
    )
    _check_canonical_source(restored)
    if not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    # This task's canonical body already is a lambda.  Strip only the outer
    # rule! wrapper; adding another lambda would return a procedure instead of
    # applying the rule to the supplied grid.
    return source[len("(rule! ") : -1]


def execute_rule(source, grid, *, bridge=None):
    grid = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def _paint(height, width, cyan, inside_blue, outside_blue):
    grid = [[0] * width for _ in range(height)]
    for value, cells in ((8, cyan), (1, inside_blue), (1, outside_blue)):
        for row, col in cells:
            if not (0 <= row < height and 0 <= col < width):
                raise ValueError("fixture cell outside grid")
            if grid[row][col] != 0:
                raise ValueError("fixture contains overlapping cells")
            grid[row][col] = value
    return grid


def fixtures():
    """Four authored lawful inputs; constraints do not depend on target colour."""
    return [
        {
            "fixture_id": "interior_sparse_gap",
            "input": _paint(
                11,
                12,
                cyan=[(2, 3), (2, 7), (3, 5), (5, 3), (5, 7)],
                inside_blue=[(2, 4), (3, 3), (3, 6), (4, 5), (5, 6)],
                outside_blue=[(0, 0), (1, 9), (7, 2), (9, 10)],
            ),
        },
        {
            "fixture_id": "top_edge_wide_gap",
            "input": _paint(
                12,
                13,
                cyan=[(0, 2), (0, 8), (2, 4), (3, 2), (3, 8)],
                inside_blue=[(0, 5), (1, 2), (1, 7), (2, 6), (3, 3)],
                outside_blue=[(5, 1), (6, 11), (9, 4), (11, 12)],
            ),
        },
        {
            "fixture_id": "corner_tall_gap",
            "input": _paint(
                13,
                11,
                cyan=[(0, 0), (0, 4), (2, 2), (5, 0), (5, 4)],
                inside_blue=[(0, 1), (1, 4), (2, 0), (3, 3), (5, 2)],
                outside_blue=[(1, 8), (7, 1), (10, 5), (12, 10)],
            ),
        },
        {
            "fixture_id": "interior_dense_irregular",
            "input": _paint(
                14,
                14,
                cyan=[
                    (5, 4), (5, 6), (5, 9), (6, 5), (6, 8),
                    (7, 4), (7, 7), (8, 6), (8, 9),
                ],
                inside_blue=[(5, 5), (6, 4), (6, 7), (7, 6), (7, 8), (8, 4)],
                outside_blue=[(0, 2), (2, 12), (10, 1), (12, 11), (13, 5)],
            ),
        },
    ]


def parameters_for_seed(seed):
    _validate_seed(seed)
    return {"target_colour": random.Random(seed).choice(ALLOWED_TARGET_COLOURS)}


def make_episode(seed, *, root=None, bridge=None):
    _validate_seed(seed)
    parameters = parameters_for_seed(seed)
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(seed, parameters, root=root, bridge=owned)
    return _make_episode(seed, parameters, root=root, bridge=bridge)


def _make_episode(seed, parameters, *, root, bridge):
    canonical = canonical_source(root=root)
    rules = {
        colour: materialize_rule(colour, source=canonical)
        for colour in ALLOWED_TARGET_COLOURS
    }
    inputs = fixtures()
    random.Random(f"{TASK_ID}:fixture-order:{VERSION}:{seed}").shuffle(inputs)
    outputs = {
        colour: [
            execute_rule(source, pair["input"], bridge=bridge)
            for pair in inputs
        ]
        for colour, source in rules.items()
    }
    target = parameters["target_colour"]
    pairs = [
        {
            **pair,
            "output": output,
            "input_sha256": grid_sha256(pair["input"]),
            "output_sha256": grid_sha256(output),
        }
        for pair, output in zip(inputs, outputs[target], strict=True)
    ]
    rival_rows = []
    ambiguities = []
    for rival_target in ALLOWED_TARGET_COLOURS:
        demo_mismatches = [
            index for index in range(3)
            if outputs[rival_target][index] != outputs[target][index]
        ]
        query_mismatches = [
            0
        ] if outputs[rival_target][3] != outputs[target][3] else []
        status = (
            "refuted_by_demonstrations" if demo_mismatches
            else "ambiguous_query" if query_mismatches
            else "matches_episode"
        )
        row = {
            "target_colour": rival_target,
            "racket_sha256": _sha256(rules[rival_target]),
            "status": status,
            "demonstration_mismatch_indices": demo_mismatches,
            "query_mismatch_indices": query_mismatches,
            "train_predictions": outputs[rival_target][:3],
            "query_predictions": outputs[rival_target][3:],
        }
        rival_rows.append(row)
        if status == "ambiguous_query":
            ambiguities.append(row)
    source = rules[target]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": parameters,
        "parameter_selection": "one random.Random(seed).choice((3, 4)) before all pairs",
        "input_constraints_depend_on_parameter": False,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "prototype_sha256": _sha256(Path(__file__).read_bytes()),
        "racket_source": source,
        "racket_sha256": _sha256(source),
        "racket_callable": rule_callable(source),
        "racket_callable_sha256": _sha256(rule_callable(source)),
        "racket_path": f"private/rules/target-colour-{target}.rkt",
        "train": pairs[:3],
        "test": pairs[3:],
        "parameter_rivals": rival_rows,
        "ambiguities": ambiguities,
        "racket_evaluations": 8,
    }


def public_challenge(episode):
    return copy.deepcopy({
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    })


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _files_manifest(out):
    rows = []
    for path in sorted(p for p in out.rglob("*") if p.is_file() and p.name != "report.json"):
        rows.append({
            "path": path.relative_to(out).as_posix(),
            "sha256": _sha256(path.read_bytes()),
            "bytes": path.stat().st_size,
        })
    return rows


def write_evidence(seeds, *, out, root=None):
    seeds = tuple(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("provide at least one distinct episode seed")
    for seed in seeds:
        _validate_seed(seed)
    root = find_root(__file__) if root is None else Path(root).resolve()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    try:
        with RacketBridge() as bridge:
            canonical = canonical_source(root=root)
            canonical_checks = []
            for row in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = execute_rule(canonical, row["input"], bridge=bridge)
                canonical_checks.append({
                    "split": row["split"],
                    "pair_index": row["pair_index"],
                    "matches": actual == row["output"],
                    "input_sha256": grid_sha256(row["input"]),
                    "expected_sha256": grid_sha256(row["output"]),
                    "actual_sha256": grid_sha256(actual),
                })
            if not canonical_checks or not all(row["matches"] for row in canonical_checks):
                raise AssertionError("canonical default failed canonical pair replay")

            episodes = [make_episode(seed, root=root, bridge=bridge) for seed in seeds]
            witness = fixtures()[0]["input"]
            witness_outputs = {
                str(colour): execute_rule(
                    materialize_rule(colour, source=canonical), witness, bridge=bridge
                )
                for colour in ALLOWED_TARGET_COLOURS
            }

        source_snapshot = out / "private" / "source_snapshot"
        source_snapshot.mkdir(parents=True, exist_ok=True)
        (source_snapshot / "prototype.py").write_bytes(Path(__file__).read_bytes())
        test_source = root / "generators" / TASK_ID / "tests" / "test_parametric_variant.py"
        if test_source.is_file():
            (source_snapshot / "test_parametric_variant.py").write_bytes(test_source.read_bytes())

        rule_dir = out / "private" / "rules"
        rule_dir.mkdir(parents=True, exist_ok=True)
        for colour in ALLOWED_TARGET_COLOURS:
            (rule_dir / f"target-colour-{colour}.rkt").write_text(
                materialize_rule(colour, source=canonical), encoding="utf-8"
            )

        rows = []
        for episode in episodes:
            seed = episode["seed"]
            private_path = Path("private") / f"episode-{seed:03d}.json"
            public_path = Path("public") / f"episode-{seed:03d}.json"
            _write_json(out / private_path, episode)
            _write_json(out / public_path, public_challenge(episode))
            rows.append({
                "seed": seed,
                "target_colour": episode["parameters"]["target_colour"],
                "private_path": private_path.as_posix(),
                "public_path": public_path.as_posix(),
                "racket_sha256": episode["racket_sha256"],
                "ambiguities": len(episode["ambiguities"]),
            })

        _write_json(out / "private" / "canonical_replay.json", canonical_checks)
        _write_json(out / "private" / "distinguishing_witness.json", {
            "input": witness,
            "outputs_by_target_colour": witness_outputs,
            "different": len({_json(value) for value in witness_outputs.values()}) == 2,
        })
        report = {
            "schema": "arcpuzzles-proposed-parametric-evidence-v1",
            "task_id": TASK_ID,
            "prototype_version": VERSION,
            "status": "proposed_unapproved",
            "approved": False,
            "parameter": {
                "name": "target_colour",
                "allowed_values": list(ALLOWED_TARGET_COLOURS),
                "original_default": DEFAULT_TARGET_COLOUR,
                "selected_once_per_episode": True,
                "input_constraints_depend_on_parameter": False,
            },
            "canonical_rule_hash": CANONICAL_RULE_HASH,
            "canonical_source_sha256": CANONICAL_SHA256,
            "prototype_sha256": _sha256(Path(__file__).read_bytes()),
            "episodes": rows,
            "counts": {
                "episodes": len(episodes),
                "demonstrations": 3 * len(episodes),
                "queries": len(episodes),
                "settings_covered": len({row["target_colour"] for row in rows}),
                "canonical_pairs_checked": len(canonical_checks),
                "ambiguous_parameter_rivals": sum(row["ambiguities"] for row in rows),
                "racket_rule_applications": 8 * len(episodes) + len(canonical_checks) + 2,
            },
            "limits": [
                "finite evidence for the declared two target colours and retained seeds",
                "four authored fixture inputs are not a replacement production distribution",
                "declared parameter rivals do not prove universal rule identifiability",
                "prototype status does not change canonical approval or production APIs",
            ],
        }
        report["files"] = _files_manifest(out)
        _write_json(out / "report.json", report)
        return report
    except Exception as exc:
        _write_json(out / "failure.json", {
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "seeds": list(seeds),
        })
        raise


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(args.seeds, out=args.out)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
