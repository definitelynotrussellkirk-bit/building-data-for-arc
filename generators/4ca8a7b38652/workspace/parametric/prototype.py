#!/usr/bin/env python3
"""Bounded parametric prototype for ARC task 4ca8a7b38652.

The production/canonical setting is ``count_scope='nonzero'``: the upscale
factor is the number of distinct nonzero colors.  The proposed ``'all'``
setting counts every distinct color, including zero.  A setting is selected
once for the whole episode; inputs are generated independently of that hidden
setting, and zero-present demonstrations distinguish the two rules.

This module is authoring evidence only.  It does not modify the selected
canonical rule or production sampler.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "4ca8a7b38652"
PROTOTYPE_VERSION = "count-scope-v2"
DEFAULT_TRAIN_COUNT = 4
DEFAULT_TEST_COUNT = 4
MAX_EPISODE_PAIRS = 64
MAX_DRAW_ATTEMPTS = 64
PARAMETER_NAME = "count_scope"
SETTINGS = ("nonzero", "all")
DEFAULT_SETTING = "nonzero"
CANONICAL_RULE_SHA256 = (
    "d91346f9bf6dbc10251783f3ea5e16533a63631db37bec02b3f21d3735d214c6"
)

# Cycle through every supported nonzero color count and both zero states.
# The first demonstration is always a witness separating the two settings.
PROFILE_SEQUENCE: tuple[tuple[int, bool], ...] = (
    (2, True),
    (3, False),
    (4, True),
    (2, False),
    (3, True),
    (4, False),
)
DIFFICULTY_SEQUENCE = ("easy", "medium", "hard", "medium", "hard", "easy")

_NONZERO_COLOR_EXPR = """(unique (filter (lambda (v) (!= v 0))
                                          (flatmap (lambda (r)
                                                     (map (lambda (c) (at g r c))
                                                          (range 0 w)))
                                                   (range 0 h))))"""
_ALL_COLOR_EXPR = """(unique (flatmap (lambda (r)
                             (map (lambda (c) (at g r c))
                                  (range 0 w)))
                           (range 0 h)))"""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_json(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _validate_seed(seed: int) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def _validate_setting(setting: str) -> str:
    if setting not in SETTINGS:
        raise ValueError(f"count_scope must be one of {SETTINGS}, got {setting!r}")
    return setting


def choose_setting(seed: int) -> str:
    """Choose one hidden setting deterministically for the complete episode."""
    _validate_seed(seed)
    return SETTINGS[seed % len(SETTINGS)]


def canonical_source(*, root: Path | str | None = None) -> str:
    """Read and content-bind the one canonical Racket program for this task."""
    if root is None:
        root = find_root(__file__)
    matches: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if not isinstance(program, str) or not program.strip():
                    raise ValueError(f"{TASK_ID}: canonical program_solution missing")
                matches.append(program)
    if len(matches) != 1:
        raise ValueError(
            f"{TASK_ID}: expected one canonical program, found {len(matches)}"
        )
    source = matches[0]
    digest = _sha256_bytes(source.encode("utf-8"))
    if digest != CANONICAL_RULE_SHA256:
        raise ValueError(
            f"{TASK_ID}: canonical rule hash drifted: {digest} != "
            f"{CANONICAL_RULE_SHA256}"
        )
    return source


def materialize_rule(
    setting: str,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    """Return an exact executable ``(rule! ...)`` program for one setting."""
    setting = _validate_setting(setting)
    canonical = canonical_source(root=root) if source is None else source
    if setting == DEFAULT_SETTING:
        return canonical
    occurrences = canonical.count(_NONZERO_COLOR_EXPR)
    if occurrences != 1:
        raise ValueError(
            "canonical rule no longer has the single expected nonzero-color expression"
        )
    alternative = canonical.replace(_NONZERO_COLOR_EXPR, _ALL_COLOR_EXPR, 1)
    if "(filter (lambda (v) (!= v 0))" in alternative:
        raise AssertionError("alternative rule still excludes zero")
    return alternative


def _rule_body(program: str) -> str:
    text = program.strip()
    if not text.startswith("(rule!") or not text.endswith(")"):
        raise ValueError("program must be a complete (rule! BODY) form")
    return text[len("(rule!") : -1].strip()


def _grid_literal(grid: list[list[int]]) -> str:
    normalized = normalize_grid(grid)
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in normalized)
    return f"'({rows})"


def apply_racket(bridge: Any, program: str, grid: list[list[int]]) -> list[list[int]]:
    """Execute one materialized rule in the protected persistent Racket bridge."""
    expression = f"({_rule_body(program)} {_grid_literal(grid)})"
    return normalize_grid(bridge.eval_text(expression))


def apply_python(grid: list[list[int]], setting: str) -> list[list[int]]:
    """Small independent mirror used for tests and Racket parity checks."""
    setting = _validate_setting(setting)
    source = normalize_grid(grid)
    colors = {value for row in source for value in row}
    if setting == "nonzero":
        colors.discard(0)
    factor = len(colors)
    if factor <= 1:
        return [row[:] for row in source]
    output: list[list[int]] = []
    for row in source:
        expanded = [value for value in row for _ in range(factor)]
        output.extend(expanded[:] for _ in range(factor))
    return output


def _validate_counts(train_count: int, test_count: int) -> tuple[int, int]:
    for name, count in (("train_count", train_count), ("test_count", test_count)):
        if type(count) is not int:
            raise TypeError(f"{name} must be an integer (not bool, float, or string)")
        if count < 1:
            raise ValueError(f"{name} must be positive")
    if train_count + test_count > MAX_EPISODE_PAIRS:
        raise ValueError(f"train_count + test_count must be at most {MAX_EPISODE_PAIRS}")
    return train_count, test_count


def build_input(
    seed: int,
    pair_index: int,
    *,
    attempt: int = 0,
    root: Path | str | None = None,
) -> list[list[int]]:
    """Draw one setting-independent candidate, retaining the pair's profile."""
    _validate_seed(seed)
    if type(pair_index) is not int or not 0 <= pair_index < MAX_EPISODE_PAIRS:
        raise ValueError(f"pair_index must be 0..{MAX_EPISODE_PAIRS - 1}")
    if type(attempt) is not int or not 0 <= attempt < MAX_DRAW_ATTEMPTS:
        raise ValueError(f"attempt must be 0..{MAX_DRAW_ATTEMPTS - 1}")
    if root is None:
        root = find_root(__file__)
    generator, _path, _digest = load_selected_generator(TASK_ID, root=root)
    profile_index = pair_index % len(PROFILE_SEQUENCE)
    color_count, zero_present = PROFILE_SEQUENCE[profile_index]
    # A collision retry varies layout/palette, never the hidden setting/profile.
    derived_seed = seed * 101 + 17 + attempt * 1_000_003
    return generator.generate(
        derived_seed,
        pair_index,
        difficulty=DIFFICULTY_SEQUENCE[profile_index],
        color_count=color_count,
        zero_present=zero_present,
    )


