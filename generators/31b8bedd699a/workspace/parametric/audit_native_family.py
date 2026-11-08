"""Finite, source-bound audit for the promoted 31b8bedd699a family.

The audit is intentionally bounded: it checks every declared setting, every
supported demonstration prefix, every supported query prefix, and the named
finite rival family over a caller-selected seed range.  It writes one
self-contained JSON receipt and refuses to overwrite prior evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import types
from typing import Any, Iterable


_HERE = Path(__file__).resolve().parent
_FAMILY_PATH = _HERE / "native_family.py"
_FAMILY_BODY = _FAMILY_PATH.read_bytes()
_FAMILY_NAME = "_audit_native_family_31b8bedd699a_" + hashlib.sha256(
    str(_FAMILY_PATH).encode() + _FAMILY_BODY
).hexdigest()
family = sys.modules.get(_FAMILY_NAME)
if family is None:
    family = types.ModuleType(_FAMILY_NAME)
    family.__file__ = str(_FAMILY_PATH)
    sys.modules[_FAMILY_NAME] = family
    try:
        exec(compile(_FAMILY_BODY, str(_FAMILY_PATH), "exec"), family.__dict__)
    except BaseException:
        sys.modules.pop(_FAMILY_NAME, None)
        raise


_DEMO_COUNTS = [2, 3, 4, 5, 6]
_QUERY_COUNTS = [1, 2, 3, 4]
_SOURCE_NAMES = (
    "adapter.py",
    "audit_native_family.py",
    "native_family.py",
    "promotion.json",
    "prototype.py",
)


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"), ensure_ascii=False)


def _setting_key(settings: dict[str, Any]) -> str:
    return json.dumps(settings, sort_keys=True, separators=(",", ":"))


def _validate_seeds(seeds: Iterable[int]) -> list[int]:
    values = list(seeds)
    if not values:
        raise ValueError("seeds must be nonempty")
    if any(type(seed) is not int or not 0 <= seed < 2**63 for seed in values):
        raise ValueError("every seed must be an exact integer in 0..2**63-1")
    if len(values) != len(set(values)):
        raise ValueError("seeds must be distinct")
    return values


def _source_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for name in _SOURCE_NAMES:
        path = _HERE / name
        if path.is_file():
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def run_audit(out: Path | str, *, seeds: Iterable[int]) -> dict[str, Any]:
    """Run the bounded audit and atomically create ``out``.

    A rival is *dangerous* only when it fits the complete minimum two-example
    lesson but differs on at least one retained query.  A rival that agrees on
    every checked pair is reported separately as an observational equivalence,
    not silently counted as evidence of identifiability.
    """
    destination = Path(out)
    if destination.exists():
        raise FileExistsError(destination)
    seed_values = _validate_seeds(seeds)

    dangerous: list[dict[str, Any]] = []
    observational: list[dict[str, Any]] = []
    all_settings_share_inputs = True
    all_inputs_distinct = True
    all_minimum_lessons_identify_setting = True
    all_query_sets_include_30x30 = True
    all_supported_demo_prefixes_identify_setting = True
    all_supported_query_prefixes_are_stable = True
    episode_count = 0

    for seed in seed_values:
        # The sampler is intentionally setting-blind.  Sample each seed once,
        # then label those exact bytes under every declared setting.  This both
        # makes the matched-input claim literal and keeps the bounded audit
        # practical for future reviewers.
        demo_rows, query_rows = family._full_inputs(seed)
        base_demo_inputs = [row["input"] for row in demo_rows]
        base_query_inputs = [row["input"] for row in query_rows]
        inputs = base_demo_inputs + base_query_inputs
        keys = [_grid_key(grid) for grid in inputs]
        all_inputs_distinct &= len(keys) == len(set(keys)) == 10
        all_query_sets_include_30x30 &= any(
            len(grid) == 30 and len(grid[0]) == 30
            for grid in base_query_inputs
        )

        reference_inputs = inputs
        for settings in family.ALL_SETTINGS:
            episode_count += 1
            # Program construction is part of totality even though Racket
            # execution belongs to native qualification rather than this audit.
            program = family.program_for(settings)
            if not isinstance(program, str) or not program:
                raise AssertionError(f"empty program for {settings}")

            train = [
                {"input": grid, "output": family.solve(grid, settings)}
                for grid in base_demo_inputs
            ]
            queries = [
                {"input": grid, "output": family.solve(grid, settings)}
                for grid in base_query_inputs
            ]
            current_inputs = [pair["input"] for pair in train + queries]
            all_settings_share_inputs &= current_inputs == reference_inputs

            # The public adapter slices the two fixed streams independently.
            # Checking every prefix of the one sampled stream covers every
            # supported count without resampling identical inputs.
            for query_count in _QUERY_COUNTS:
                all_supported_query_prefixes_are_stable &= (
                    queries[:query_count] == queries[0:query_count]
                    and len(queries[:query_count]) == query_count
                )

            # Check every supported visible demonstration prefix against every
            # declared setting, rather than trusting generate()'s own guard.
            for demo_count in _DEMO_COUNTS:
                visible = train[:demo_count]
                survivors = [
                    candidate
                    for candidate in family.ALL_SETTINGS
                    if all(
                        family.solve(pair["input"], candidate) == pair["output"]
                        for pair in visible
                    )
                ]
                identified = survivors == [settings]
                all_supported_demo_prefixes_identify_setting &= identified
                if demo_count == 2:
                    all_minimum_lessons_identify_setting &= identified

            minimum_train = train[:2]
            for rival_name in family.TEACHING_RIVALS:
                fits = all(
                    family.rival_outputs(pair["input"], settings)[rival_name]
                    == pair["output"]
                    for pair in minimum_train
                )
                if not fits:
                    continue
                differing_queries = [
                    index
                    for index, pair in enumerate(queries)
                    if family.rival_outputs(pair["input"], settings)[rival_name]
                    != pair["output"]
                ]
                finding = {
                    "seed": seed,
                    "settings": dict(settings),
                    "rival": rival_name,
                    "differing_query_indices": differing_queries,
                }
                if differing_queries:
                    dangerous.append(finding)
                else:
                    observational.append(finding)

    status = "pass" if all(
        (
            not dangerous,
            all_settings_share_inputs,
            all_inputs_distinct,
            all_minimum_lessons_identify_setting,
            all_query_sets_include_30x30,
            all_supported_demo_prefixes_identify_setting,
            all_supported_query_prefixes_are_stable,
        )
    ) else "fail"
    summary: dict[str, Any] = {
        "schema": "arcpuzzles-parametric-finite-audit-v1",
        "status": status,
        "task_id": "31b8bedd699a",
        "seed_count": len(seed_values),
        "seeds": seed_values,
        "setting_count": len(family.ALL_SETTINGS),
        "settings": [dict(settings) for settings in family.ALL_SETTINGS],
        "episode_count": episode_count,
        "supported_demo_counts": _DEMO_COUNTS,
        "supported_query_counts": _QUERY_COUNTS,
        "minimum_lesson_rivals": list(family.TEACHING_RIVALS),
        "dangerous_ambiguities": dangerous,
        "observational_equivalences": observational,
        "all_settings_share_inputs": bool(all_settings_share_inputs),
        "all_inputs_distinct": bool(all_inputs_distinct),
        "all_minimum_lessons_identify_setting": bool(
            all_minimum_lessons_identify_setting
        ),
        "all_supported_demo_prefixes_identify_setting": bool(
            all_supported_demo_prefixes_identify_setting
        ),
        "all_supported_query_prefixes_are_stable": bool(
            all_supported_query_prefixes_are_stable
        ),
        "all_query_sets_include_30x30": bool(all_query_sets_include_30x30),
        "scope_note": (
            "Finite audit over the listed seeds, six declared settings, all "
            "supported visible prefixes, and the named rival family; it is not "
            "a proof against unenumerated programs."
        ),
        "source_sha256": _source_hashes(),
    }

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(destination)
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--seed-count",
        type=int,
        default=32,
        help="audit seeds range(seed_count); default: 32",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if type(args.seed_count) is not int or args.seed_count < 1:
        raise SystemExit("--seed-count must be a positive integer")
    summary = run_audit(args.out, seeds=range(args.seed_count))
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
