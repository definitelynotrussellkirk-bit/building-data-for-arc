"""Proposed episode-level priority-scan extension for generator 9000d0ea6484.

This authoring prototype leaves the selected generator and canonical Racket
rule contract unchanged.  It materializes a bounded family of exact Racket
rules, chooses one hidden setting once per episode, executes every label
through the public Racket bridge, and writes answer-masked public challenges
separately from private evidence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import traceback
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)


TASK_ID = "9000d0ea6484"
PROTOTYPE_VERSION = "1.0.0"
CANONICAL_PROGRAM_SHA256 = (
    "3bec9ede53940dce7bdf0aa83666b99ea3fb754cb6c4d356406e7eab30dade8c"
)
START_SECTIONS = (0, 1, 2, 3)
SCAN_DIRECTIONS = ("forward", "reverse")
DEFAULT_START_SECTION = 2
DEFAULT_SCAN_DIRECTION = "forward"
PRIORITY_BINDING = "(priority (list 2 3 0 1))"
SECTION_STARTS = (0, 5, 10, 15)
DIFFICULTIES = ("easy", "medium", "hard", None)


def sha256(raw: bytes | str) -> str:
    return hashlib.sha256(raw.encode() if isinstance(raw, str) else raw).hexdigest()


def grid_hash(grid: list[list[int]]) -> str:
    return sha256(json.dumps(grid, separators=(",", ":")))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    return seed


def _validate_parameters(start_section: Any, scan_direction: Any) -> tuple[int, str]:
    if type(start_section) is not int:
        raise TypeError("start_section must be an integer section index")
    if start_section not in START_SECTIONS:
        raise ValueError(f"start_section must be one of {START_SECTIONS}")
    if type(scan_direction) is not str:
        raise TypeError("scan_direction must be a string")
    if scan_direction not in SCAN_DIRECTIONS:
        raise ValueError(f"scan_direction must be one of {SCAN_DIRECTIONS}")
    return start_section, scan_direction


def all_settings() -> tuple[tuple[int, str], ...]:
    """Return the complete bounded parameter domain in a stable order."""
    return tuple(
        (start, direction)
        for direction in SCAN_DIRECTIONS
        for start in START_SECTIONS
    )


def priority_order(start_section: Any, scan_direction: Any) -> tuple[int, ...]:
    """Materialize a cyclic scan as one of the eight total orders on sections."""
    start, direction = _validate_parameters(start_section, scan_direction)
    step = 1 if direction == "forward" else -1
    return tuple((start + step * offset) % 4 for offset in range(4))


def choose_parameters(seed: Any) -> tuple[int, str]:
    """Choose one hidden setting once for the entire episode.

    The mapping is deliberately transparent and replayable.  Seeds 2 and 6
    share start section 2 while changing only scan direction, which gives a
    minimal default-versus-alternative evidence pair.
    """
    seed = _validate_seed(seed)
    return seed % 4, SCAN_DIRECTIONS[(seed // 4) % len(SCAN_DIRECTIONS)]


def canonical_rule(root: Path) -> str:
    """Read the exact selected canonical program from an explicit source tree."""
    matches: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    if len(matches) != 1:
        raise ValueError(f"Expected one canonical rule for {TASK_ID}; found {len(matches)}")
    return matches[0]


def materialize_rule(start_section: Any, scan_direction: Any, *, root: Path) -> str:
    """Return exact canonical bytes for the default or a guarded priority variant."""
    order = priority_order(start_section, scan_direction)
    source = canonical_rule(root)
    if sha256(source) != CANONICAL_PROGRAM_SHA256:
        raise ValueError("Canonical program bytes changed; review the pinned adapter")
    if source.count(PRIORITY_BINDING) != 1:
        raise ValueError("Canonical priority binding changed; review the prototype")
    if order == priority_order(DEFAULT_START_SECTION, DEFAULT_SCAN_DIRECTION):
        return source
    replacement = "(priority (list " + " ".join(map(str, order)) + "))"
    return source.replace(PRIORITY_BINDING, replacement, 1)


def racket_lambda(program: str) -> str:
    """Extract this task's already-lambda rule body for direct bridge execution."""
    body = strip_rule_wrapper(program).strip()
    if not body.startswith("(lambda"):
        raise ValueError("Expected the pinned task rule body to be a lambda")
    return body


