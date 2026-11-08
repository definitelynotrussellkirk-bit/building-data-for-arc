#!/usr/bin/env python3
"""Proposed cross-shape parameter for the extrema-frame family.

The selected production generator and canonical rule remain unchanged.  This
separate authoring prototype chooses one cross mode per episode and derives all
labels by executing an exact, hash-pinned Racket program with the packet bridge.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import random
import sys
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    normalize_grid,
)


TASK_ID = "0a9926d504f3"
VERSION = "proposed-cross-mode-v1"
ALLOWED_CROSS_MODES = ("plus", "horizontal")
DEFAULT_CROSS_MODE = "plus"
CANONICAL_RULE_HASH = "b54594bcf310"
CANONICAL_SHA256 = "7bf1b4a25c111974b44ecbad6a6e5257f98fad03190691c9f04d92ed2874816c"

# This is the unique vertical arm clause in the pinned canonical source.  The
# alternative keeps frame inference, edge precedence, the center, and the
# horizontal arm, while making the vertical interior background.
CANONICAL_VERTICAL_CLAUSE = "((and (= c cc) (> r top-r) (< r bot-r)) 5)"
HORIZONTAL_VERTICAL_CLAUSE = "((and (= c cc) (> r top-r) (< r bot-r)) 0)"

FIXTURE_SPECS = (
    {
        "fixture_id": "shared_corner_15x15",
        "seed": 4201,
        "sample_index": 0,
        "difficulty": "medium",
        "overrides": {"grid_h": 15, "grid_w": 15, "texture": "shared_corner"},
    },
    {
        "fixture_id": "center_edge_15x14",
        "seed": 4202,
        "sample_index": 1,
        "difficulty": "medium",
        "overrides": {"grid_h": 15, "grid_w": 14, "texture": "center_edge"},
    },
    {
        "fixture_id": "extra_marker_16x15",
        "seed": 4203,
        "sample_index": 2,
        "difficulty": "hard",
        "overrides": {"grid_h": 16, "grid_w": 15, "texture": "extra_marker"},
    },
    {
        "fixture_id": "plain_14x15",
        "seed": 4204,
        "sample_index": 3,
        "difficulty": "easy",
        "overrides": {"grid_h": 14, "grid_w": 15, "texture": "plain"},
    },
)


def _sha256(value: str | bytes) -> str:
    data = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(data).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def grid_sha256(grid: Any) -> str:
    normalized = normalize_grid(grid)
    if normalized is None:
        raise ValueError("grid must be a rectangular ARC integer grid")
    return _sha256(_json(normalized))


def _validate_seed(seed: Any) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1")


def _check_canonical_source(source: Any) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CANONICAL_VERTICAL_CLAUSE) != 1:
        raise ValueError("canonical source must contain one vertical cross clause")
    if HORIZONTAL_VERTICAL_CLAUSE in source:
        raise ValueError("canonical source unexpectedly contains the alternative clause")
    return source


def canonical_source(*, root: Path | str | None = None) -> str:
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if isinstance(source, str):
                    sources.add(source)
    if len(sources) != 1:
        raise ValueError(f"expected exactly one canonical source for {TASK_ID}")
    return _check_canonical_source(sources.pop())


def materialize_rule(
    cross_mode: str = DEFAULT_CROSS_MODE,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    if type(cross_mode) is not str or cross_mode not in ALLOWED_CROSS_MODES:
        raise ValueError("cross_mode must be exactly 'plus' or 'horizontal'")
    canonical = (
        canonical_source(root=root)
        if source is None
        else _check_canonical_source(source)
    )
    if cross_mode == DEFAULT_CROSS_MODE:
        return canonical
    alternative = canonical.replace(
        CANONICAL_VERTICAL_CLAUSE,
        HORIZONTAL_VERTICAL_CLAUSE,
        1,
    )
    if alternative.count(HORIZONTAL_VERTICAL_CLAUSE) != 1:
        raise AssertionError("failed to materialize horizontal-only rule")
    return alternative


def _restore_canonical(source: Any) -> str:
    if not isinstance(source, str):
        raise ValueError("Racket source must be text")
    canonical_count = source.count(CANONICAL_VERTICAL_CLAUSE)
    alternative_count = source.count(HORIZONTAL_VERTICAL_CLAUSE)
    if (canonical_count, alternative_count) == (1, 0):
        restored = source
    elif (canonical_count, alternative_count) == (0, 1):
        restored = source.replace(
            HORIZONTAL_VERTICAL_CLAUSE,
            CANONICAL_VERTICAL_CLAUSE,
            1,
        )
    else:
        raise ValueError("Racket source must contain one declared vertical clause")
    return _check_canonical_source(restored)


def rule_callable(source: str) -> str:
    """Strip only the outer ``rule!`` wrapper from one declared rule."""
    _restore_canonical(source)
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    body = source[len("(rule!") : -1].strip()
    marker = "(lambda (g)"
    if body.count(marker) != 1:
        raise ValueError("expected exactly one wrapped grid lambda")
    lambda_body = body[body.index(marker) :]
    # Match the executor's legacy rule! convention used by retained prototypes.
    return (
        "(lambda (g) "
        "(let* ((h (rows g)) (w (cols g))) "
        f"({lambda_body} g)))"
    )


def execute_rule(source: str, grid: Any, *, bridge: RacketBridge | None = None):
    normalized = normalize_grid(grid)
    if normalized is None:
        raise ValueError("grid must be a rectangular ARC integer grid")
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def _load_fixture_generator(root: Path):
    """Load the selected bytes without replacing cached portable dependencies.

    Portable task tests intentionally expose both execution-layout and
    repository-layout mirrors.  The frozen fixture may import the latter's
    ``puzzle_generators`` first, so asking ``load_selected_generator`` to switch
    dependency trees in the same pytest process is correctly rejected.  The
    task runner already supplies ``GENERATOR_UNDER_TEST`` for its selected
    source; ordinary authoring runs use this task's explicit source under root.
    Both paths remain inside the source-bound tree and are hashed before exec.
    """
    selected = os.environ.get("GENERATOR_UNDER_TEST")
    source = (
        Path(selected).resolve()
        if selected
        else (root / "generators" / TASK_ID / "generator.py").resolve()
    )
    if source.is_symlink() or not source.is_relative_to(root) or not source.is_file():
        raise ValueError(f"selected generator must stay inside {root}: {source}")
    body = source.read_bytes()
    digest = _sha256(body)
    name = f"_parametric_fixture_{TASK_ID}_{digest}"
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load selected generator at {source}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    try:
        sys.modules[name] = module
        exec(compile(body, str(source), "exec"), module.__dict__)
    except BaseException:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise
    return module, source, digest


def fixtures(*, root: Path | str | None = None) -> list[dict[str, Any]]:
    """Return four deterministic lawful inputs independent of cross mode."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    generator, generator_path, generator_sha256 = _load_fixture_generator(root)
    rows: list[dict[str, Any]] = []
    for spec in FIXTURE_SPECS:
        overrides = copy.deepcopy(spec["overrides"])
        grid = generator.generate(
            spec["seed"],
            spec["sample_index"],
            difficulty=spec["difficulty"],
            **overrides,
        )
        errors = generator.self_check(grid)
        if errors:
            raise AssertionError(
                f"fixture {spec['fixture_id']} is outside the task grammar: {errors}"
            )
        observed = generator.observe_overrides(grid)
        if observed != overrides:
            raise AssertionError(
                f"fixture {spec['fixture_id']} override mismatch: "
                f"observed={observed}, expected={overrides}"
            )
        rows.append({
            "fixture_id": spec["fixture_id"],
            "generation": {
                "seed": spec["seed"],
                "sample_index": spec["sample_index"],
                "difficulty": spec["difficulty"],
                "overrides": overrides,
                "generator_path": Path(generator_path).relative_to(root).as_posix(),
                "generator_sha256": generator_sha256,
            },
            "input": normalize_grid(grid),
            "input_sha256": grid_sha256(grid),
        })
    return rows