def _unique_inputs(
    seed: int, total: int, *, root: Path | str
) -> tuple[list[list[list[int]]], dict[str, Any]]:
    grids: list[list[list[int]]] = []
    seen: set[tuple[tuple[int, ...], ...]] = set()
    attempts: list[int] = []
    for pair_index in range(total):
        for attempt in range(MAX_DRAW_ATTEMPTS):
            grid = normalize_grid(build_input(seed, pair_index, attempt=attempt, root=root))
            key = tuple(map(tuple, grid))
            if key in seen:
                continue
            seen.add(key)
            grids.append(grid)
            attempts.append(attempt)
            break
        else:
            raise RuntimeError(
                f"could not draw a unique input for pair {pair_index} after "
                f"{MAX_DRAW_ATTEMPTS} attempts; requested {total} distinct inputs"
            )
    return grids, {
        "unique_inputs": len(seen),
        "draws": total + sum(attempts),
        "duplicate_rejections": sum(attempts),
        "accepted_attempts": attempts,
        "max_attempts_per_input": MAX_DRAW_ATTEMPTS,
    }


def _assess_query_identifiability(
    demonstrations: list[dict[str, Any]],
    predictions: dict[str, list[list[list[int]]]],
    selected: str,
) -> dict[str, Any]:
    """Fit settings on demos alone, then inspect each held-out prediction.

    Each predictions list is ordered as demos followed by query inputs. Query
    predictions never participate in the demo-consistency calculation.
    """
    selected = _validate_setting(selected)
    demo_count = len(demonstrations)
    lengths = {len(rows) for rows in predictions.values()}
    if set(predictions) != set(SETTINGS) or len(lengths) != 1:
        raise ValueError("predictions must cover every setting with equal pair counts")
    total = lengths.pop()
    if demo_count < 1 or total <= demo_count:
        raise ValueError("identifiability needs demonstrations and at least one query")
    refutations = {
        setting: [
            index for index, pair in enumerate(demonstrations)
            if predictions[setting][index] != pair["output"]
        ]
        for setting in SETTINGS
    }
    consistent = [setting for setting in SETTINGS if not refutations[setting]]
    if selected not in consistent:
        raise AssertionError("selected rule does not fit the demonstrations")
    rivals = {
        setting: {
            "fits_demonstrations": not refutations[setting],
            "refuting_demo_indices": refutations[setting],
        }
        for setting in SETTINGS if setting != selected
    }
    queries: list[dict[str, Any]] = []
    for query_index in range(total - demo_count):
        pair_index = demo_count + query_index
        query_rivals: dict[str, Any] = {}
        for setting, demo_check in rivals.items():
            agrees = predictions[setting][pair_index] == predictions[selected][pair_index]
            query_rivals[setting] = {
                "fits_demonstrations": demo_check["fits_demonstrations"],
                "agrees_with_selected": agrees,
                "ambiguous": demo_check["fits_demonstrations"] and not agrees,
            }
        queries.append({
            "query_index": query_index,
            "identified_from_demonstrations": not any(
                row["ambiguous"] for row in query_rivals.values()
            ),
            "rivals": query_rivals,
        })
    return {
        "candidate_settings": list(SETTINGS),
        "consistent_settings": consistent,
        "rivals": rivals,
        "queries": queries,
    }