def racket_application(program: str, grid: list[list[int]]) -> str:
    grid = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    return f"({racket_lambda(program)} {literal})"


def execute(
    bridge: RacketBridge, program: str, grid: list[list[int]]
) -> list[list[int]]:
    return normalize_grid(bridge.eval_text(racket_application(program, grid)))


def apply_python(grid: list[list[int]], order: Iterable[int]) -> list[list[int]]:
    """Independent Python oracle for the bounded priority family."""
    grid = normalize_grid(grid)
    if len(grid) != 4 or len(grid[0]) != 19:
        raise ValueError("priority prototype expects a 4x19 input")
    order = tuple(order)
    if len(order) != 4 or set(order) != set(START_SECTIONS):
        raise ValueError("order must be a permutation of sections 0..3")
    return [
        [
            next(
                (
                    grid[row][SECTION_STARTS[section] + col]
                    for section in order
                    if grid[row][SECTION_STARTS[section] + col] != 0
                ),
                0,
            )
            for col in range(4)
        ]
        for row in range(4)
    ]


def episode_inputs(seed: Any, *, root: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Generate four complete lessons from the selected, source-bound generator."""
    seed = _validate_seed(seed)
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    fixtures: list[dict[str, Any]] = []
    for sample_index, difficulty in enumerate(DIFFICULTIES):
        grid = normalize_grid(
            module.generate(seed, sample_index, difficulty=difficulty)
        )
        errors = module.self_check(grid, difficulty=difficulty)
        if errors:
            raise ValueError(
                f"selected generator rejected seed={seed} sample={sample_index}: {errors}"
            )
        fixtures.append(
            {
                "input": grid,
                "spec": {
                    "sample_index": sample_index,
                    "difficulty": difficulty,
                    "input_sha256": grid_hash(grid),
                    "observed_axes": module.observe_overrides(grid),
                },
            }
        )
    return fixtures, {
        "path": source_path.relative_to(root).as_posix(),
        "sha256": source_sha256,
    }


def _setting_record(setting: tuple[int, str]) -> dict[str, Any]:
    start, direction = setting
    return {
        "start_section": start,
        "scan_direction": direction,
        "priority_order": list(priority_order(start, direction)),
    }


def build_episode(seed: Any, *, root: Path, bridge: RacketBridge) -> dict[str, Any]:
    """Choose one hidden priority scan and label all pairs by executing Racket."""
    seed = _validate_seed(seed)
    selected = choose_parameters(seed)
    settings = all_settings()
    programs = {
        setting: materialize_rule(*setting, root=root) for setting in settings
    }
    fixtures, generator_source = episode_inputs(seed, root=root)

    outputs: dict[tuple[int, str], list[list[list[int]]]] = {
        setting: [] for setting in settings
    }
    execution_checks: list[dict[str, Any]] = []
    for pair_index, fixture in enumerate(fixtures):
        grid = fixture["input"]
        for setting in settings:
            order = priority_order(*setting)
            program = programs[setting]
            racket_output = execute(bridge, program, grid)
            python_output = apply_python(grid, order)
            outputs[setting].append(racket_output)
            execution_checks.append(
                {
                    "pair_index": pair_index,
                    "parameters": _setting_record(setting),
                    "program_sha256": sha256(program),
                    "application_sha256": sha256(racket_application(program, grid)),
                    "input_sha256": grid_hash(grid),
                    "output_sha256": grid_hash(racket_output),
                    "racket_matches_python": racket_output == python_output,
                }
            )

    selected_outputs = outputs[selected]
    labelled_pairs = [
        {"input": fixture["input"], "output": selected_outputs[index]}
        for index, fixture in enumerate(fixtures)
    ]

    rivals = [setting for setting in settings if setting != selected]
    pair_rival_checks: list[dict[str, Any]] = []
    for pair_index in range(len(fixtures)):
        refuted = [
            _setting_record(rival)
            for rival in rivals
            if outputs[rival][pair_index] != selected_outputs[pair_index]
        ]
        pair_rival_checks.append(
            {
                "pair_index": pair_index,
                "rivals_total": len(rivals),
                "rivals_refuted": len(refuted),
                "all_rivals_refuted": len(refuted) == len(rivals),
                "refuted_settings": refuted,
            }
        )

    query_rotations: list[dict[str, Any]] = []
    for query_index in range(len(fixtures)):
        demonstration_indices = [
            index for index in range(len(fixtures)) if index != query_index
        ]
        unresolved: list[dict[str, Any]] = []
        witnesses: dict[str, list[int]] = {}
        for rival in rivals:
            rival_key = f"{rival[0]}:{rival[1]}"
            witness_indices = [
                index
                for index in demonstration_indices
                if outputs[rival][index] != selected_outputs[index]
            ]
            witnesses[rival_key] = witness_indices
            if not witness_indices:
                unresolved.append(_setting_record(rival))
        query_rotations.append(
            {
                "query_index": query_index,
                "demonstration_indices": demonstration_indices,
                "rival_witness_indices": witnesses,
                "unresolved_rivals": unresolved,
                "identifiable": not unresolved,
            }
        )

    selected_program = programs[selected]
    return {
        "schema": "arcpuzzles-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": _setting_record(selected),
        "parameter_selection": (
            "start_section = seed % 4; scan_direction = "
            "('forward','reverse')[(seed // 4) % 2], chosen once per episode"
        ),
        "generator_source": generator_source,
        "program_sha256": sha256(selected_program),
        "program": selected_program,
        "labelled_pairs": labelled_pairs,
        "fixture_specs": [fixture["spec"] for fixture in fixtures],
        "execution_checks": execution_checks,
        "pair_rival_checks": pair_rival_checks,
        "query_rotations": query_rotations,
        "production_split": {
            "demonstration_indices": [0, 1, 2],
            "query_index": 3,
            "identifiable": query_rotations[3]["identifiable"],
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Expose demonstrations plus an input-only query, with hidden rule metadata."""
    labelled = episode["labelled_pairs"]
    return {
        "train": copy.deepcopy(labelled[:3]),
        "test": [{"input": copy.deepcopy(labelled[3]["input"])}],
    }


def _diff_cells(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    return [
        [row, col]
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    ]


def _validate_evidence_seeds(seeds: list[Any]) -> list[int]:
    if not isinstance(seeds, list) or not seeds:
        raise ValueError("seeds must be a nonempty list")
    checked = [_validate_seed(seed) for seed in seeds]
    if len(set(checked)) != len(checked):
        raise ValueError("seeds must be distinct")
    settings = {choose_parameters(seed) for seed in checked}
    default = (DEFAULT_START_SECTION, DEFAULT_SCAN_DIRECTION)
    if default not in settings:
        raise ValueError("evidence seeds must include the canonical default setting")
    if settings == {default}:
        raise ValueError("evidence seeds must include at least one alternative setting")
    return checked


def run_evidence(out: Path, seeds: list[Any]) -> dict[str, Any]:
    """Write reproducible private evidence and separately masked challenges."""
    root = find_root(__file__)
    checked_seeds = _validate_evidence_seeds(seeds)
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / "rules").mkdir()
    (out / "private").mkdir()
    (out / "public").mkdir()

    source_file = Path(__file__).resolve()
    source_paths = [
        source_file,
        source_file.with_name("README.md"),
        root / "generators" / TASK_ID / "tests" / "test_parametric.py",
    ]
    report: dict[str, Any] = {
        "schema": "arcpuzzles-task-parametric-prototype-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "proposed",
        "completion_state": "in_progress",
        "canonical_authority_changed": False,
        "seeds": checked_seeds,
        "parameter_contract": {
            "start_section": {
                "allowed_values": list(START_SECTIONS),
                "original_default": DEFAULT_START_SECTION,
            },
            "scan_direction": {
                "allowed_values": list(SCAN_DIRECTIONS),
                "original_default": DEFAULT_SCAN_DIRECTION,
            },
            "episode_scope": "one setting chosen before all four labels",
            "selection": (
                "start_section=seed%4; "
                "scan_direction=('forward','reverse')[(seed//4)%2]"
            ),
        },
        "input_contract": {
            "source": f"selected generators/{TASK_ID}/generator.py",
            "shape": [4, 19],
            "section_starts": list(SECTION_STARTS),
            "divider_columns": [4, 9, 14],
            "lesson_witnesses": (
                "empty, all four solos, and all six pairwise overlaps in every input"
            ),
        },
        "source_hashes": {
            path.relative_to(root).as_posix(): sha256(path.read_bytes())
            for path in source_paths
        },
        "limitations": [
            "This is a proposed authoring prototype, not a canonical rule update.",
            "The bounded domain covers cyclic scans only, not all 24 priority orders.",
            "Public challenge files intentionally omit hidden parameters and query outputs.",
        ],
    }

    try:
        canonical = canonical_rule(root)
        programs = {
            setting: materialize_rule(*setting, root=root)
            for setting in all_settings()
        }
        report["canonical_program_sha256"] = sha256(canonical)
        report["default_program_byte_identical"] = (
            programs[(DEFAULT_START_SECTION, DEFAULT_SCAN_DIRECTION)] == canonical
        )
        report["programs"] = {}
        for setting, program in programs.items():
            start, direction = setting
            filename = f"start_{start}_{direction}.rkt"
            (out / "rules" / filename).write_text(program, encoding="utf-8")
            report["programs"][f"{start}:{direction}"] = {
                **_setting_record(setting),
                "path": f"rules/{filename}",
                "sha256": sha256(program),
            }

        canonical_checks: list[dict[str, Any]] = []
        episodes: list[dict[str, Any]] = []
        with RacketBridge(timeout=20) as bridge:
            default_program = programs[
                (DEFAULT_START_SECTION, DEFAULT_SCAN_DIRECTION)
            ]
            for pair in canonical_pairs(TASK_ID, root=root):
                actual = execute(bridge, default_program, pair["input"])
                passed = actual == pair["output"]
                canonical_checks.append(
                    {
                        "variant": pair["variant"],
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "input_sha256": grid_hash(pair["input"]),
                        "expected_sha256": grid_hash(pair["output"]),
                        "actual_sha256": grid_hash(actual),
                        "passed": passed,
                    }
                )
            for seed in checked_seeds:
                episode = build_episode(seed, root=root, bridge=bridge)
                episodes.append(episode)
                write_json(out / "private" / f"episode_seed_{seed}.json", episode)
                write_json(
                    out / "public" / f"challenge_seed_{seed}.json",
                    public_challenge(episode),
                )
            report["racket_runtime"] = bridge.runtime_identity

        write_json(out / "canonical_checks.json", canonical_checks)

        default_episode = next(
            episode
            for episode in episodes
            if (
                episode["parameters"]["start_section"],
                episode["parameters"]["scan_direction"],
            )
            == (DEFAULT_START_SECTION, DEFAULT_SCAN_DIRECTION)
        )
        alternative_episode = next(
            episode
            for episode in episodes
            if (
                episode["parameters"]["start_section"],
                episode["parameters"]["scan_direction"],
            )
            != (DEFAULT_START_SECTION, DEFAULT_SCAN_DIRECTION)
        )
        witness_pair_index = 0
        witness_input = default_episode["labelled_pairs"][witness_pair_index]["input"]
        alternative_setting = (
            alternative_episode["parameters"]["start_section"],
            alternative_episode["parameters"]["scan_direction"],
        )
        with RacketBridge(timeout=20) as bridge:
            default_output = execute(
                bridge,
                programs[(DEFAULT_START_SECTION, DEFAULT_SCAN_DIRECTION)],
                witness_input,
            )
            alternative_output = execute(
                bridge,
                programs[alternative_setting],
                witness_input,
            )
        witness = {
            "input_source": {
                "seed": default_episode["seed"],
                "pair_index": witness_pair_index,
            },
            "input": witness_input,
            "default_parameters": _setting_record(
                (DEFAULT_START_SECTION, DEFAULT_SCAN_DIRECTION)
            ),
            "alternative_parameters": _setting_record(alternative_setting),
            "default_output": default_output,
            "alternative_output": alternative_output,
            "different_cells": _diff_cells(default_output, alternative_output),
            "different_cell_count": len(_diff_cells(default_output, alternative_output)),
            "belongs_to_prototype_domain": True,
        }
        write_json(out / "setting_difference_witness.json", witness)

        execution_checks = [
            row for episode in episodes for row in episode["execution_checks"]
        ]
        pair_checks = [
            row for episode in episodes for row in episode["pair_rival_checks"]
        ]
        rotations = [
            row for episode in episodes for row in episode["query_rotations"]
        ]
        distinct_settings = {
            (
                episode["parameters"]["start_section"],
                episode["parameters"]["scan_direction"],
            )
            for episode in episodes
        }
        report["counts"] = {
            "settings_materialized": len(programs),
            "distinct_programs": len(set(programs.values())),
            "episodes": len(episodes),
            "distinct_settings_demonstrated": len(distinct_settings),
            "unique_inputs": len(
                {
                    grid_hash(pair["input"])
                    for episode in episodes
                    for pair in episode["labelled_pairs"]
                }
            ),
            "racket_episode_label_executions": len(execution_checks),
            "racket_python_matches": sum(
                row["racket_matches_python"] for row in execution_checks
            ),
            "canonical_pairs": len(canonical_checks),
            "canonical_pairs_passed": sum(row["passed"] for row in canonical_checks),
            "canonical_pairs_failed": sum(not row["passed"] for row in canonical_checks),
            "pair_rival_checks": len(pair_checks),
            "pair_checks_refuting_all_rivals": sum(
                row["all_rivals_refuted"] for row in pair_checks
            ),
            "query_rotations": len(rotations),
            "rotations_identifiable": sum(row["identifiable"] for row in rotations),
        }
        report["private_episode_files"] = [
            f"private/episode_seed_{seed}.json" for seed in checked_seeds
        ]
        report["public_challenge_files"] = [
            f"public/challenge_seed_{seed}.json" for seed in checked_seeds
        ]
        report["passed"] = all(
            [
                report["default_program_byte_identical"],
                len(set(programs.values())) == len(programs),
                all(row["passed"] for row in canonical_checks),
                all(row["racket_matches_python"] for row in execution_checks),
                all(row["all_rivals_refuted"] for row in pair_checks),
                all(row["identifiable"] for row in rotations),
                len(distinct_settings) >= 2,
                bool(witness["different_cells"]),
            ]
        )
        report["completion_state"] = "complete"
    except Exception as exc:  # report blocked evidence instead of losing context
        report.update(
            passed=False,
            completion_state="blocked",
            error=str(exc),
            traceback=traceback.format_exc(),
        )

    write_json(out / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    parser.add_argument("--seeds", nargs="+", type=int, default=[2, 6])
    args = parser.parse_args()
    try:
        _validate_evidence_seeds(args.seeds)
    except (TypeError, ValueError) as exc:
        parser.error(str(exc))
    report = run_evidence(args.out, args.seeds)
    print(
        json.dumps(
            {
                key: report.get(key)
                for key in ("status", "completion_state", "passed", "counts", "error")
            },
            indent=2,
        )
    )
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
