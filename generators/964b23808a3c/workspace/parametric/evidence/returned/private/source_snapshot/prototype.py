#!/usr/bin/env python3
"""Proposed episode-level segment-owner parameter for task 964b23808a3c.

The production generator and canonical Racket authority stay fixed.  This
unapproved task-local authoring prototype chooses one segment ownership rule for
an entire episode:

``lower`` (canonical)
    The lower/current marker owns the gap above it.  This is the byte-exact
    canonical Racket program.

``upper`` (alternative)
    The upper/previous marker owns the gap below it.  Marker cells retain their
    own colors, the last-nonzero-is-5 selector is unchanged, and rows below a
    floating terminator remain unchanged.

The CLI materializes complete public/private episodes and obtains every retained
label by executing the bundled Racket runtime through ``RacketBridge``.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)


TASK_ID = "964b23808a3c"
PROTOTYPE_VERSION = "proposed-segment-owner-v1"
STATUS = "proposed_unapproved"
ALLOWED_SEGMENT_OWNERS = ("lower", "upper")
DEFAULT_SEGMENT_OWNER = "lower"
CANONICAL_RULE_HASH = "c7e69da25375"
CANONICAL_SOURCE_SHA256 = (
    "2c8f8aa67ae8104f49348542b8fc365527f316c292c87dd8a6c08a0dfd9cc1a0"
)

_UPPER_RULE = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (reduce (lambda (acc c)
                     (let* ((marks (filter (lambda (r) (!= (at g r c) 0)) (range 0 h))))
                       (if (or
                             (empty? marks)
                             (!= (at g (nth marks (- (length marks) 1)) c) 5))
                           acc
                           (reduce (lambda (a i)
                                     (let* ((r (nth marks i))
                                            (previous-row (if (zero? i)
                                                              -1
                                                              (nth marks (- i 1))))
                                            (start (+ previous-row 1))
                                            (end (if (zero? i) (+ r 1) r))
                                            (color (if (zero? i)
                                                       (at g r c)
                                                       (at g previous-row c))))
                                       (reduce (lambda (aa rr) (set-cell aa rr c color))
                                               a
                                               (range start end))))
                                   acc
                                   (range 0 (length marks))))))
                   g
                   (range 0 w)))))"""


