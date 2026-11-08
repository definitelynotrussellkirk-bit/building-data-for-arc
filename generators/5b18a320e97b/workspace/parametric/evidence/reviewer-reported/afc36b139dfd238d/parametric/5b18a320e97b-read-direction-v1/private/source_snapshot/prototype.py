#!/usr/bin/env python3
"""Proposed episode-level read-direction extension for ARC task 5b18a320e97b.

This task-local prototype preserves the selected production generator and exact
canonical Racket authority. It adds one bounded episode parameter: whether the
visible line colors are read in canonical spatial order or the reverse order.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import nullcontext
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "5b18a320e97b"
PROTOTYPE_VERSION = "1.0.0"
SCHEMA = "arcpuzzles-read-direction-prototype-v1"
READ_DIRECTIONS = ("forward", "reverse")
DEFAULT_READ_DIRECTION = "forward"
DEFAULT_DEMO_COUNT = 3
DEFAULT_QUERY_COUNT = 4
CANONICAL_SHA256 = "c88b81c9786841551051d1c26625321375d4849229760bd0e40b7329fda63231"
CANONICAL_SORT_BINDING = """(sorted-colors (if horizontal
                                     (sort-by colors
                                              (lambda (col)
                                                (first (color-first-cell col))))
                                     (sort-by colors
                                              (lambda (col)
                                                (second (color-first-cell col))))))"""
REVERSE_SORT_BINDING = CANONICAL_SORT_BINDING.replace(
    "(sorted-colors (if horizontal",
    "(sorted-colors (reverse (if horizontal",
    1,
) + ")"

# Each seven-example default episode crosses both orientations and at least
# four color cardinalities. Rotating this schedule by seed keeps that coverage.
PROFILE_SCHEDULE = (
    "horizontal_n2",
    "vertical_n3",
    "horizontal_n4",
    "vertical_n5",
    "horizontal_n6",
    "vertical_n7",
    "horizontal_n3",
    "vertical_n4",
    "horizontal_n5",
    "vertical_n6",
    "horizontal_n7",
    "vertical_n2",
)
DIFFICULTY_SCHEDULE = ("easy", "medium", "hard", None)


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _grid_sha256(grid: Any) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be a nonnegative plain integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def _validate_count(value: Any, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} count must be a positive plain integer")
    if value <= 0:
        raise ValueError(f"{name} count must be positive")
    return value


def _validate_read_direction(read_direction: Any) -> str:
    if type(read_direction) is not str:
        raise TypeError("read_direction must be a string")
    if read_direction not in READ_DIRECTIONS:
        raise ValueError(
            f"read_direction must be one of {READ_DIRECTIONS}, got {read_direction!r}"
        )
    return read_direction


def choose_setting(seed: Any) -> str:
    """Select one episode-fixed setting deterministically from a valid seed."""
    validated = _validate_seed(seed)
    return READ_DIRECTIONS[validated % len(READ_DIRECTIONS)]


def _check_canonical_source(source: Any) -> str:
    if not isinstance(source, str):
        raise ValueError("canonical Racket source must be text")
    actual = _sha256(source)
    if actual != CANONICAL_SHA256:
        raise ValueError(
            f"canonical Racket source hash mismatch: {actual} != {CANONICAL_SHA256}"
        )
    if source.count(CANONICAL_SORT_BINDING) != 1:
        raise ValueError("canonical source does not contain the unique sort binding")
    if REVERSE_SORT_BINDING in source:
        raise ValueError("canonical source unexpectedly contains reverse ordering")
    return source


def canonical_source(*, root: Path | str | None = None) -> str:
    """Load and pin the exact canonical Racket authority for this task."""
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(resolved_root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(
                row.get("program_solution"), str
            ):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(
            f"expected exactly one canonical source for {TASK_ID}, got {len(sources)}"
        )
    return _check_canonical_source(sources.pop())


def materialize_rule(
    read_direction: str = DEFAULT_READ_DIRECTION,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    """Instantiate one declared setting while preserving exact default bytes."""
    selected = _validate_read_direction(read_direction)
    canonical = (
        canonical_source(root=root)
        if source is None
        else _check_canonical_source(source)
    )
    if selected == DEFAULT_READ_DIRECTION:
        return canonical
    alternative = canonical.replace(
        CANONICAL_SORT_BINDING,
        REVERSE_SORT_BINDING,
        1,
    )
    if alternative.count(REVERSE_SORT_BINDING) != 1:
        raise AssertionError("failed to materialize reverse read direction")
    return alternative


def restore_canonical(source: Any) -> str:
    """Restore either declared materialization to the exact canonical source."""
    if not isinstance(source, str):
        raise ValueError("Racket source must be text")
    if source.count(REVERSE_SORT_BINDING) == 1:
        restored = source.replace(
            REVERSE_SORT_BINDING,
            CANONICAL_SORT_BINDING,
            1,
        )
    elif source.count(CANONICAL_SORT_BINDING) == 1:
        restored = source
    else:
        raise ValueError("Racket source must contain exactly one declared sort binding")
    return _check_canonical_source(restored)


def rule_callable(source: str) -> str:
    """Strip only the outer ``rule!`` wrapper from a declared rule source."""
    restore_canonical(source)
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    callable_source = source[len("(rule!") : -1].strip()
    if not callable_source.startswith("(lambda (g)"):
        raise ValueError("expected a wrapped grid lambda")
    return callable_source


def _racket_grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")"


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    """Execute one exact declared Racket rule on one normalized grid."""
    normalized = normalize_grid(grid)
    expression = f"({rule_callable(source)} {_racket_grid_literal(normalized)})"
    manager = nullcontext(bridge) if bridge is not None else RacketBridge(timeout=30)
    with manager as active:
        assert active is not None
        return normalize_grid(active.eval_text(expression))


def _derived_generation_seed(episode_seed: int, pair_index: int, attempt: int) -> int:
    digest = _sha256(f"{TASK_ID}:{episode_seed}:{pair_index}:{attempt}")
    return int(digest[:16], 16)


def _generate_inputs(
    seed: int,
    count: int,
    *,
    root: Path,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root
    )
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    start = seed % len(PROFILE_SCHEDULE)
    for pair_index in range(count):
        profile = PROFILE_SCHEDULE[(start + pair_index) % len(PROFILE_SCHEDULE)]
        difficulty = DIFFICULTY_SCHEDULE[pair_index % len(DIFFICULTY_SCHEDULE)]
        for attempt in range(50):
            generation_seed = _derived_generation_seed(seed, pair_index, attempt)
            grid = generator.generate(
                generation_seed,
                pair_index,
                difficulty=difficulty,
                scene_profile=profile,
            )
            errors = generator.self_check(grid, difficulty=difficulty)
            if errors:
                raise AssertionError(
                    f"selected generator emitted invalid {profile}: {errors}"
                )
            observed = generator.observe_overrides(grid)
            if observed != {"scene_profile": profile}:
                raise AssertionError(
                    f"selected generator missed requested profile {profile}: {observed}"
                )
            normalized = normalize_grid(grid)
            digest = _grid_sha256(normalized)
            if digest in seen:
                continue
            seen.add(digest)
            rows.append(
                {
                    "input": normalized,
                    "input_sha256": digest,
                    "sampling": {
                        "seed": generation_seed,
                        "sample_index": pair_index,
                        "attempt": attempt,
                        "difficulty": difficulty,
                        "scene_profile": profile,
                    },
                }
            )
            break
        else:
            raise AssertionError(
                f"could not generate a distinct lawful input for pair {pair_index}"
            )
    return rows, {
        "path": generator_path.relative_to(root).as_posix(),
        "sha256": generator_sha256,
        "version": str(generator.VERSION),
        "rule_hash": str(generator.RULE_HASH),
    }


def make_episode(
    seed: Any,
    *,
    read_direction: str | None = None,
    demo_count: Any = DEFAULT_DEMO_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one deterministic episode whose parameter is fixed across all pairs."""
    episode_seed = _validate_seed(seed)
    demos = _validate_count(demo_count, "demo")
    queries = _validate_count(query_count, "query")
    selected = (
        choose_setting(episode_seed)
        if read_direction is None
        else _validate_read_direction(read_direction)
    )
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    inputs, generator_record = _generate_inputs(
        episode_seed, demos + queries, root=resolved_root
    )
    canonical = canonical_source(root=resolved_root)
    rules = {
        setting: materialize_rule(setting, source=canonical)
        for setting in READ_DIRECTIONS
    }
    manager = nullcontext(bridge) if bridge is not None else RacketBridge(timeout=30)
    pairs: list[dict[str, Any]] = []
    with manager as active:
        assert active is not None
        for pair_index, fixture in enumerate(inputs):
            outputs = {
                setting: execute_rule(source, fixture["input"], bridge=active)
                for setting, source in rules.items()
            }
            if len({_stable_json(output) for output in outputs.values()}) != len(outputs):
                raise AssertionError(
                    f"read-direction settings did not distinguish pair {pair_index}"
                )
            selected_output = outputs[selected]
            pairs.append(
                {
                    "pair_index": pair_index,
                    "split": "train" if pair_index < demos else "test",
                    "read_direction": selected,
                    "input": fixture["input"],
                    "output": selected_output,
                    "input_sha256": fixture["input_sha256"],
                    "output_sha256": _grid_sha256(selected_output),
                    "sampling": fixture["sampling"],
                    "counterfactual_outputs": outputs,
                }
            )
    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": episode_seed,
        "parameters": {"read_direction": selected},
        "parameter_selection": (
            "read_direction is fixed once per episode; absent an explicit setting, "
            "seed parity selects forward then reverse"
        ),
        "counts": {"demonstrations": demos, "queries": queries},
        "generator": generator_record,
        "canonical_source_sha256": CANONICAL_SHA256,
        "program": rules[selected],
        "program_sha256": _sha256(rules[selected]),
        "programs_by_read_direction": rules,
        "pairs": copy.deepcopy(pairs),
        "train": copy.deepcopy(pairs[:demos]),
        "test": copy.deepcopy(pairs[demos:]),
    }


