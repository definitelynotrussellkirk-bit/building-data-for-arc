#!/usr/bin/env python3
"""Proposed episode-level compression-axis extension for ARC task 4e081a15d785.

The production generator and canonical Racket authority remain unchanged.  This
prototype selects one rule per episode: compress adjacent identical whole rows
and columns (canonical), rows only, or columns only.  Every retained label is
executed by the protected Racket bridge.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "4e081a15d785"
PROTOTYPE_VERSION = "1.0.0"
SCHEMA = "arcpuzzles-compression-axes-prototype-v1"
COMPRESSION_AXES = ("both", "rows", "columns")
DEFAULT_COMPRESSION_AXES = "both"
DEFAULT_DEMO_COUNT = 3
DEFAULT_QUERY_COUNT = 4
MAX_TOTAL_PAIRS = 32
CANONICAL_RULE_TEXT = "(rule! (compress-grid g))"
CANONICAL_SHA256 = "0805714fcf25d8095c0f65fdc0cc2c3e25ad692d3a2bb8406a2684142ea5db3b"

_DEDUP_BODY = """(letrec ([dedup-consecutive
            (lambda (lst)
              (cond [(empty? lst) '()]
                    [(empty? (rest lst)) lst]
                    [(equal? (first lst) (second lst))
                     (dedup-consecutive (rest lst))]
                    [else (cons (first lst)
                                (dedup-consecutive (rest lst)))]))])
    {result})"""
ROWS_RULE_TEXT = "(rule! " + _DEDUP_BODY.format(result="(dedup-consecutive g)") + ")"
COLUMNS_RULE_TEXT = "(rule! " + _DEDUP_BODY.format(
    result="(apply map list\n           (dedup-consecutive (apply map list g)))"
) + ")"

# Exact observable generator controls.  Every profile has at least one row and
# one column deletion, so any demonstration distinguishes all three settings by
# dimensions while retaining the same full-line reasoning pattern.
PROFILE_SCHEDULE = (
    {"grid_h": 4, "grid_w": 5, "base_color_count": 3,
     "n_duplicates": 1, "n_column_duplicates": 1},
    {"grid_h": 5, "grid_w": 6, "base_color_count": 4,
     "n_duplicates": 2, "n_column_duplicates": 1},
    {"grid_h": 4, "grid_w": 7, "base_color_count": 5,
     "n_duplicates": 1, "n_column_duplicates": 2},
    {"grid_h": 6, "grid_w": 5, "base_color_count": 4,
     "n_duplicates": 2, "n_column_duplicates": 2},
    {"grid_h": 3, "grid_w": 8, "base_color_count": 4,
     "n_duplicates": 1, "n_column_duplicates": 3},
    {"grid_h": 7, "grid_w": 4, "base_color_count": 3,
     "n_duplicates": 3, "n_column_duplicates": 1},
    {"grid_h": 5, "grid_w": 8, "base_color_count": 6,
     "n_duplicates": 2, "n_column_duplicates": 2},
    {"grid_h": 8, "grid_w": 6, "base_color_count": 7,
     "n_duplicates": 3, "n_column_duplicates": 2},
)
DIFFICULTY_SCHEDULE = ("easy", "medium", "hard", None)


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _grid_sha256(grid: Any) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be a nonnegative plain integer")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_count(value: Any, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a positive plain integer")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _validate_counts(demo_count: Any, query_count: Any) -> tuple[int, int]:
    demos = _validate_count(demo_count, "demo_count")
    queries = _validate_count(query_count, "query_count")
    if demos + queries > MAX_TOTAL_PAIRS:
        raise ValueError(
            f"demo_count + query_count must be at most {MAX_TOTAL_PAIRS}"
        )
    return demos, queries


def _validate_setting(compression_axes: Any) -> str:
    if type(compression_axes) is not str:
        raise TypeError("compression_axes must be a string")
    if compression_axes not in COMPRESSION_AXES:
        raise ValueError(
            f"compression_axes must be one of {COMPRESSION_AXES}, got {compression_axes!r}"
        )
    return compression_axes


def choose_setting(seed: Any) -> str:
    """Select one episode-fixed setting deterministically from the seed."""
    return COMPRESSION_AXES[_validate_seed(seed) % len(COMPRESSION_AXES)]


def canonical_source(*, root: Path | str | None = None) -> str:
    """Load and pin the exact canonical Racket source for this task."""
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
            f"expected one canonical Racket source for {TASK_ID}, got {len(sources)}"
        )
    source = sources.pop()
    if source != CANONICAL_RULE_TEXT:
        raise ValueError("canonical Racket source changed from the pinned exact text")
    actual = _sha256(source)
    if actual != CANONICAL_SHA256:
        raise ValueError(
            f"canonical Racket source hash mismatch: {actual} != {CANONICAL_SHA256}"
        )
    return source


def materialize_rule(
    compression_axes: str = DEFAULT_COMPRESSION_AXES,
    *,
    root: Path | str | None = None,
) -> str:
    """Return the exact Racket rule for one declared episode setting."""
    selected = _validate_setting(compression_axes)
    canonical = canonical_source(root=root)
    if selected == "both":
        return canonical
    if selected == "rows":
        return ROWS_RULE_TEXT
    return COLUMNS_RULE_TEXT


def rule_setting(source: Any) -> str:
    """Recognize only the three exact declared rule texts."""
    if not isinstance(source, str):
        raise TypeError("Racket source must be text")
    by_source = {
        CANONICAL_RULE_TEXT: "both",
        ROWS_RULE_TEXT: "rows",
        COLUMNS_RULE_TEXT: "columns",
    }
    try:
        return by_source[source]
    except KeyError as error:
        raise ValueError("Racket source is not an exact declared materialization") from error


def _rule_body(source: str) -> str:
    rule_setting(source)
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("unexpected rule! wrapper")
    return source[len(prefix):-1].strip()


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
    expression = (
        f"(let ([g {_racket_grid_literal(normalized)}]) {_rule_body(source)})"
    )
    if bridge is None:
        with RacketBridge(timeout=30.0) as owned:
            result = owned.eval_text(expression)
    else:
        result = bridge.eval_text(expression)
    return normalize_grid(result)


def distinguishing_input() -> list[list[int]]:
    """A hand-derived witness with adjacent duplicate rows and columns."""
    return [
        [1, 1, 2, 2],
        [1, 1, 2, 2],
        [3, 3, 4, 4],
        [3, 3, 4, 4],
    ]


def _derived_generation_seed(episode_seed: int, pair_index: int, attempt: int) -> int:
    material = f"{TASK_ID}:{PROTOTYPE_VERSION}:{episode_seed}:{pair_index}:{attempt}"
    return int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], "big") % (2**63)


def _generate_inputs(
    seed: int,
    total: int,
    *,
    root: Path,
) -> tuple[list[list[list[int]]], list[dict[str, Any]], dict[str, str]]:
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    inputs: list[list[list[int]]] = []
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for pair_index in range(total):
        profile = dict(PROFILE_SCHEDULE[(seed + pair_index) % len(PROFILE_SCHEDULE)])
        difficulty = DIFFICULTY_SCHEDULE[(seed + pair_index) % len(DIFFICULTY_SCHEDULE)]
        for attempt in range(64):
            generation_seed = _derived_generation_seed(seed, pair_index, attempt)
            grid = normalize_grid(
                generator.generate(
                    generation_seed,
                    pair_index,
                    difficulty=difficulty,
                    **profile,
                )
            )
            digest = _grid_sha256(grid)
            if digest in seen:
                continue
            observed = generator.observe_overrides(grid)
            if any(observed[key] != value for key, value in profile.items()):
                raise AssertionError(
                    f"selected generator failed exact profile {profile}: {observed}"
                )
            if observed["n_duplicates"] <= 0 or observed["n_column_duplicates"] <= 0:
                raise AssertionError("episode input must exercise both compression axes")
            seen.add(digest)
            inputs.append(grid)
            records.append(
                {
                    "pair_index": pair_index,
                    "generation_seed": generation_seed,
                    "sample_index": pair_index,
                    "difficulty": difficulty,
                    "requested_overrides": profile,
                    "observed_overrides": observed,
                    "input_sha256": digest,
                }
            )
            break
        else:
            raise RuntimeError(f"could not draw distinct input for pair {pair_index}")
    return inputs, records, {
        "path": str(source_path.relative_to(root)),
        "sha256": source_sha256,
    }


def _analyze_outputs(
    selected: str,
    all_outputs: dict[str, list[list[list[int]]]],
    demo_count: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    selected_outputs = all_outputs[selected]
    rows: list[dict[str, Any]] = []
    ambiguities: list[str] = []
    for setting in COMPRESSION_AXES:
        outputs = all_outputs[setting]
        demo_mismatches = [
            index for index in range(demo_count)
            if outputs[index] != selected_outputs[index]
        ]
        query_mismatches = [
            index - demo_count for index in range(demo_count, len(outputs))
            if outputs[index] != selected_outputs[index]
        ]
        if not demo_mismatches and not query_mismatches:
            status = "matches_episode" if setting == selected else "answer_equivalent"
        elif demo_mismatches:
            status = "refuted_by_demonstrations"
        else:
            status = "ambiguous_on_demonstrations"
            ambiguities.append(setting)
        rows.append(
            {
                "compression_axes": setting,
                "status": status,
                "demonstration_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
                "rule_sha256": _sha256(
                    CANONICAL_RULE_TEXT if setting == "both"
                    else ROWS_RULE_TEXT if setting == "rows"
                    else COLUMNS_RULE_TEXT
                ),
            }
        )
    return rows, ambiguities


def _make_episode_with_bridge(
    seed: int,
    *,
    demo_count: int,
    query_count: int,
    compression_axes: str | None,
    root: Path,
    bridge: RacketBridge,
) -> dict[str, Any]:
    selected = choose_setting(seed) if compression_axes is None else _validate_setting(
        compression_axes
    )
    inputs, input_records, generator_source = _generate_inputs(
        seed, demo_count + query_count, root=root
    )
    sources = {
        setting: materialize_rule(setting, root=root) for setting in COMPRESSION_AXES
    }
    all_outputs = {
        setting: [execute_rule(source, grid, bridge=bridge) for grid in inputs]
        for setting, source in sources.items()
    }
    selected_outputs = all_outputs[selected]
    rivals, ambiguities = _analyze_outputs(selected, all_outputs, demo_count)
    if ambiguities:
        raise AssertionError(
            f"episode demonstrations do not identify compression_axes: {ambiguities}"
        )
    pairs = [
        {"input": copy.deepcopy(grid), "output": copy.deepcopy(output)}
        for grid, output in zip(inputs, selected_outputs, strict=True)
    ]
    return {
        "schema": "arcpuzzles-compression-axes-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": {"compression_axes": selected},
        "counts": {"demonstrations": demo_count, "queries": query_count},
        "rule": {
            "compression_axes": selected,
            "racket_source": sources[selected],
            "sha256": _sha256(sources[selected]),
        },
        "input_source": {
            "kind": "selected_generator_exact_overrides",
            "generator": generator_source,
            "records": input_records,
        },
        "train": pairs[:demo_count],
        "test": pairs[demo_count:],
        "parameter_rivals": rivals,
        "ambiguities": ambiguities,
    }


def make_episode(
    seed: Any,
    *,
    demo_count: Any = DEFAULT_DEMO_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
    compression_axes: str | None = None,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one deterministic episode with a single fixed rule setting."""
    validated_seed = _validate_seed(seed)
    demos, queries = _validate_counts(demo_count, query_count)
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    if bridge is None:
        with RacketBridge(timeout=30.0) as owned:
            return _make_episode_with_bridge(
                validated_seed,
                demo_count=demos,
                query_count=queries,
                compression_axes=compression_axes,
                root=resolved_root,
                bridge=owned,
            )
    return _make_episode_with_bridge(
        validated_seed,
        demo_count=demos,
        query_count=queries,
        compression_axes=compression_axes,
        root=resolved_root,
        bridge=bridge,
    )


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project a private episode to visible demonstrations and query inputs."""
    try:
        train = episode["train"]
        test = episode["test"]
    except (KeyError, TypeError) as error:
        raise ValueError("episode must contain train/test pairs") from error
    return {
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in test],
    }


def public_filename(episode: dict[str, Any]) -> str:
    return f"challenge-{public_challenge_id(public_challenge(episode))}.json"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _canonical_check(root: Path, bridge: RacketBridge) -> dict[str, Any]:
    source = materialize_rule("both", root=root)
    rows = []
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        actual = execute_rule(source, pair["input"], bridge=bridge)
        passed = actual == pair["output"]
        rows.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input_sha256": _grid_sha256(pair["input"]),
                "expected_sha256": _grid_sha256(pair["output"]),
                "actual_sha256": _grid_sha256(actual),
                "passed": passed,
            }
        )
    if not rows or not all(row["passed"] for row in rows):
        raise AssertionError("canonical default replay failed")
    return {
        "task_id": TASK_ID,
        "compression_axes": "both",
        "rule_sha256": _sha256(source),
        "pairs": rows,
        "passed": True,
    }


def _witness_check(root: Path, bridge: RacketBridge) -> dict[str, Any]:
    grid = distinguishing_input()
    outputs = {
        setting: execute_rule(
            materialize_rule(setting, root=root), grid, bridge=bridge
        )
        for setting in COMPRESSION_AXES
    }
    if len({_stable_json(output) for output in outputs.values()}) != len(
        COMPRESSION_AXES
    ):
        raise AssertionError("declared settings are not distinct on witness")
    return {
        "input": grid,
        "input_sha256": _grid_sha256(grid),
        "outputs": outputs,
        "output_sha256": {
            setting: _grid_sha256(output) for setting, output in outputs.items()
        },
        "all_settings_distinct": True,
    }


def verify_evidence(
    out: Path | str,
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Re-read a written bundle and replay every private label through Racket."""
    evidence_root = Path(out).resolve()
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()

    def run(runtime: RacketBridge) -> dict[str, Any]:
        report = json.loads((evidence_root / "report.json").read_text(encoding="utf-8"))
        if report.get("task_id") != TASK_ID or report.get("schema") != SCHEMA:
            raise ValueError("evidence report does not belong to this prototype")
        for setting in COMPRESSION_AXES:
            path = evidence_root / f"private/rules/compression-axes-{setting}.rkt"
            if path.read_text(encoding="utf-8") != materialize_rule(
                setting, root=resolved_root
            ) + "\n":
                raise AssertionError(f"stored {setting} Racket source changed")

        labels_checked = 0
        public_ids: list[str] = []
        for row in report["episodes"]:
            private = json.loads(
                (evidence_root / row["private_path"]).read_text(encoding="utf-8")
            )
            public_path = evidence_root / row["public_path"]
            challenge = public_challenge(private)
            expected_bytes = public_challenge_bytes(challenge)
            if public_path.read_bytes() != expected_bytes:
                raise AssertionError("public challenge bytes differ from allowlisted projection")
            observed_id = public_challenge_id(challenge)
            if observed_id != row["public_id"]:
                raise AssertionError("public challenge ID mismatch")
            public_ids.append(observed_id)
            selected = private["parameters"]["compression_axes"]
            source = materialize_rule(selected, root=resolved_root)
            if private["rule"]["racket_source"] != source:
                raise AssertionError("private episode rule does not match its setting")
            for pair in private["train"] + private["test"]:
                if execute_rule(source, pair["input"], bridge=runtime) != pair["output"]:
                    raise AssertionError("private label failed live Racket replay")
                labels_checked += 1
            if private.get("ambiguities"):
                raise AssertionError("retained episode has an unresolved parameter rival")
        if public_ids != sorted(public_ids) or len(public_ids) != len(set(public_ids)):
            raise AssertionError("public challenge rows are not sorted and unique")

        canonical = _canonical_check(resolved_root, runtime)
        labels_checked += len(canonical["pairs"])
        return {
            "schema": "arcpuzzles-compression-axes-verification-v1",
            "status": "pass",
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "public_challenges_checked": len(public_ids),
            "live_labels_checked": labels_checked,
            "canonical_pairs_checked": len(canonical["pairs"]),
            "public_ids": public_ids,
            "runtime_identity": runtime.runtime_identity,
        }

    if bridge is None:
        with RacketBridge(timeout=30.0) as owned:
            return run(owned)
    return run(bridge)


def _manifest(root: Path) -> dict[str, Any]:
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": _file_sha256(path),
                "size": path.stat().st_size,
            }
        )
    return {
        "schema": "arcpuzzles-compression-axes-manifest-v1",
        "task_id": TASK_ID,
        "files": files,
    }