def _sha256(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def grid_sha256(grid) -> str:
    return _sha256(_json_bytes(normalize_grid(grid)))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be a literal nonnegative integer")
    if seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    return seed


def _validate_owner(segment_owner: Any) -> str:
    if not isinstance(segment_owner, str) or segment_owner not in ALLOWED_SEGMENT_OWNERS:
        raise ValueError(
            "segment_owner must be one of: " + ", ".join(ALLOWED_SEGMENT_OWNERS)
        )
    return segment_owner


def _check_canonical_source(source: Any) -> str:
    if not isinstance(source, str):
        raise TypeError("canonical Racket source must be text")
    actual = _sha256(source)
    if actual != CANONICAL_SOURCE_SHA256:
        raise ValueError(
            "canonical Racket source SHA256 drift: "
            f"expected {CANONICAL_SOURCE_SHA256}, got {actual}"
        )
    if not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    return source


def canonical_source(*, root: Path | str | None = None) -> str:
    root_path = find_root(__file__) if root is None else Path(root)
    sources = {
        row.get("program_solution")
        for row in (
            json.loads(line)
            for line in canonical_path(root_path).read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        if row.get("task_id") == TASK_ID
    }
    if len(sources) != 1:
        raise ValueError(f"expected exactly one canonical source for {TASK_ID}")
    return _check_canonical_source(sources.pop())


def materialize_rule(
    segment_owner: str = DEFAULT_SEGMENT_OWNER,
    *,
    root: Path | str | None = None,
) -> str:
    owner = _validate_owner(segment_owner)
    if owner == DEFAULT_SEGMENT_OWNER:
        return canonical_source(root=root)
    if not _UPPER_RULE.startswith("(rule! ") or not _UPPER_RULE.endswith(")"):
        raise AssertionError("alternative Racket source has an invalid wrapper")
    return _UPPER_RULE


def _rule_callable(source: str) -> str:
    if not isinstance(source, str) or not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("Racket source must be a (rule! ...) form")
    return source[len("(rule! ") : -1]


def execute_rule(source: str, grid, *, bridge: RacketBridge | None = None):
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    expression = f"({_rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def apply_python(grid, segment_owner: str = DEFAULT_SEGMENT_OWNER):
    """Independent mirror of the two proposed settings; never label authority."""
    owner = _validate_owner(segment_owner)
    source = normalize_grid(grid)
    if not source or not source[0]:
        raise ValueError("grid must be nonempty")
    width = len(source[0])
    if any(len(row) != width for row in source):
        raise ValueError("grid must be rectangular")
    out = copy.deepcopy(source)
    height = len(source)
    for column in range(width):
        marks = [
            (row, source[row][column])
            for row in range(height)
            if source[row][column] != 0
        ]
        if not marks or marks[-1][1] != 5:
            continue
        if owner == "lower":
            previous_row = -1
            for row, color in marks:
                for fill_row in range(previous_row + 1, row + 1):
                    out[fill_row][column] = color
                previous_row = row
        else:
            first_row, first_color = marks[0]
            for fill_row in range(0, first_row + 1):
                out[fill_row][column] = first_color
            for index in range(1, len(marks)):
                previous_row, previous_color = marks[index - 1]
                current_row, _current_color = marks[index]
                for fill_row in range(previous_row + 1, current_row):
                    out[fill_row][column] = previous_color
    return out


def parameters_for_seed(seed: int) -> dict[str, str]:
    seed = _validate_seed(seed)
    return {"segment_owner": ALLOWED_SEGMENT_OWNERS[seed % len(ALLOWED_SEGMENT_OWNERS)]}


def _episode_inputs(seed: int, *, root: Path) -> tuple[list[dict[str, Any]], str, str]:
    module, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root
    )
    bands = ("easy", "medium", "hard", "medium")
    rows: list[dict[str, Any]] = []
    for slot, band in enumerate(bands):
        generator_seed = 20_261_021 + seed * 10_000 + slot * 137
        sample_index = slot
        grid = module.generate(generator_seed, sample_index, difficulty=band)
        errors = module.self_check(grid)
        if errors:
            raise AssertionError(
                f"selected generator rejected prototype slot {slot}: {errors}"
            )
        lower = apply_python(grid, "lower")
        upper = apply_python(grid, "upper")
        if lower == upper:
            raise AssertionError(
                f"prototype slot {slot} does not distinguish segment ownership"
            )
        rows.append(
            {
                "fixture_id": f"profile-{slot}-{module.schedule_profile(generator_seed, sample_index, band)}",
                "input": grid,
                "input_sha256": grid_sha256(grid),
                "sampling": {
                    "generator_seed": generator_seed,
                    "sample_index": sample_index,
                    "difficulty": band,
                    "schedule_profile": module.schedule_profile(
                        generator_seed, sample_index, band
                    ),
                },
            }
        )
    return rows, str(generator_path), generator_sha256


def build_episode(seed: int, *, root: Path | str | None = None) -> dict[str, Any]:
    """Build a Python-mirror blueprint; retained evidence is re-labeled in Racket."""
    seed = _validate_seed(seed)
    root_path = find_root(__file__) if root is None else Path(root)
    owner = parameters_for_seed(seed)["segment_owner"]
    rival = next(value for value in ALLOWED_SEGMENT_OWNERS if value != owner)
    program = materialize_rule(owner, root=root_path)
    rows, generator_path, generator_sha256 = _episode_inputs(seed, root=root_path)
    pairs = [
        {
            **copy.deepcopy(row),
            "output": apply_python(row["input"], owner),
            "output_sha256": grid_sha256(apply_python(row["input"], owner)),
        }
        for row in rows
    ]
    train = pairs[:3]
    test = pairs[3:]
    rival_record = {
        "segment_owner": rival,
        "demonstration_mismatch_indices": [
            index
            for index, pair in enumerate(train)
            if apply_python(pair["input"], rival) != pair["output"]
        ],
        "query_mismatch_indices": [
            index
            for index, pair in enumerate(test)
            if apply_python(pair["input"], rival) != pair["output"]
        ],
    }
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": STATUS,
        "approved": False,
        "seed": seed,
        "parameters": {"segment_owner": owner},
        "parameter_selected_once": True,
        "input_constraints_depend_on_parameter": False,
        "label_source": "python_mirror_blueprint_not_retained_authority",
        "program": program,
        "program_sha256": _sha256(program),
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "generator_path": generator_path,
        "generator_sha256": generator_sha256,
        "train": train,
        "test": test,
        "parameter_rivals": [rival_record],
        "limitations": [
            "Only the declared lower/upper ownership settings are compared.",
            "Finite four-pair episodes do not prove unique induction against undeclared rules.",
            "The prototype is not production- or training-approved.",
        ],
    }