def _diff_cells(left: list[list[int]], right: list[list[int]]) -> int:
    if len(left) != len(right) or len(left[0]) != len(right[0]):
        return -1
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def make_episode(
    seed: int,
    setting: str | None = None,
    *,
    train_count: int = DEFAULT_TRAIN_COUNT,
    test_count: int = DEFAULT_TEST_COUNT,
    root: Path | str | None = None,
    verify_racket: bool = True,
) -> dict[str, Any]:
    """Build independent demo/query counts under one fixed hidden setting.

    ``verify_racket=False`` is a unit-test convenience only; exported episodes
    always execute the exact program for every setting and input.
    """
    _validate_seed(seed)
    train_count, test_count = _validate_counts(train_count, test_count)
    selected = choose_setting(seed) if setting is None else _validate_setting(setting)
    root = Path(find_root(__file__) if root is None else root).resolve()
    total = train_count + test_count
    grids, sampling = _unique_inputs(seed, total, root=root)
    canonical = canonical_source(root=root)
    programs = {value: materialize_rule(value, source=canonical) for value in SETTINGS}
    predictions: dict[str, list[list[list[int]]]] = {}
    bridge = None
    try:
        if verify_racket:
            from arc_repl.racket_bridge import RacketBridge

            bridge = RacketBridge(max_calls_before_restart=64, timeout=30.0)
        for value in SETTINGS:
            predictions[value] = []
            for pair_index, grid in enumerate(grids):
                expected = apply_python(grid, value)
                actual = apply_racket(bridge, programs[value], grid) if bridge else expected
                if actual != expected:
                    raise AssertionError(
                        f"Racket/Python mismatch for {value=} {seed=} {pair_index=}"
                    )
                predictions[value].append(actual)
    finally:
        if bridge is not None:
            bridge.shutdown()

    pairs = [
        {"input": copy.deepcopy(grid), "output": copy.deepcopy(output)}
        for grid, output in zip(grids, predictions[selected])
    ]
    train, test = pairs[:train_count], pairs[train_count:]
    audit = _assess_query_identifiability(train, predictions, selected)
    if not all(row["identified_from_demonstrations"] for row in audit["queries"]):
        raise AssertionError("demonstrations leave at least one query ambiguous")
    rival = next(value for value in SETTINGS if value != selected)
    _generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    program = programs[selected]
    return {
        "schema": "arcpuzzles-parametric-count-scope-episode-v2",
        "train": train,
        "test": test,
        "program": program,
        "meta": {
            "task_id": TASK_ID,
            "seed": seed,
            PARAMETER_NAME: selected,
            "canonical_default": DEFAULT_SETTING,
            "prototype_version": PROTOTYPE_VERSION,
            "train_count": len(train),
            "test_count": len(test),
            "profile_sequence": [
                {"color_count": PROFILE_SEQUENCE[index % len(PROFILE_SEQUENCE)][0],
                 "zero_present": PROFILE_SEQUENCE[index % len(PROFILE_SEQUENCE)][1],
                 "difficulty": DIFFICULTY_SEQUENCE[index % len(PROFILE_SEQUENCE)]}
                for index in range(total)
            ],
            "sampling": sampling,
            "input_sha256": [_sha256_json(grid) for grid in grids],
            "program_sha256": _sha256_bytes(program.encode("utf-8")),
            "canonical_rule_sha256": CANONICAL_RULE_SHA256,
            "prototype_source_sha256": _sha256_bytes(Path(__file__).read_bytes()),
            "selected_generator": str(generator_path.relative_to(root)),
            "selected_generator_sha256": generator_sha,
            "racket_verified": verify_racket,
            "racket_evaluations": len(SETTINGS) * total if verify_racket else 0,
            "racket_evaluations_by_setting": {
                value: total if verify_racket else 0 for value in SETTINGS
            },
            "evaluated_program_sha256": {
                value: _sha256_bytes(text.encode("utf-8")) for value, text in programs.items()
            },
            "query_labels_racket_verified": test_count if verify_racket else 0,
            "query_identifiability": audit,
            "rival_setting": rival,
            "rival_diff_cells": [
                _diff_cells(selected_output, rival_output)
                for selected_output, rival_output in zip(predictions[selected], predictions[rival])
            ],
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Publish only demonstrations and query inputs under a generic schema."""
    return {
        "schema": "arcpuzzles-challenge-v1",
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_filename(episode: dict[str, Any]) -> str:
    """Identify visible challenge contents without exposing its hidden setting."""
    return f"challenge-{_sha256_json(public_challenge(episode))}.json"


def write_evidence(
    out_dir: Path,
    *,
    seeds: dict[str, int] | None = None,
    train_count: int = DEFAULT_TRAIN_COUNT,
    test_count: int = DEFAULT_TEST_COUNT,
) -> dict[str, Any]:
    """Materialize Racket-verified public/private examples for both settings."""
    train_count, test_count = _validate_counts(train_count, test_count)
    out_dir = Path(out_dir)
    if out_dir.exists():
        raise FileExistsError(f"choose a new output directory: {out_dir}")
    seeds = {"nonzero": 0, "all": 1} if seeds is None else dict(seeds)
    if set(seeds) != set(SETTINGS):
        raise ValueError(f"seeds must provide exactly {SETTINGS}")
    for setting, seed in seeds.items():
        _validate_seed(seed)
        if choose_setting(seed) != setting:
            raise ValueError(
                f"seed {seed} naturally selects {choose_setting(seed)!r}, not {setting!r}"
            )

    private_dir = out_dir / "private"
    public_dir = out_dir / "public"
    rules_dir = private_dir / "rules"
    episodes_dir = private_dir / "episodes"
    for directory in (rules_dir, episodes_dir, public_dir):
        directory.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    source_path = Path(__file__).resolve()
    _generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    records: dict[str, Any] = {}
    for setting in SETTINGS:
        episode = make_episode(
            seeds[setting], setting=setting, train_count=train_count, test_count=test_count,
            root=root, verify_racket=True,
        )
        public = public_challenge(episode)
        rule_path = rules_dir / f"{setting}.rkt"
        episode_path = episodes_dir / f"{setting}.json"
        public_path = public_dir / public_filename(episode)
        # Write exactly the executed bytes: an appended newline would invalidate
        # the source-bound program hash even though Racket tolerates whitespace.
        rule_bytes = episode["program"].encode("utf-8")
        rule_path.write_bytes(rule_bytes)
        episode_bytes = (json.dumps(episode, indent=2, sort_keys=True) + "\n").encode("utf-8")
        public_bytes = (json.dumps(public, indent=2, sort_keys=True) + "\n").encode("utf-8")
        episode_path.write_bytes(episode_bytes)
        public_path.write_bytes(public_bytes)
        audit = episode["meta"]["query_identifiability"]
        records[setting] = {
            "seed": seeds[setting],
            "rule": str(rule_path.relative_to(out_dir)),
            "rule_sha256": _sha256_bytes(rule_bytes),
            "private_episode": str(episode_path.relative_to(out_dir)),
            "private_episode_sha256": _sha256_json(episode),
            "private_episode_file_sha256": _sha256_bytes(episode_bytes),
            "public_challenge": str(public_path.relative_to(out_dir)),
            "public_challenge_sha256": _sha256_json(public),
            "public_challenge_file_sha256": _sha256_bytes(public_bytes),
            "actual_counts": {"train": len(episode["train"]), "test": len(episode["test"])},
            "unique_inputs": episode["meta"]["sampling"]["unique_inputs"],
            "duplicate_rejections": episode["meta"]["sampling"]["duplicate_rejections"],
            "racket_evaluations": episode["meta"]["racket_evaluations"],
            "query_labels_racket_verified": episode["meta"]["query_labels_racket_verified"],
            "query_identifiability": audit,
            "all_queries_identified_from_demonstrations": all(
                row["identified_from_demonstrations"] for row in audit["queries"]
            ),
            "rival_diff_cells": episode["meta"]["rival_diff_cells"],
            "demonstrations_refute_rival": all(
                not row["fits_demonstrations"] for row in audit["rivals"].values()
            ),
        }

    manifest = {
        "schema": "arcpuzzles-parametric-count-scope-evidence-v2",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": PARAMETER_NAME,
        "settings": list(SETTINGS),
        "canonical_default": DEFAULT_SETTING,
        "canonical_rule_sha256": CANONICAL_RULE_SHA256,
        "requested_counts": {"train": train_count, "test": test_count},
        "prototype_source": str(source_path.relative_to(root)),
        "prototype_source_sha256": _sha256_bytes(source_path.read_bytes()),
        "selected_generator": str(generator_path.relative_to(root)),
        "selected_generator_sha256": generator_sha,
        "label_authority": "protected Racket execution of each materialized rule",
        "production_path_modified": False,
        "public_boundary": "Only public/ is model-visible; evidence.json and private/ are private.",
        "racket_evaluations": sum(row["racket_evaluations"] for row in records.values()),
        "records": records,
        "limitations": [
            "This is a bounded authoring prototype, not an approved production rule.",
            "Only the two declared count scopes are checked; no universal rival completeness claim is made.",
            "Inputs retain the selected 3x3 domain with 2..4 nonzero colors; no large-grid support is claimed.",
            "Zero-free demonstrations alone do not distinguish the settings for zero-present queries.",
            f"Counts must be positive integers with at most {MAX_EPISODE_PAIRS} total pairs.",
            f"Unique sampling has at most {MAX_DRAW_ATTEMPTS} attempts per input and raises on exhaustion.",
        ],
    }
    (out_dir / "evidence.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--train", type=int, default=DEFAULT_TRAIN_COUNT, dest="train_count")
    parser.add_argument("--test", type=int, default=DEFAULT_TEST_COUNT, dest="test_count")
    parser.add_argument("--seed", type=int, default=0,
                        help="first seed of two consecutive seeds covering both settings")
    args = parser.parse_args(argv)
    _validate_seed(args.seed)
    seeds = {choose_setting(args.seed + offset): args.seed + offset for offset in range(len(SETTINGS))}
    manifest = write_evidence(
        args.out, seeds=seeds, train_count=args.train_count, test_count=args.test_count
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
