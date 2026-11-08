#!/usr/bin/env python3
"""Task-local selector-role prototype for ARC task ef02aedbac38.

The selected production generator remains bound to the canonical rule: select
color-5 cells, paint them with the companion input color, and zero all other
cells.  This proposed prototype adds one episode-level setting, ``companion``,
that selects companion-color cells, paints them 5, and zeros the rest.

Every retained evidence label is executed by the bundled Racket bridge.  The
Python mirror exists only for focused tests and an independent parity check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "ef02aedbac38"
PROTOTYPE_VERSION = "1.1.0"
PARAMETER_NAME = "selector_role"
ALLOWED_SETTINGS = ("five", "companion")
DEFAULT_SETTING = "five"
DEFAULT_DEMO_COUNT = 3
DEFAULT_QUERY_COUNT = 4
PARAMETER_SPEC = {
    "name": PARAMETER_NAME,
    "allowed": list(ALLOWED_SETTINGS),
    "default": DEFAULT_SETTING,
    "selection": "ALLOWED_SETTINGS[episode_seed % 2], chosen once per episode",
}
STATUS = "proposed task-local prototype; not production-approved"
ROOT = find_root(__file__)
HERE = Path(__file__).resolve().parent

# This is a complete alternate authority, not a production rule replacement.
# It deliberately keeps the same two-color role inference and zero background.
_COMPANION_PROGRAM = """(rule! (lambda (g)
         (cellmap g (r c v) (if (!= v 5) 5 0))))"""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _canonical_record(*, root: Path | str = ROOT) -> dict[str, Any]:
    root = Path(root)
    found = []
    with canonical_path(root).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                found.append(row)
    if len(found) != 1:
        raise ValueError(f"expected one canonical task {TASK_ID}, found {len(found)}")
    return found[0]


def _validate_setting(setting: Any) -> str:
    if type(setting) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a string")
    if setting not in ALLOWED_SETTINGS:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}, got {setting!r}"
        )
    return setting


def choose_setting(seed: int) -> str:
    """Choose the hidden rule exactly once from an episode seed."""
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    return ALLOWED_SETTINGS[seed % len(ALLOWED_SETTINGS)]


def program_for(setting: str = DEFAULT_SETTING, *, root: Path | str = ROOT) -> str:
    """Return the exact complete Racket program for one declared setting."""
    setting = _validate_setting(setting)
    if setting == DEFAULT_SETTING:
        return _canonical_record(root=root)["program_solution"]
    return _COMPANION_PROGRAM


def _companion_color(grid: list[list[int]]) -> int:
    if not isinstance(grid, list) or not grid or not all(
        isinstance(row, list) and row for row in grid
    ):
        raise ValueError("grid must be a non-empty list of non-empty rows")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    values = {value for row in grid for value in row}
    companions = values - {5}
    if 5 not in values or len(companions) != 1:
        raise ValueError("prototype input must contain exactly color 5 and one companion")
    companion = next(iter(companions))
    if type(companion) is not int or companion not in (1, 2, 3, 4, 6, 7, 8, 9):
        raise ValueError("companion must be a legal nonzero ARC color other than 5")
    return companion


def apply_python(grid: list[list[int]], setting: str = DEFAULT_SETTING) -> list[list[int]]:
    """Independent mirror used only for tests and Racket parity checks."""
    setting = _validate_setting(setting)
    companion = _companion_color(grid)
    if setting == "five":
        selected, paint = 5, companion
    else:
        selected, paint = companion, 5
    return [
        [paint if value == selected else 0 for value in row]
        for row in grid
    ]


def _validate_episode_counts(demo_count: Any, query_count: Any) -> tuple[int, int]:
    if type(demo_count) is not int or not 1 <= demo_count <= 8:
        raise ValueError("demo_count must be an integer in 1..8")
    if type(query_count) is not int or not 1 <= query_count <= 4:
        raise ValueError("query_count must be an integer in 1..4")
    return demo_count, query_count


def _episode_inputs(
    seed: int,
    *,
    root: Path | str = ROOT,
    pair_count: int = 4,
) -> tuple[list[list[int]], ...]:
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    if type(pair_count) is not int or not 2 <= pair_count <= 12:
        raise ValueError("pair_count must be an integer in 2..12")
    generator, _, _ = load_selected_generator(TASK_ID, root=Path(root))
    # Input sampling is independent of the hidden rule.  A fixed xor namespace
    # avoids accidentally treating the small episode seed as a curriculum cue.
    input_seed = seed ^ 0xEF02AED
    return tuple(
        generator.generate(
            input_seed,
            sample_index,
            difficulty="medium",
        )
        for sample_index in range(pair_count)
    )


def build_episode(
    seed: int,
    *,
    setting: str | None = None,
    root: Path | str = ROOT,
    demo_count: int = DEFAULT_DEMO_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
) -> dict[str, Any]:
    """Build a deterministic complete episode using the independent mirror.

    ``write_evidence`` re-executes and replaces every retained label with Racket
    output before writing artifacts.  Keeping this function pure makes the
    parameter contract easy to test without starting the Racket process.
    """
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    if setting is None:
        selected = choose_setting(seed)
    else:
        selected = _validate_setting(setting)
    demo_count, query_count = _validate_episode_counts(demo_count, query_count)
    grids = _episode_inputs(
        seed,
        root=root,
        pair_count=demo_count + query_count,
    )
    pairs = [
        {"input": grid, "output": apply_python(grid, selected)}
        for grid in grids
    ]
    return {
        "meta": {
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "episode_seed": seed,
            PARAMETER_NAME: selected,
        },
        "train": pairs[:demo_count],
        "test": pairs[demo_count:],
    }


def public_filename(episode: dict[str, Any]) -> str:
    """Content-address the exact visible demonstrations and query inputs."""
    return f"challenge-{public_challenge_id(public_challenge(episode))}.json"


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return only demonstrations and unlabeled query inputs."""
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def _callable_text(program: str) -> str:
    # ``strip_rule_wrapper`` removes only the outer ``rule!`` form and already
    # returns the complete callable lambda.  Wrapping it again would evaluate
    # to a procedure instead of applying the rule to the grid.
    return strip_rule_wrapper(program)


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def application(program: str, grid: list[list[int]]) -> str:
    return f"({_callable_text(program)} {_grid_literal(grid)})"