def episode_errors(episode: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(episode, dict):
        return ["episode must be a dictionary"]
    try:
        seed = _validate_seed(episode.get("seed"))
        owner = _validate_owner(episode["parameters"]["segment_owner"])
    except (KeyError, TypeError, ValueError) as exc:
        return [f"invalid episode parameter: {exc}"]
    if episode.get("parameters") != parameters_for_seed(seed):
        errors.append("parameter is not the deterministic once-per-episode selection")
    if episode.get("parameter_selected_once") is not True:
        errors.append("parameter_selected_once must be true")
    if episode.get("program") != materialize_rule(owner):
        errors.append("episode program does not match selected parameter")
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or len(train) != 3:
        errors.append("episode must contain exactly three demonstrations")
        train = []
    if not isinstance(test, list) or len(test) != 1:
        errors.append("episode must contain exactly one query")
        test = []
    rival = next(value for value in ALLOWED_SEGMENT_OWNERS if value != owner)
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                errors.append(f"{split_name}[{index}] must contain input and output")
                continue
            selected_output = apply_python(pair["input"], owner)
            if pair["output"] != selected_output:
                errors.append(f"{split_name}[{index}] output does not match selected setting")
            if apply_python(pair["input"], rival) == selected_output:
                errors.append(f"{split_name}[{index}] does not refute rival {rival}")
    return errors


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove hidden parameters/programs, rival outputs, and query labels."""
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [
            {"input": copy.deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def _racket_materialized_episode(
    seed: int, *, root: Path, bridge: RacketBridge
) -> tuple[dict[str, Any], list[str]]:
    blueprint = build_episode(seed, root=root)
    owner = blueprint["parameters"]["segment_owner"]
    rival = next(value for value in ALLOWED_SEGMENT_OWNERS if value != owner)
    selected_source = materialize_rule(owner, root=root)
    rival_source = materialize_rule(rival, root=root)
    failures: list[str] = []
    labeled_pairs: list[dict[str, Any]] = []
    rival_outputs: list[list[list[int]]] = []
    all_pairs = blueprint["train"] + blueprint["test"]
    for index, pair in enumerate(all_pairs):
        selected_output = execute_rule(selected_source, pair["input"], bridge=bridge)
        rival_output = execute_rule(rival_source, pair["input"], bridge=bridge)
        mirror_selected = apply_python(pair["input"], owner)
        mirror_rival = apply_python(pair["input"], rival)
        if selected_output != mirror_selected:
            failures.append(f"seed={seed} pair={index}: selected Racket/Python mismatch")
        if rival_output != mirror_rival:
            failures.append(f"seed={seed} pair={index}: rival Racket/Python mismatch")
        if selected_output == rival_output:
            failures.append(f"seed={seed} pair={index}: settings do not differ")
        labeled_pairs.append(
            {
                key: copy.deepcopy(value)
                for key, value in pair.items()
                if key not in {"output", "output_sha256"}
            }
            | {
                "output": selected_output,
                "output_sha256": grid_sha256(selected_output),
                "label_source": "bundled_racket_runtime",
            }
        )
        rival_outputs.append(rival_output)

    private = {
        **{
            key: copy.deepcopy(value)
            for key, value in blueprint.items()
            if key not in {"train", "test", "program", "program_sha256", "parameter_rivals", "label_source"}
        },
        "label_source": "bundled_racket_runtime",
        "racket_source": selected_source,
        "racket_sha256": _sha256(selected_source),
        "train": labeled_pairs[:3],
        "test": labeled_pairs[3:],
        "parameter_rivals": [
            {
                "segment_owner": rival,
                "racket_source": rival_source,
                "racket_sha256": _sha256(rival_source),
                "demonstration_mismatch_indices": [
                    index
                    for index in range(3)
                    if rival_outputs[index] != labeled_pairs[index]["output"]
                ],
                "query_mismatch_indices": [
                    index
                    for index in range(1)
                    if rival_outputs[3 + index] != labeled_pairs[3 + index]["output"]
                ],
                "outputs": rival_outputs,
                "output_sha256": [grid_sha256(grid) for grid in rival_outputs],
            }
        ],
        "ambiguities": [],
    }
    if failures:
        private["ambiguities"] = failures
    return private, failures


def _canonical_replay(*, root: Path, bridge: RacketBridge) -> dict[str, Any]:
    source = materialize_rule(DEFAULT_SEGMENT_OWNER, root=root)
    records = []
    failures = []
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        actual = execute_rule(source, pair["input"], bridge=bridge)
        expected = normalize_grid(pair["output"])
        label = f"{pair['split']}[{pair['pair_index']}]"
        passed = actual == expected
        if not passed:
            failures.append(label)
        records.append(
            {
                "label": label,
                "input_sha256": grid_sha256(pair["input"]),
                "expected_sha256": grid_sha256(expected),
                "actual_sha256": grid_sha256(actual),
                "passed": passed,
            }
        )
    return {
        "canonical_setting": DEFAULT_SEGMENT_OWNER,
        "racket_sha256": _sha256(source),
        "pairs": records,
        "passed": len(records) - len(failures),
        "total": len(records),
        "failures": failures,
    }


def _manifest(root: Path) -> dict[str, Any]:
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative == "manifest.json":
            continue
        data = path.read_bytes()
        files.append(
            {"path": relative, "size": len(data), "sha256": _sha256(data)}
        )
    return {
        "schema": "arcpuzzles-parametric-evidence-manifest-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "files": files,
    }


def materialize_evidence(seeds: list[int], *, out: Path) -> dict[str, Any]:
    if not seeds:
        raise ValueError("at least one seed is required")
    normalized_seeds = [_validate_seed(seed) for seed in seeds]
    if out.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {out}")
    out.mkdir(parents=True)
    root = find_root(__file__)
    prototype_path = Path(__file__).resolve()
    test_path = root / "generators" / TASK_ID / "tests" / "test_parametric_segment_owner.py"
    readme_path = prototype_path.with_name("README.md")
    generator_path = root / "generators" / TASK_ID / "generator.py"

    failures: list[str] = []
    episodes: list[dict[str, Any]] = []
    with RacketBridge() as bridge:
        replay = _canonical_replay(root=root, bridge=bridge)
        if replay["failures"]:
            failures.append("canonical default replay failed: " + ", ".join(replay["failures"]))
        _write_json(out / "private" / "canonical_replay.json", replay)

        for episode_index, seed in enumerate(normalized_seeds):
            private, episode_failures = _racket_materialized_episode(
                seed, root=root, bridge=bridge
            )
            failures.extend(episode_failures)
            private_path = out / "private" / f"episode-{episode_index:03d}.json"
            public_path = out / "public" / f"episode-{episode_index:03d}.json"
            _write_json(private_path, private)
            _write_json(public_path, public_challenge(private))
            episodes.append(
                {
                    "seed": seed,
                    "segment_owner": private["parameters"]["segment_owner"],
                    "racket_sha256": private["racket_sha256"],
                    "private_path": private_path.relative_to(out).as_posix(),
                    "public_path": public_path.relative_to(out).as_posix(),
                    "demonstration_mismatch_indices": private["parameter_rivals"][0][
                        "demonstration_mismatch_indices"
                    ],
                    "query_mismatch_indices": private["parameter_rivals"][0][
                        "query_mismatch_indices"
                    ],
                    "ambiguities": private["ambiguities"],
                }
            )

        lower_source = materialize_rule("lower", root=root)
        upper_source = materialize_rule("upper", root=root)
        rules_dir = out / "private" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        (rules_dir / "segment-owner-lower.rkt").write_text(lower_source + "\n", encoding="utf-8")
        (rules_dir / "segment-owner-upper.rkt").write_text(upper_source + "\n", encoding="utf-8")

        witness_grid = build_episode(0, root=root)["train"][0]["input"]
        lower_output = execute_rule(lower_source, witness_grid, bridge=bridge)
        upper_output = execute_rule(upper_source, witness_grid, bridge=bridge)
        witness = {
            "task_id": TASK_ID,
            "input": witness_grid,
            "input_sha256": grid_sha256(witness_grid),
            "lower_output": lower_output,
            "lower_output_sha256": grid_sha256(lower_output),
            "upper_output": upper_output,
            "upper_output_sha256": grid_sha256(upper_output),
            "settings_differ": lower_output != upper_output,
        }
        if not witness["settings_differ"]:
            failures.append("shared distinguishing witness does not distinguish settings")
        _write_json(out / "private" / "shared_input_witness.json", witness)

    owners = {row["segment_owner"] for row in episodes}
    if owners != set(ALLOWED_SEGMENT_OWNERS):
        failures.append(
            "materialized seeds do not cover both settings: " + ", ".join(sorted(owners))
        )
    for row in episodes:
        if row["demonstration_mismatch_indices"] != [0, 1, 2]:
            failures.append(
                f"seed={row['seed']}: rival not refuted by every demonstration"
            )
        if row["query_mismatch_indices"] != [0]:
            failures.append(f"seed={row['seed']}: rival agrees on retained query")

    snapshot_dir = out / "private" / "source_snapshot"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    for source_path in (prototype_path, test_path, readme_path, generator_path):
        if source_path.is_file():
            shutil.copy2(source_path, snapshot_dir / source_path.name)

    generator_sha256 = _sha256(generator_path.read_bytes())
    report = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "PASS" if not failures else "FAIL",
        "approval_status": STATUS,
        "approved": False,
        "parameter": {
            "name": "segment_owner",
            "allowed_values": list(ALLOWED_SEGMENT_OWNERS),
            "default": DEFAULT_SEGMENT_OWNER,
            "selected_once_per_episode": True,
            "input_constraints_depend_on_parameter": False,
        },
        "reasoning_invariants": [
            "select columns whose last nonzero marker is color 5",
            "partition each selected column at its ordered marker rows",
            "preserve marker colors and all non-target columns",
            "leave rows below a floating terminator unchanged",
        ],
        "changed_reasoning_step": (
            "which adjacent marker owns each blank marker-to-marker interval"
        ),
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "generator_source_sha256": generator_sha256,
        "prototype_source_sha256": _sha256(prototype_path.read_bytes()),
        "label_source": "bundled Racket runtime via RacketBridge",
        "seeds": normalized_seeds,
        "episodes": episodes,
        "canonical_replay": replay,
        "shared_witness_path": "private/shared_input_witness.json",
        "exact_racket_paths": {
            "lower": "private/rules/segment-owner-lower.rkt",
            "upper": "private/rules/segment-owner-upper.rkt",
        },
        "command": [sys.executable, *sys.argv],
        "cwd": os.getcwd(),
        "failures": failures,
        "limitations": [
            "Evidence covers two settings and two four-pair episodes only.",
            "Only the declared opposite-setting rival is exhaustively checked.",
            "The selected canonical production API remains non-parametric.",
            "This prototype does not confer production or training approval.",
        ],
    }
    _write_json(out / "report.json", report)
    _write_json(out / "manifest.json", _manifest(out))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = materialize_evidence(args.seeds, out=args.out.resolve())
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