def parameters_for_seed(seed: Any) -> dict[str, str]:
    _validate_seed(seed)
    return {"cross_mode": random.Random(seed).choice(ALLOWED_CROSS_MODES)}


def make_episode(
    seed: int,
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    _validate_seed(seed)
    parameters = parameters_for_seed(seed)
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(seed, parameters, root=root, bridge=owned)
    return _make_episode(seed, parameters, root=root, bridge=bridge)


def _make_episode(seed, parameters, *, root, bridge):
    root = find_root(__file__) if root is None else Path(root).resolve()
    canonical = canonical_source(root=root)
    rules = {
        mode: materialize_rule(mode, source=canonical)
        for mode in ALLOWED_CROSS_MODES
    }
    inputs = fixtures(root=root)
    random.Random(f"{TASK_ID}:fixture-order:{VERSION}:{seed}").shuffle(inputs)
    outputs = {
        mode: [
            execute_rule(source, fixture["input"], bridge=bridge)
            for fixture in inputs
        ]
        for mode, source in rules.items()
    }
    for index, fixture in enumerate(inputs):
        if outputs["plus"][index] == outputs["horizontal"][index]:
            raise AssertionError(
                f"fixture {fixture['fixture_id']} does not distinguish cross modes"
            )

    cross_mode = parameters["cross_mode"]
    pairs = [
        {
            **copy.deepcopy(fixture),
            "cross_mode": cross_mode,
            "output": output,
            "output_sha256": grid_sha256(output),
        }
        for fixture, output in zip(inputs, outputs[cross_mode], strict=True)
    ]

    rival_rows = []
    ambiguities = []
    for rival_mode in ALLOWED_CROSS_MODES:
        demo_mismatches = [
            index
            for index in range(3)
            if outputs[rival_mode][index] != outputs[cross_mode][index]
        ]
        query_mismatches = (
            [0] if outputs[rival_mode][3] != outputs[cross_mode][3] else []
        )
        status = (
            "refuted_by_demonstrations"
            if demo_mismatches
            else "ambiguous_query"
            if query_mismatches
            else "matches_episode"
        )
        row = {
            "cross_mode": rival_mode,
            "racket_sha256": _sha256(rules[rival_mode]),
            "status": status,
            "demonstration_mismatch_indices": demo_mismatches,
            "query_mismatch_indices": query_mismatches,
            "train_predictions": outputs[rival_mode][:3],
            "query_predictions": outputs[rival_mode][3:],
        }
        rival_rows.append(row)
        if status == "ambiguous_query":
            ambiguities.append(row)

    source = rules[cross_mode]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": parameters,
        "parameter_selection": (
            "one random.Random(seed).choice(('plus', 'horizontal')) before all pairs"
        ),
        "input_constraints_depend_on_parameter": False,
        "invariant_reasoning": [
            "identify the unique color-2 center and all other nonzero markers",
            "select unique row/column extrema and carry their colors to a frame",
            "apply top > bottom > left > right edge precedence",
            "preserve the center and horizontal color-5 arm in both modes",
        ],
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "prototype_sha256": _sha256(Path(__file__).read_bytes()),
        "racket_source": source,
        "racket_sha256": _sha256(source),
        "racket_callable": rule_callable(source),
        "racket_callable_sha256": _sha256(rule_callable(source)),
        "racket_path": f"private/rules/cross-mode-{cross_mode}.rkt",
        "train": pairs[:3],
        "test": pairs[3:],
        "parameter_rivals": rival_rows,
        "ambiguities": ambiguities,
        "racket_evaluations": 8,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy({
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    })


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _files_manifest(out: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(
        path
        for path in out.rglob("*")
        if path.is_file() and path.name != "report.json"
    ):
        rows.append({
            "path": path.relative_to(out).as_posix(),
            "sha256": _sha256(path.read_bytes()),
            "bytes": path.stat().st_size,
        })
    return rows


def write_evidence(
    seeds,
    *,
    out: Path | str,
    root: Path | str | None = None,
) -> dict[str, Any]:
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
            runtime_identity = bridge.runtime_identity
            canonical = canonical_source(root=root)
            canonical_checks = []
            for row in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = execute_rule(canonical, row["input"], bridge=bridge)
                canonical_checks.append({
                    "variant": row["variant"],
                    "split": row["split"],
                    "pair_index": row["pair_index"],
                    "matches": actual == row["output"],
                    "input_sha256": grid_sha256(row["input"]),
                    "expected_sha256": grid_sha256(row["output"]),
                    "actual_sha256": grid_sha256(actual),
                })
            if not canonical_checks or not all(
                row["matches"] for row in canonical_checks
            ):
                raise AssertionError("canonical default failed canonical pair replay")

            episodes = [
                make_episode(seed, root=root, bridge=bridge) for seed in seeds
            ]
            covered = {
                episode["parameters"]["cross_mode"] for episode in episodes
            }
            if covered != set(ALLOWED_CROSS_MODES):
                raise ValueError(
                    "evidence seeds must cover both cross_mode settings; "
                    f"covered={sorted(covered)}"
                )

            witness = fixtures(root=root)[0]["input"]
            witness_outputs = {
                mode: execute_rule(
                    materialize_rule(mode, source=canonical),
                    witness,
                    bridge=bridge,
                )
                for mode in ALLOWED_CROSS_MODES
            }
            if witness_outputs["plus"] == witness_outputs["horizontal"]:
                raise AssertionError("retained witness does not distinguish cross modes")

        source_snapshot = out / "private" / "source_snapshot"
        source_snapshot.mkdir(parents=True, exist_ok=True)
        (source_snapshot / "prototype.py").write_bytes(Path(__file__).read_bytes())
        test_source = (
            root
            / "generators"
            / TASK_ID
            / "tests"
            / "test_parametric_cross_mode.py"
        )
        if test_source.is_file():
            (source_snapshot / test_source.name).write_bytes(test_source.read_bytes())

        rule_dir = out / "private" / "rules"
        rule_dir.mkdir(parents=True, exist_ok=True)
        for mode in ALLOWED_CROSS_MODES:
            (rule_dir / f"cross-mode-{mode}.rkt").write_text(
                materialize_rule(mode, source=canonical),
                encoding="utf-8",
            )

        episode_rows = []
        for episode in episodes:
            seed = episode["seed"]
            private_path = Path("private") / f"episode-{seed:03d}.json"
            public_path = Path("public") / f"episode-{seed:03d}.json"
            _write_json(out / private_path, episode)
            _write_json(out / public_path, public_challenge(episode))
            episode_rows.append({
                "seed": seed,
                "cross_mode": episode["parameters"]["cross_mode"],
                "private_path": private_path.as_posix(),
                "public_path": public_path.as_posix(),
                "racket_sha256": episode["racket_sha256"],
                "ambiguities": len(episode["ambiguities"]),
            })

        _write_json(out / "private" / "canonical_replay.json", canonical_checks)
        _write_json(
            out / "private" / "racket_runtime_identity.json",
            runtime_identity,
        )
        _write_json(out / "private" / "distinguishing_witness.json", {
            "input": witness,
            "input_sha256": grid_sha256(witness),
            "outputs_by_cross_mode": witness_outputs,
            "different": witness_outputs["plus"] != witness_outputs["horizontal"],
        })

        report = {
            "schema": "arcpuzzles-proposed-parametric-evidence-v1",
            "task_id": TASK_ID,
            "prototype_version": VERSION,
            "status": "proposed_unapproved",
            "approved": False,
            "parameter": {
                "name": "cross_mode",
                "allowed_values": list(ALLOWED_CROSS_MODES),
                "original_default": DEFAULT_CROSS_MODE,
                "selected_once_per_episode": True,
                "input_constraints_depend_on_parameter": False,
                "meaning": {
                    "plus": "draw both horizontal and vertical color-5 arms (canonical)",
                    "horizontal": "draw only the horizontal color-5 arm",
                },
            },
            "invariant_reasoning": episodes[0]["invariant_reasoning"],
            "canonical_rule_hash": CANONICAL_RULE_HASH,
            "canonical_source_sha256": CANONICAL_SHA256,
            "prototype_sha256": _sha256(Path(__file__).read_bytes()),
            "test_source_sha256": (
                _sha256(test_source.read_bytes()) if test_source.is_file() else None
            ),
            "episodes": episode_rows,
            "counts": {
                "episodes": len(episodes),
                "demonstrations": 3 * len(episodes),
                "queries": len(episodes),
                "settings_covered": len({row["cross_mode"] for row in episode_rows}),
                "canonical_pairs_checked": len(canonical_checks),
                "ambiguous_parameter_rivals": sum(
                    row["ambiguities"] for row in episode_rows
                ),
                "racket_rule_applications": (
                    8 * len(episodes) + len(canonical_checks) + 2
                ),
            },
            "commands": {
                "evidence": (
                    "python3 review.py run python3 "
                    "generators/0a9926d504f3/workspace/parametric/prototype.py "
                    "--seeds 0 1 --out ../checks/parametric/cross-mode-final"
                ),
                "focused_test": (
                    "python3 review.py run python3 -m pytest -q "
                    "generators/0a9926d504f3/tests/test_parametric_cross_mode.py"
                ),
            },
            "limits": [
                "finite evidence for the two declared cross modes and retained seeds",
                "four deterministic generator fixtures are not a production distribution",
                "declared parameter-rival checks do not prove universal identifiability",
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


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(args.seeds, out=args.out)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