def execute_racket(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    return bridge.eval_text(application(program, grid))


def _replace_episode_outputs(
    episode: dict[str, Any],
    outputs: Iterable[list[list[int]]],
) -> dict[str, Any]:
    outputs = iter(outputs)
    return {
        "meta": dict(episode["meta"]),
        "train": [
            {"input": pair["input"], "output": next(outputs)}
            for pair in episode["train"]
        ],
        "test": [
            {"input": pair["input"], "output": next(outputs)}
            for pair in episode["test"]
        ],
    }


def _assert_public_redaction(public: dict[str, Any]) -> None:
    if any("output" in pair for pair in public["test"]):
        raise AssertionError("public challenge leaks a query answer")
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in (
        PARAMETER_NAME,
        "rule!",
        '"program"',
        "query_answer",
        "episode_seed",
    ):
        if forbidden in serialized:
            raise AssertionError(f"public challenge leaks {forbidden!r}")


def write_evidence(
    out: Path | str,
    *,
    seeds: tuple[int, ...] | list[int] = (0, 1),
    demo_count: int = DEFAULT_DEMO_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    """Materialize Racket-verified public/private evidence for both settings."""
    demo_count, query_count = _validate_episode_counts(demo_count, query_count)
    if not seeds or any(type(seed) is not int for seed in seeds):
        raise ValueError("seeds must be a non-empty sequence of integers")
    selected_settings = [choose_setting(seed) for seed in seeds]
    if (
        len(selected_settings) != len(ALLOWED_SETTINGS)
        or sorted(selected_settings) != sorted(ALLOWED_SETTINGS)
    ):
        raise ValueError(
            f"seeds must select each setting exactly once; got {selected_settings}"
        )

    out = Path(out)
    root = Path(root)
    if out.exists():
        raise FileExistsError(f"evidence output already exists: {out}")

    public_dir = out / "public"
    private_dir = out / "private"
    rules_dir = out / "rules"
    for folder in (public_dir, private_dir, rules_dir):
        folder.mkdir(parents=True, exist_ok=False)

    programs = {setting: program_for(setting, root=root) for setting in ALLOWED_SETTINGS}
    canonical_program = _canonical_record(root=root)["program_solution"]
    if programs[DEFAULT_SETTING] != canonical_program:
        raise AssertionError("default prototype program is not exact canonical authority")

    rule_records: dict[str, Any] = {}
    for setting, program in programs.items():
        path = rules_dir / f"selector-{setting}.rkt"
        path.write_text(program, encoding="utf-8")
        rule_records[setting] = {
            "path": str(path.relative_to(out)),
            "sha256": _sha256_file(path),
            "text": program,
        }

    episode_summaries: dict[str, Any] = {}
    canonical_checks: list[dict[str, Any]] = []
    all_executions: list[dict[str, Any]] = []
    with RacketBridge(max_calls_before_restart=128) as bridge:
        runtime_identity = bridge.runtime_identity

        for pair_index, pair in enumerate(
            canonical_pairs(TASK_ID, root=root, labeled_only=True)
        ):
            actual = execute_racket(
                bridge,
                programs[DEFAULT_SETTING],
                pair["input"],
            )
            if actual != pair["output"]:
                raise AssertionError(f"canonical default failed pair {pair_index}")
            canonical_checks.append(
                {
                    "pair_index": pair_index,
                    "expected": pair["output"],
                    "actual": actual,
                    "input_sha256": _sha256_bytes(
                        json.dumps(pair["input"], sort_keys=True).encode()
                    ),
                }
            )
        _write_json(private_dir / "canonical-checks.json", canonical_checks)

        for episode_index, seed in enumerate(seeds):
            selected = choose_setting(seed)
            rival = next(value for value in ALLOWED_SETTINGS if value != selected)
            mirror_episode = build_episode(
                seed,
                setting=selected,
                root=root,
                demo_count=demo_count,
                query_count=query_count,
            )
            pairs = mirror_episode["train"] + mirror_episode["test"]
            grids = [pair["input"] for pair in pairs]
            input_fingerprints = [
                _sha256_bytes(
                    json.dumps(grid, sort_keys=True, separators=(",", ":")).encode(
                        "utf-8"
                    )
                )
                for grid in grids
            ]
            all_episode_inputs_distinct = len(set(input_fingerprints)) == len(
                input_fingerprints
            )
            if not all_episode_inputs_distinct:
                raise AssertionError("episode demonstrations and queries must be distinct")
            predictions: dict[str, list[list[list[int]]]] = {}

            for setting in ALLOWED_SETTINGS:
                setting_outputs = []
                for pair_index, grid in enumerate(grids):
                    output = execute_racket(bridge, programs[setting], grid)
                    setting_outputs.append(output)
                    all_executions.append(
                        {
                            "episode_index": episode_index,
                            "episode_seed": seed,
                            "pair_index": pair_index,
                            PARAMETER_NAME: setting,
                            "application_sha256": _sha256_bytes(
                                application(programs[setting], grid).encode()
                            ),
                            "output": output,
                        }
                    )
                    python_output = apply_python(grid, setting)
                    if output != python_output:
                        raise AssertionError(
                            f"Python/Racket mismatch: seed={seed} pair={pair_index} "
                            f"setting={setting}"
                        )
                predictions[setting] = setting_outputs

            selected_outputs = predictions[selected]
            racket_episode = _replace_episode_outputs(
                mirror_episode,
                selected_outputs,
            )
            demo_disagreements = [
                index
                for index in range(len(racket_episode["train"]))
                if predictions[selected][index] != predictions[rival][index]
            ]
            query_start = len(racket_episode["train"])
            query_disagreements = [
                index - query_start
                for index in range(query_start, len(pairs))
                if predictions[selected][index] != predictions[rival][index]
            ]
            if not demo_disagreements:
                raise AssertionError("demonstrations do not identify selector role")
            if len(query_disagreements) != len(racket_episode["test"]):
                raise AssertionError("a retained query does not distinguish selector roles")

            public = public_challenge(racket_episode)
            _assert_public_redaction(public)
            public_path = public_dir / public_filename(racket_episode)
            public_bytes = public_challenge_bytes(public)
            if public_path.exists():
                raise ValueError(f"duplicate public challenge: {public_path.name}")
            public_path.write_bytes(public_bytes)
            if _sha256_bytes(public_bytes) != public_path.stem.removeprefix("challenge-"):
                raise AssertionError("public filename does not hash the exact written bytes")

            private_path = private_dir / f"episode-{selected}.json"
            private_record = {
                "schema": "ef02aedbac38-parametric-selector-role-episode-v1",
                "status": STATUS,
                "task_id": TASK_ID,
                "episode_index": episode_index,
                "episode_seed": seed,
                "parameter": PARAMETER_SPEC,
                "selected_setting": selected,
                "rival_setting": rival,
                "selected_program": rule_records[selected],
                "rival_program": rule_records[rival],
                "episode": racket_episode,
                "racket_predictions": predictions,
                "query_answers": selected_outputs[query_start:],
                "checks": {
                    "setting_chosen_once": True,
                    "demo_count": len(racket_episode["train"]),
                    "query_count": len(racket_episode["test"]),
                    "requested_counts_match": (
                        len(racket_episode["train"]) == demo_count
                        and len(racket_episode["test"]) == query_count
                    ),
                    "all_episode_inputs_distinct": all_episode_inputs_distinct,
                    "all_labels_executed_by_racket": True,
                    "python_mirror_parity": True,
                    "demonstrations_distinguish_rival": bool(demo_disagreements),
                    "queries_distinguish_rival": (
                        len(query_disagreements) == len(racket_episode["test"])
                    ),
                },
                "demonstration_disagreement_indices": demo_disagreements,
                "query_disagreement_indices": query_disagreements,
            }
            _write_json(private_path, private_record)

            episode_summaries[selected] = {
                "episode_seed": seed,
                "selected_setting": selected,
                "rival_setting": rival,
                "public_path": str(public_path.relative_to(out)),
                "public_sha256": _sha256_file(public_path),
                "private_path": str(private_path.relative_to(out)),
                "private_sha256": _sha256_file(private_path),
                "demonstration_disagreement_indices": demo_disagreements,
                "query_disagreement_indices": query_disagreements,
                "demo_count": len(racket_episode["train"]),
                "query_count": len(racket_episode["test"]),
            }

        witness_input = canonical_pairs(
            TASK_ID, root=root, labeled_only=True
        )[0]["input"]
        witness_outputs = {
            setting: execute_racket(bridge, program, witness_input)
            for setting, program in programs.items()
        }
        if witness_outputs[ALLOWED_SETTINGS[0]] == witness_outputs[ALLOWED_SETTINGS[1]]:
            raise AssertionError("shared witness does not distinguish selector roles")
        witness_path = private_dir / "setting-difference-witness.json"
        _write_json(
            witness_path,
            {
                "task_id": TASK_ID,
                "input": witness_input,
                "outputs": witness_outputs,
                "checked_by": "both complete Racket programs",
                "outputs_differ": True,
            },
        )

    executions_path = private_dir / "racket-executions.json"
    _write_json(executions_path, all_executions)

    _, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    source_paths = [
        Path(__file__).resolve(),
        HERE / "README.md",
        Path(generator_path),
        root / "generators" / TASK_ID / "tests" / "test_parametric_selector_role.py",
        root / "generators" / TASK_ID / "tests" / "test_parametric_public_names.py",
    ]
    report = {
        "schema": "ef02aedbac38-parametric-selector-role-v1",
        "status": "passed",
        "scope": STATUS,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": PARAMETER_SPEC,
        "episode_shape": {
            "demo_count": demo_count,
            "query_count": query_count,
        },
        "input_constraints": (
            "unchanged production grammar: rectangular two-color {5, X} grids "
            "with both roles nontrivial and spatially distributed"
        ),
        "invariant_reasoning": [
            "identify literal color 5 and the sole companion color",
            "choose one episode-fixed color role as the mask",
            "paint selected cells with the opposite role color",
            "write 0 everywhere else",
        ],
        "canonical_default_exact_program_match": True,
        "canonical_pairs_checked_with_default_racket": len(canonical_checks),
        "canonical_pairs_passed_with_default_racket": len(canonical_checks),
        "programs": rule_records,
        "episodes": episode_summaries,
        "distinguishing_witness": {
            "path": str(witness_path.relative_to(out)),
            "sha256": _sha256_file(witness_path),
            "lawful_input": True,
            "outputs_differ": True,
        },
        "racket_execution_log": {
            "path": str(executions_path.relative_to(out)),
            "sha256": _sha256_file(executions_path),
            "count": len(all_executions),
        },
        "racket_runtime": runtime_identity,
        "selected_generator": {
            "path": str(Path(generator_path).relative_to(root)),
            "sha256": generator_sha256,
        },
        "source_hashes": {
            str(path.relative_to(root)): _sha256_file(path)
            for path in source_paths
        },
        "command": {
            "cwd": os.getcwd(),
            "argv": [sys.executable, *sys.argv],
        },
        "limitations": [
            "This is a task-local proposed prototype, not a production API or approval.",
            "Evidence covers only the two declared settings and retained episode seeds.",
            "Finite checks against the declared parameter rival do not exclude arbitrary programs.",
            "The companion setting changes the selected color role but preserves the family structure.",
        ],
        "passed": True,
    }
    _write_json(out / "report.json", report)
    _write_json(
        out / "manifest.json",
        {
            "schema": "ef02aedbac38-parametric-selector-role-manifest-v1",
            "report": "report.json",
            "report_sha256": _sha256_file(out / "report.json"),
            "files": {
                str(path.relative_to(out)): _sha256_file(path)
                for path in sorted(out.rglob("*"))
                if path.is_file() and path.name != "manifest.json"
            },
        },
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--demo-count", type=int, default=DEFAULT_DEMO_COUNT)
    parser.add_argument("--query-count", type=int, default=DEFAULT_QUERY_COUNT)
    args = parser.parse_args(argv)
    report = write_evidence(
        args.out,
        seeds=args.seeds,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "task_id": report["task_id"],
                "parameter": report["parameter"],
                "episode_shape": report["episode_shape"],
                "evidence": str(args.out),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