def _write_evidence_with_bridge(
    seeds: Iterable[Any],
    *,
    demo_count: Any,
    query_count: Any,
    out: Path,
    root: Path,
    bridge: RacketBridge,
) -> dict[str, Any]:
    validated_seeds = [_validate_seed(seed) for seed in seeds]
    if not validated_seeds:
        raise ValueError("at least one episode seed is required")
    demos, queries = _validate_counts(demo_count, query_count)
    episodes = [
        make_episode(
            seed,
            demo_count=demos,
            query_count=queries,
            root=root,
            bridge=bridge,
        )
        for seed in validated_seeds
    ]
    prepared = [
        {
            "episode": episode,
            "public_id": public_challenge_id(public_challenge(episode)),
        }
        for episode in episodes
    ]
    ids = [row["public_id"] for row in prepared]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate visible challenge in requested episode batch")
    prepared.sort(key=lambda row: row["public_id"])

    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{out.name}.tmp-", dir=out.parent))
    try:
        for setting in COMPRESSION_AXES:
            _write_text(
                temp / f"private/rules/compression-axes-{setting}.rkt",
                materialize_rule(setting, root=root) + "\n",
            )
        canonical = _canonical_check(root, bridge)
        witness = _witness_check(root, bridge)
        _write_json(temp / "private/canonical-default-check.json", canonical)
        _write_json(temp / "private/distinguishing-witness.json", witness)

        episode_rows = []
        for index, row in enumerate(prepared):
            episode = row["episode"]
            public_id = row["public_id"]
            private_rel = f"private/episodes/episode-{index:03d}.json"
            public_rel = f"public/challenge-{public_id}.json"
            _write_json(temp / private_rel, episode)
            public_path = temp / public_rel
            public_path.parent.mkdir(parents=True, exist_ok=True)
            public_path.write_bytes(public_challenge_bytes(public_challenge(episode)))
            episode_rows.append(
                {
                    "seed": episode["seed"],
                    "parameters": episode["parameters"],
                    "counts": episode["counts"],
                    "rule_sha256": episode["rule"]["sha256"],
                    "public_id": public_id,
                    "public_path": public_rel,
                    "private_path": private_rel,
                }
            )

        prototype_path = Path(__file__).resolve()
        generator_path = root / f"generators/{TASK_ID}/generator.py"
        test_path = root / f"generators/{TASK_ID}/tests/test_parametric_compression_axes.py"
        report = {
            "schema": SCHEMA,
            "status": "proposed_unapproved",
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "parameter": {
                "name": "compression_axes",
                "allowed_values": list(COMPRESSION_AXES),
                "original_default": DEFAULT_COMPRESSION_AXES,
                "input_constraints": (
                    "Every authored episode input has at least one adjacent duplicate whole "
                    "row and column so demonstrations identify the selected axis behavior."
                ),
            },
            "counts": {
                "episodes": len(episode_rows),
                "settings_exercised": len(
                    {row["parameters"]["compression_axes"] for row in episode_rows}
                ),
                "demonstrations": len(episode_rows) * demos,
                "queries": len(episode_rows) * queries,
                "ambiguous_parameter_rivals": sum(
                    len(row["episode"]["ambiguities"]) for row in prepared
                ),
            },
            "episodes": episode_rows,
            "sources": {
                "prototype": {
                    "path": prototype_path.relative_to(root).as_posix(),
                    "sha256": _file_sha256(prototype_path),
                },
                "focused_test": {
                    "path": test_path.relative_to(root).as_posix(),
                    "sha256": _file_sha256(test_path),
                },
                "production_generator": {
                    "path": generator_path.relative_to(root).as_posix(),
                    "sha256": _file_sha256(generator_path),
                },
                "canonical_ledger": {
                    "path": canonical_path(root).relative_to(root).as_posix(),
                    "sha256": _file_sha256(canonical_path(root)),
                },
            },
            "rules": {
                setting: {
                    "path": f"private/rules/compression-axes-{setting}.rkt",
                    "sha256": _sha256(materialize_rule(setting, root=root)),
                    "canonical_default": setting == DEFAULT_COMPRESSION_AXES,
                }
                for setting in COMPRESSION_AXES
            },
            "canonical_check_path": "private/canonical-default-check.json",
            "distinguishing_witness_path": "private/distinguishing-witness.json",
            "verification_path": "verification.json",
            "manifest_path": "manifest.json",
            "runtime_identity": bridge.runtime_identity,
            "command": {
                "cwd": str(Path.cwd()),
                "argv": [sys.executable, *sys.argv],
            },
            "limitations": [
                "Prototype only: production generator, catalog authority, and approval state are unchanged.",
                "Finite evidence covers the requested seeds and the three declared axis settings, not every grid or rival program.",
                f"Episode size is bounded to {MAX_TOTAL_PAIRS} total pairs for review-time execution.",
                "All authored inputs deliberately contain duplicates on both axes; support outside that teaching grammar is not claimed.",
            ],
        }
        _write_json(temp / "report.json", report)
        verification = verify_evidence(temp, root=root, bridge=bridge)
        _write_json(temp / "verification.json", verification)
        _write_json(temp / "manifest.json", _manifest(temp))
        temp.rename(out)
        return report
    except BaseException:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def write_evidence(
    seeds: Iterable[Any],
    *,
    demo_count: Any = DEFAULT_DEMO_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
    out: Path | str,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Write an atomic public/private evidence bundle and verify it live."""
    output = Path(out).resolve()
    if output.exists():
        raise FileExistsError(output)
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    if bridge is None:
        with RacketBridge(timeout=30.0) as owned:
            return _write_evidence_with_bridge(
                seeds,
                demo_count=demo_count,
                query_count=query_count,
                out=output,
                root=resolved_root,
                bridge=owned,
            )
    return _write_evidence_with_bridge(
        seeds,
        demo_count=demo_count,
        query_count=query_count,
        out=output,
        root=resolved_root,
        bridge=bridge,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--demo-count", type=int, default=DEFAULT_DEMO_COUNT)
    parser.add_argument("--query-count", type=int, default=DEFAULT_QUERY_COUNT)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(
        args.seeds,
        demo_count=args.demo_count,
        query_count=args.query_count,
        out=args.out,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "out": str(args.out),
                "episodes": report["counts"]["episodes"],
                "settings_exercised": report["counts"]["settings_exercised"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