def analyze_episode(
    episode: dict[str, Any],
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Re-execute every declared setting and explicitly refute rivals on demos."""
    if not isinstance(episode, dict):
        raise TypeError("episode must be a dictionary")
    selected = _validate_read_direction(
        episode.get("parameters", {}).get("read_direction")
    )
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not train or not isinstance(test, list) or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    canonical = canonical_source(root=resolved_root)
    rules = {
        setting: materialize_rule(setting, source=canonical)
        for setting in READ_DIRECTIONS
    }
    manager = nullcontext(bridge) if bridge is not None else RacketBridge(timeout=30)
    settings: list[dict[str, Any]] = []
    with manager as active:
        assert active is not None
        for setting, source in rules.items():
            train_predictions = [
                execute_rule(source, pair["input"], bridge=active) for pair in train
            ]
            query_predictions = [
                execute_rule(source, pair["input"], bridge=active) for pair in test
            ]
            demo_mismatches = [
                index
                for index, (prediction, pair) in enumerate(
                    zip(train_predictions, train, strict=True)
                )
                if prediction != normalize_grid(pair["output"])
            ]
            query_mismatches = [
                index
                for index, (prediction, pair) in enumerate(
                    zip(query_predictions, test, strict=True)
                )
                if prediction != normalize_grid(pair["output"])
            ]
            status = (
                "matches_episode"
                if not demo_mismatches and not query_mismatches
                else "refuted_by_demonstrations"
                if demo_mismatches
                else "ambiguous_query"
            )
            settings.append(
                {
                    "read_direction": setting,
                    "status": status,
                    "program_sha256": _sha256(source),
                    "demonstration_mismatch_indices": demo_mismatches,
                    "query_mismatch_indices": query_mismatches,
                    "train_predictions": train_predictions,
                    "query_predictions": query_predictions,
                }
            )
    matches = [
        row["read_direction"]
        for row in settings
        if row["status"] == "matches_episode"
    ]
    return {
        "status": (
            "no_ambiguity_found"
            if matches == [selected]
            and all(
                row["status"] == "refuted_by_demonstrations"
                for row in settings
                if row["read_direction"] != selected
            )
            else "ambiguity_or_label_failure"
        ),
        "selected_read_direction": selected,
        "matching_settings": matches,
        "settings": settings,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return only model-visible demonstrations and query inputs."""
    if not isinstance(episode, dict):
        raise TypeError("episode must be a dictionary")
    return copy.deepcopy(
        {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in episode["train"]
            ],
            "test": [{"input": pair["input"]} for pair in episode["test"]],
        }
    )


def public_filename(episode: dict[str, Any]) -> str:
    """Name public evidence from exactly the visible challenge bytes."""
    return f"challenge-{public_challenge_id(public_challenge(episode))}.json"



def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_public(path: Path, challenge: dict[str, Any]) -> None:
    payload = public_challenge_bytes(challenge)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() == payload:
            raise ValueError(f"duplicate visible public challenge: {path.name}")
        raise AssertionError(f"public challenge identifier collision: {path.name}")
    path.write_bytes(payload)


def _file_record(path: Path, *, relative_to: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(relative_to).as_posix(),
        "sha256": _sha256(path.read_bytes()),
    }


def verify_evidence(
    out: Path | str,
    *,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Re-execute a written bundle and verify its visible/private boundaries."""
    evidence_root = Path(out).resolve()
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    report = json.loads((evidence_root / "report.json").read_text(encoding="utf-8"))
    if report.get("task_id") != TASK_ID:
        raise AssertionError("evidence report belongs to another task")
    if report.get("status") != "proposed_unapproved" or report.get("approved") is not False:
        raise AssertionError("evidence must remain explicitly proposed and unapproved")

    canonical = canonical_source(root=resolved_root)
    rule_sources: dict[str, str] = {}
    for row in report["rules"]:
        setting = _validate_read_direction(row["read_direction"])
        path = evidence_root / row["path"]
        source = path.read_text(encoding="utf-8")
        if _sha256(path.read_bytes()) != row["sha256"]:
            raise AssertionError(f"rule hash mismatch for {setting}")
        if source != materialize_rule(setting, source=canonical):
            raise AssertionError(f"stored rule is not the exact {setting} materialization")
        rule_sources[setting] = source
    if set(rule_sources) != set(READ_DIRECTIONS):
        raise AssertionError("evidence must contain every declared rule setting")

    for row in report["files"]:
        path = evidence_root / row["path"]
        if not path.is_file() or _sha256(path.read_bytes()) != row["sha256"]:
            raise AssertionError(f"payload file hash mismatch: {row['path']}")

    labels_checked = 0
    rival_predictions_checked = 0
    distinct_inputs: set[str] = set()
    settings_exercised: set[str] = set()
    canonical_rows: list[dict[str, Any]] = []
    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        for pair in canonical_pairs(TASK_ID, root=resolved_root, labeled_only=True):
            actual = execute_rule(canonical, pair["input"], bridge=bridge)
            canonical_rows.append(
                {
                    **pair,
                    "actual": actual,
                    "matches": actual == pair["output"],
                    "input_sha256": _grid_sha256(pair["input"]),
                    "actual_output_sha256": _grid_sha256(actual),
                }
            )
        if not canonical_rows or not all(row["matches"] for row in canonical_rows):
            raise AssertionError("forward default failed a labeled canonical pair")
        stored_canonical = json.loads(
            (evidence_root / report["canonical_check_path"]).read_text(encoding="utf-8")
        )
        if stored_canonical != canonical_rows:
            raise AssertionError("stored canonical replay differs from live Racket replay")

        for row in report["episodes"]:
            episode = json.loads(
                (evidence_root / row["private_path"]).read_text(encoding="utf-8")
            )
            stored_analysis = json.loads(
                (evidence_root / row["analysis_path"]).read_text(encoding="utf-8")
            )
            selected = _validate_read_direction(
                episode["parameters"]["read_direction"]
            )
            settings_exercised.add(selected)
            visible = public_challenge(episode)
            public_path = evidence_root / row["public_path"]
            if public_path.name != public_filename(episode):
                raise AssertionError("public filename is not derived from visible bytes")
            if public_path.read_bytes() != public_challenge_bytes(visible):
                raise AssertionError("public challenge bytes contain drift or private data")

            live_analysis = analyze_episode(
                episode, root=resolved_root, bridge=bridge
            )
            if live_analysis != stored_analysis:
                raise AssertionError("stored rival analysis differs from live Racket replay")
            if live_analysis["status"] != "no_ambiguity_found":
                raise AssertionError("episode is ambiguous under a declared setting")
            by_setting = {
                item["read_direction"]: item for item in live_analysis["settings"]
            }
            pairs = episode["train"] + episode["test"]
            for pair_index, pair in enumerate(pairs):
                distinct_inputs.add(pair["input_sha256"])
                selected_prediction = (
                    by_setting[selected]["train_predictions"][pair_index]
                    if pair_index < len(episode["train"])
                    else by_setting[selected]["query_predictions"][
                        pair_index - len(episode["train"])
                    ]
                )
                if selected_prediction != pair["output"]:
                    raise AssertionError("selected Racket prediction differs from stored label")
                labels_checked += 1
                for setting in READ_DIRECTIONS:
                    prediction = (
                        by_setting[setting]["train_predictions"][pair_index]
                        if pair_index < len(episode["train"])
                        else by_setting[setting]["query_predictions"][
                            pair_index - len(episode["train"])
                        ]
                    )
                    if prediction != pair["counterfactual_outputs"][setting]:
                        raise AssertionError("stored counterfactual differs from live Racket")
                    rival_predictions_checked += 1

            replay = make_episode(
                episode["seed"],
                read_direction=selected,
                demo_count=len(episode["train"]),
                query_count=len(episode["test"]),
                root=resolved_root,
                bridge=bridge,
            )
            if replay != episode:
                raise AssertionError("same-seed episode replay changed")

    expected_counts = report["counts"]
    if labels_checked != expected_counts["train_pairs"] + expected_counts["query_pairs"]:
        raise AssertionError("label count does not match report")
    if len(distinct_inputs) != expected_counts["distinct_input_grids"]:
        raise AssertionError("distinct input count does not match report")
    if settings_exercised != set(READ_DIRECTIONS):
        raise AssertionError("evidence seeds do not exercise every setting")
    return {
        "schema": "arcpuzzles-parametric-evidence-verification-v1",
        "status": "pass",
        "task_id": TASK_ID,
        "episodes_checked": len(report["episodes"]),
        "labels_checked": labels_checked,
        "rival_predictions_checked": rival_predictions_checked,
        "canonical_pairs_checked": len(canonical_rows),
        "settings_exercised": sorted(settings_exercised),
        "distinct_input_grids": len(distinct_inputs),
    }


def write_evidence(
    seeds: Any,
    *,
    out: Path | str,
    demo_count: Any = DEFAULT_DEMO_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Write a finite, source-bound bundle to a new directory and verify it."""
    episode_seeds = tuple(seeds)
    if not episode_seeds or len(set(episode_seeds)) != len(episode_seeds):
        raise ValueError("provide at least one distinct episode seed")
    for seed in episode_seeds:
        _validate_seed(seed)
    demos = _validate_count(demo_count, "demo")
    queries = _validate_count(query_count, "query")
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    output = Path(out)
    output.mkdir(parents=True, exist_ok=False)
    try:
        report = _write_evidence(
            episode_seeds,
            out=output.resolve(),
            root=resolved_root,
            demo_count=demos,
            query_count=queries,
        )
        verification = verify_evidence(output, root=resolved_root)
        _write_json(output / "verification.json", verification)
        report["verification"] = verification
        report["verification_path"] = "verification.json"
        _write_json(output / "report.json", report)
        return report
    except Exception as exc:
        _write_json(
            output / "failure.json",
            {
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "seeds": list(episode_seeds),
                "demo_count": demos,
                "query_count": queries,
            },
        )
        raise


def _write_evidence(
    seeds: tuple[int, ...],
    *,
    out: Path,
    root: Path,
    demo_count: int,
    query_count: int,
) -> dict[str, Any]:
    source_rows: list[dict[str, str]] = []
    for path in (
        Path(__file__).resolve(),
        root / f"generators/{TASK_ID}/tests/test_parametric_read_direction.py",
    ):
        if path.is_file():
            destination = out / "private/source_snapshot" / path.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(path.read_bytes())
            source_rows.append(
                {
                    **_file_record(path, relative_to=root),
                    "snapshot": destination.relative_to(out).as_posix(),
                }
            )

    runtime_rows: list[dict[str, str]] = []
    for name in (
        "reviewer_support.py",
        "arc_repl/racket_bridge.py",
        "arc_repl/racket_prelude/arc-prelude.rkt",
    ):
        path = root / "shared/runtime" / name
        runtime_rows.append(_file_record(path, relative_to=root))
    runtime = racket_runtime_status()
    if runtime.get("available") and runtime.get("resolved_binary"):
        runtime["resolved_binary_sha256"] = _sha256(
            Path(runtime["resolved_binary"]).read_bytes()
        )

    canonical = canonical_source(root=root)
    rule_rows: list[dict[str, str]] = []
    for setting in READ_DIRECTIONS:
        source = materialize_rule(setting, source=canonical)
        path = out / f"private/rules/read-direction-{setting}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        rule_rows.append(
            {
                "read_direction": setting,
                "path": path.relative_to(out).as_posix(),
                "sha256": _sha256(path.read_bytes()),
                "callable_sha256": _sha256(rule_callable(source)),
            }
        )

    canonical_rows: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []
    distinct_inputs: set[str] = set()
    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute_rule(canonical, pair["input"], bridge=bridge)
            canonical_rows.append(
                {
                    **pair,
                    "actual": actual,
                    "matches": actual == pair["output"],
                    "input_sha256": _grid_sha256(pair["input"]),
                    "actual_output_sha256": _grid_sha256(actual),
                }
            )
        if not canonical_rows or not all(row["matches"] for row in canonical_rows):
            raise AssertionError("forward default failed a labeled canonical pair")
        canonical_check_path = "private/canonical-default-check.json"
        _write_json(out / canonical_check_path, canonical_rows)

        for index, seed in enumerate(seeds):
            episode = make_episode(
                seed,
                demo_count=demo_count,
                query_count=query_count,
                root=root,
                bridge=bridge,
            )
            replay = make_episode(
                seed,
                demo_count=demo_count,
                query_count=query_count,
                root=root,
                bridge=bridge,
            )
            if replay != episode:
                raise AssertionError("same-seed episode replay changed")
            analysis = analyze_episode(episode, root=root, bridge=bridge)
            if analysis["status"] != "no_ambiguity_found":
                raise AssertionError("declared rival was not refuted by demonstrations")

            public = public_challenge(episode)
            public_path = f"public/{public_filename(episode)}"
            public_file = out / public_path
            _write_public(public_file, public)
            private_path = f"private/episodes/episode-{index:03d}.json"
            analysis_path = f"private/episodes/episode-{index:03d}-analysis.json"
            _write_json(out / private_path, episode)
            _write_json(out / analysis_path, analysis)
            distinct_inputs.update(pair["input_sha256"] for pair in episode["pairs"])
            episode_rows.append(
                {
                    "seed": seed,
                    "parameters": episode["parameters"],
                    "demo_count": len(episode["train"]),
                    "query_count": len(episode["test"]),
                    "public_path": public_path,
                    "public_id": public_challenge_id(public),
                    "private_path": private_path,
                    "analysis_path": analysis_path,
                    "episode_sha256": _sha256(_stable_json(episode)),
                    "deterministic_replay": True,
                    "rivals": [
                        {
                            key: item[key]
                            for key in (
                                "read_direction",
                                "status",
                                "demonstration_mismatch_indices",
                                "query_mismatch_indices",
                            )
                        }
                        for item in analysis["settings"]
                    ],
                }
            )

    episode_rows.sort(key=lambda row: row["public_id"])
    settings_exercised = {
        row["parameters"]["read_direction"] for row in episode_rows
    }
    if settings_exercised != set(READ_DIRECTIONS):
        raise AssertionError(
            f"seed set must exercise both read directions, got {settings_exercised}"
        )
    ambiguous_count = sum(
        rival["status"] == "ambiguous_query"
        for episode in episode_rows
        for rival in episode["rivals"]
    )
    files = [
        _file_record(path, relative_to=out)
        for path in sorted(out.rglob("*"))
        if path.is_file()
    ]
    report: dict[str, Any] = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": "read_direction",
            "allowed_values": list(READ_DIRECTIONS),
            "original_default": DEFAULT_READ_DIRECTION,
            "input_constraints_depend_on_parameter": False,
        },
        "invariant_reasoning": (
            "ignore zero and gray, infer the common line orientation, preserve "
            "the same visible line objects and stripe construction; only reverse "
            "the spatial order of the colors before constructing the output"
        ),
        "input_scope": (
            f"deterministic lawful general profiles with {demo_count} demonstrations "
            f"and {query_count} distinct queries per episode"
        ),
        "sources": source_rows,
        "runtime_files": runtime_rows,
        "runtime": runtime,
        "rules": rule_rows,
        "canonical_source_sha256": CANONICAL_SHA256,
        "canonical_check_path": canonical_check_path,
        "episodes": episode_rows,
        "files": files,
        "counts": {
            "episodes": len(episode_rows),
            "train_pairs": demo_count * len(episode_rows),
            "query_pairs": query_count * len(episode_rows),
            "distinct_input_grids": len(distinct_inputs),
            "settings_exercised": len(settings_exercised),
            "canonical_pairs_checked": len(canonical_rows),
            "parameter_rival_episode_checks": len(READ_DIRECTIONS) * len(episode_rows),
            "ambiguous_parameter_rivals": ambiguous_count,
        },
        "limitations": [
            "Proposed task-local prototype only; no production API, catalog, or approval change.",
            "Evidence covers two settings and the supplied finite seed set, not all seeds or rival rules.",
            "The only declared semantic variation is forward versus reverse spatial color order.",
            "Rival checks cover the two declared read_direction settings, not every conceivable hypothesis.",
            "The forward source is byte-identical to the pinned canonical Racket authority and is replayed on every labeled canonical record.",
        ],
        "process_argv": list(sys.argv),
        "effective_cwd": str(Path.cwd()),
    }
    _write_json(out / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--demo-count", type=int, default=DEFAULT_DEMO_COUNT)
    parser.add_argument("--query-count", type=int, default=DEFAULT_QUERY_COUNT)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    args = parser.parse_args(argv)
    report = write_evidence(
        args.seeds,
        out=args.out,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "counts": report["counts"],
                "verification": report["verification"],
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
