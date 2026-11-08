#!/usr/bin/env python3
"""Task-local layer-order prototype for ARC task 3a4b67ab16ff.

The selected production generator and canonical Racket rule remain unchanged:
marker-color bounding boxes are intersected with the gray bounding rectangle,
and colors are painted in ascending numeric order.  This proposed prototype
adds one episode-level parameter, ``layer_order``.  Its alternate value paints
colors in descending order, so the lower color wins only where active
intersections overlap.

Every retained evidence label is executed by the bundled protected Racket
bridge.  The Python implementation is an independent mirror used for focused
tests and parity checks, not label authority.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
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

TASK_ID = "3a4b67ab16ff"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "layer_order"
ALLOWED_SETTINGS = ("ascending", "descending")
DEFAULT_SETTING = "ascending"
PARAMETER_SPEC = {
    "name": PARAMETER_NAME,
    "allowed": list(ALLOWED_SETTINGS),
    "default": DEFAULT_SETTING,
    "selection": "ALLOWED_SETTINGS[episode_seed % 2], chosen once per episode",
    "input_sampling": (
        "episode_seed // 2 selects inputs, so paired ascending/descending "
        "episodes use the same input distribution"
    ),
}
STATUS = "proposed task-local prototype; not production-approved"
ROOT = find_root(__file__)
HERE = Path(__file__).resolve().parent
_DESCENDING_SEQUENCE = "(list 9 8 7 6 5 4 3 2 1)"
_CANONICAL_SEQUENCE = "(range 1 10)"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _grid_sha256(grid: list[list[int]]) -> str:
    return _sha256_bytes(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _canonical_record(*, root: Path | str = ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    found = []
    with canonical_path(root).open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
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
    """Choose one hidden setting exactly once from an episode seed."""
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    return ALLOWED_SETTINGS[seed % len(ALLOWED_SETTINGS)]


@lru_cache(maxsize=8)
def _selected_generator_record(root_text: str):
    return load_selected_generator(TASK_ID, root=Path(root_text))


def selected_generator(root: Path | str = ROOT):
    """Return the selected production generator from one explicit source tree."""
    return _selected_generator_record(str(Path(root).resolve()))[0]


def program_for(setting: str = DEFAULT_SETTING, *, root: Path | str = ROOT) -> str:
    """Return the exact complete Racket program for one declared setting."""
    setting = _validate_setting(setting)
    canonical = _canonical_record(root=root)["program_solution"]
    if setting == DEFAULT_SETTING:
        return canonical
    if canonical.count(_CANONICAL_SEQUENCE) != 1:
        raise AssertionError(
            "canonical program must contain one unambiguous final color sequence"
        )
    return canonical.replace(_CANONICAL_SEQUENCE, _DESCENDING_SEQUENCE, 1)


def apply_python(
    grid: list[list[int]],
    setting: str = DEFAULT_SETTING,
    *,
    root: Path | str = ROOT,
) -> list[list[int]]:
    """Independent Python mirror for tests and Racket parity checks."""
    setting = _validate_setting(setting)
    generator = selected_generator(root)
    errors = generator._valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = generator._extract_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))

    output = [[0 for _ in row] for row in grid]
    for row, col in facts["gray_area"]:
        output[row][col] = 5
    colors = sorted(facts["colors"], reverse=(setting == "descending"))
    for color in colors:
        intersection = facts["colors"][color]["intersection"]
        for row, col in generator._rect_cells(intersection):
            output[row][col] = color
    return output


def _episode_inputs(
    seed: int,
    *,
    root: Path | str = ROOT,
    pair_count: int,
) -> tuple[list[list[int]], ...]:
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    if type(pair_count) is not int or not 2 <= pair_count <= 16:
        raise ValueError("pair_count must be an integer in 2..16")

    generator = selected_generator(root)
    # Paired seeds (0/1, 2/3, ...) share input sampling.  The hidden setting
    # therefore cannot influence which grids are shown.
    input_seed = (seed // len(ALLOWED_SETTINGS)) ^ 0x3A4B67AB
    grids: list[list[list[int]]] = []
    seen: set[str] = set()
    for sample_index in range(512):
        grid = generator.generate(
            input_seed,
            sample_index,
            difficulty="medium",
            scene_profile="overlap_priority",
        )
        analysis = generator._analysis(grid)
        if analysis["errors"] or analysis["scene_profile"] != "overlap_priority":
            raise AssertionError("selected generator returned an invalid overlap lesson")
        if apply_python(grid, "ascending", root=root) == apply_python(
            grid, "descending", root=root
        ):
            raise AssertionError("overlap lesson does not distinguish layer orders")
        digest = _grid_sha256(grid)
        if digest in seen:
            continue
        seen.add(digest)
        grids.append(grid)
        if len(grids) == pair_count:
            return tuple(grids)
    raise AssertionError(f"could not generate {pair_count} distinct overlap lessons")


def build_episode(
    seed: int,
    *,
    setting: str | None = None,
    root: Path | str = ROOT,
    demo_count: int = 3,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build a deterministic complete episode with mirror-generated labels.

    ``write_evidence`` re-executes and replaces every retained label with exact
    Racket output before materializing artifacts.
    """
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    selected = choose_setting(seed) if setting is None else _validate_setting(setting)
    if type(demo_count) is not int or not 1 <= demo_count <= 8:
        raise ValueError("demo_count must be an integer in 1..8")
    if type(query_count) is not int or not 1 <= query_count <= 8:
        raise ValueError("query_count must be an integer in 1..8")

    grids = _episode_inputs(
        seed,
        root=root,
        pair_count=demo_count + query_count,
    )
    pairs = [
        {
            "input": deepcopy(grid),
            "output": apply_python(grid, selected, root=root),
        }
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


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return a fresh public view: labeled demos and unlabeled query inputs."""
    return {
        "train": [
            {
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def public_filename(episode: dict[str, Any]) -> str:
    """Identify exactly the visible challenge, excluding all private fields."""
    return f"challenge-{public_challenge_id(public_challenge(episode))}.json"


def _assert_public_redaction(public: dict[str, Any]) -> None:
    # Also validate the precise public schema and grid types through the shared
    # canonical serializer used by the identifier.
    public_challenge_bytes(public)
    if any("output" in pair for pair in public["test"]):
        raise AssertionError("public challenge leaks a query answer")
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in (
        PARAMETER_NAME,
        "episode_seed",
        "rule!",
        '"program"',
        "query_answer",
    ):
        if forbidden in serialized:
            raise AssertionError(f"public challenge leaks {forbidden!r}")


def _callable_text(program: str) -> str:
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
    stream = iter(outputs)
    replaced = {
        "meta": deepcopy(episode["meta"]),
        "train": [
            {"input": deepcopy(pair["input"]), "output": next(stream)}
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"]), "output": next(stream)}
            for pair in episode["test"]
        ],
    }
    try:
        next(stream)
    except StopIteration:
        return replaced
    raise ValueError("too many outputs for episode")


def _endpoint_only_output(grid: list[list[int]], *, root: Path | str) -> list[list[int]]:
    """Known shortcut retained only as a split-extrema counterexample."""
    generator = selected_generator(root)
    facts = generator._extract_facts(grid)
    output = [[0 for _ in row] for row in grid]
    for row, col in facts["gray_area"]:
        output[row][col] = 5
    for color in sorted(facts["colors"]):
        cells = facts["colors"][color]["cells"]
        endpoint_bbox = generator._bbox((cells[0], cells[-1]))
        intersection = generator._intersection(endpoint_bbox, facts["gray_bbox"])
        for row, col in generator._rect_cells(intersection):
            output[row][col] = color
    return output


def write_evidence(
    out: Path | str,
    *,
    seeds: tuple[int, ...] | list[int] = (0, 1),
    demo_count: int = 3,
    query_count: int = 4,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    """Materialize exact-Racket public/private evidence for both settings."""
    out = Path(out)
    root = Path(root).resolve()
    if out.exists():
        raise FileExistsError(f"evidence output already exists: {out}")
    if not seeds or any(type(seed) is not int for seed in seeds):
        raise ValueError("seeds must be a non-empty sequence of integers")
    selected_settings = [choose_setting(seed) for seed in seeds]
    if len(seeds) != len(ALLOWED_SETTINGS) or set(selected_settings) != set(
        ALLOWED_SETTINGS
    ):
        raise ValueError(
            "seeds must select each declared setting exactly once; "
            f"got {selected_settings}"
        )
    if type(demo_count) is not int or not 1 <= demo_count <= 8:
        raise ValueError("demo_count must be an integer in 1..8")
    if type(query_count) is not int or not 1 <= query_count <= 8:
        raise ValueError("query_count must be an integer in 1..8")

    public_dir = out / "public"
    private_dir = out / "private"
    rules_dir = out / "rules"
    for folder in (public_dir, private_dir, rules_dir):
        folder.mkdir(parents=True, exist_ok=False)

    programs = {setting: program_for(setting, root=root) for setting in ALLOWED_SETTINGS}
    canonical_program = _canonical_record(root=root)["program_solution"]
    if programs[DEFAULT_SETTING] != canonical_program:
        raise AssertionError("default prototype program is not exact canonical authority")

    rule_records: dict[str, dict[str, Any]] = {}
    for setting, program in programs.items():
        path = rules_dir / f"layer-{setting}.rkt"
        path.write_text(program, encoding="utf-8")
        rule_records[setting] = {
            "path": str(path.relative_to(out)),
            "sha256": _sha256_file(path),
            "normalized_sha256": _sha256_bytes(" ".join(program.split()).encode()),
        }

    canonical_checks: list[dict[str, Any]] = []
    split_checks: list[dict[str, Any]] = []
    all_executions: list[dict[str, Any]] = []
    episode_summaries: dict[str, dict[str, Any]] = {}

    generator, generator_path, generator_sha256 = _selected_generator_record(str(root))
    with RacketBridge(max_calls_before_restart=128) as bridge:
        runtime_identity = bridge.runtime_identity

        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute_racket(bridge, programs[DEFAULT_SETTING], pair["input"])
            passed = actual == pair["output"]
            if not passed:
                raise AssertionError(
                    f"canonical Racket mismatch: {pair['split']} pair {pair['pair_index']}"
                )
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input_sha256": _grid_sha256(pair["input"]),
                    "passed": passed,
                }
            )

        for sample_index in range(4):
            grid = generator.generate(
                0x5EED3A4B,
                sample_index,
                difficulty="medium",
                scene_profile="split_extrema",
            )
            expected = generator.rule_mirror(grid)
            actual = execute_racket(bridge, programs[DEFAULT_SETTING], grid)
            mirror = apply_python(grid, DEFAULT_SETTING, root=root)
            shortcut = _endpoint_only_output(grid, root=root)
            facts = generator._analysis(grid)["facts"]
            color, = facts["active_colors"]
            cells = facts["colors"][color]["cells"]
            endpoint_bbox = generator._bbox((cells[0], cells[-1]))
            true_bbox = facts["colors"][color]["bbox"]
            if actual != expected or mirror != expected:
                raise AssertionError("split-extrema Racket/Python parity failed")
            if shortcut == expected or endpoint_bbox == true_bbox:
                raise AssertionError("split-extrema lesson did not refute endpoint shortcut")
            split_checks.append(
                {
                    "sample_index": sample_index,
                    "input_sha256": _grid_sha256(grid),
                    "racket_matches_generator": True,
                    "python_matches_generator": True,
                    "endpoint_bbox": list(endpoint_bbox),
                    "true_bbox": list(true_bbox),
                    "endpoint_shortcut_refuted": True,
                }
            )

        first_witness: dict[str, Any] | None = None
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
            if len({_grid_sha256(grid) for grid in grids}) != len(grids):
                raise AssertionError("episode contains duplicate inputs")

            predictions: dict[str, list[list[list[int]]]] = {}
            for setting in ALLOWED_SETTINGS:
                setting_outputs = []
                for pair_index, grid in enumerate(grids):
                    output = execute_racket(bridge, programs[setting], grid)
                    setting_outputs.append(output)
                    python_output = apply_python(grid, setting, root=root)
                    if output != python_output:
                        raise AssertionError(
                            f"Python/Racket mismatch: seed={seed} pair={pair_index} "
                            f"setting={setting}"
                        )
                    all_executions.append(
                        {
                            "episode_index": episode_index,
                            "episode_seed": seed,
                            "pair_index": pair_index,
                            PARAMETER_NAME: setting,
                            "application_sha256": _sha256_bytes(
                                application(programs[setting], grid).encode("utf-8")
                            ),
                            "output": output,
                        }
                    )
                predictions[setting] = setting_outputs

            selected_outputs = predictions[selected]
            racket_episode = _replace_episode_outputs(mirror_episode, selected_outputs)
            query_start = demo_count
            demo_disagreements = [
                index
                for index in range(demo_count)
                if predictions[selected][index] != predictions[rival][index]
            ]
            query_disagreements = [
                index - query_start
                for index in range(query_start, len(pairs))
                if predictions[selected][index] != predictions[rival][index]
            ]
            if len(demo_disagreements) != demo_count:
                raise AssertionError("every retained demo must distinguish layer order")
            if len(query_disagreements) != query_count:
                raise AssertionError("every retained query must distinguish layer order")

            public = public_challenge(racket_episode)
            _assert_public_redaction(public)
            public_path = public_dir / public_filename(racket_episode)
            _write_json(public_path, public)

            private_path = private_dir / f"episode-{selected}.json"
            private_record = {
                "schema": "3a4b67ab16ff-parametric-layer-order-episode-v1",
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
                    "distinct_inputs": len({_grid_sha256(grid) for grid in grids}),
                    "all_labels_executed_by_racket": True,
                    "python_mirror_parity": True,
                    "all_demos_distinguish_rival": (
                        len(demo_disagreements) == demo_count
                    ),
                    "all_queries_distinguish_rival": (
                        len(query_disagreements) == query_count
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
                "demo_count": demo_count,
                "query_count": query_count,
                "distinct_input_count": len(grids),
                "all_demos_distinguish_rival": True,
                "all_queries_distinguish_rival": True,
                "public_path": str(public_path.relative_to(out)),
                "public_sha256": _sha256_file(public_path),
                "private_path": str(private_path.relative_to(out)),
                "private_sha256": _sha256_file(private_path),
            }
            if first_witness is None:
                first_witness = {
                    "input": deepcopy(grids[-1]),
                    "outputs": {
                        setting: deepcopy(predictions[setting][-1])
                        for setting in ALLOWED_SETTINGS
                    },
                }

        if first_witness is None:
            raise AssertionError("no setting witness was generated")
        if first_witness["outputs"]["ascending"] == first_witness["outputs"][
            "descending"
        ]:
            raise AssertionError("setting witness does not distinguish layer orders")
        witness_path = private_dir / "setting-difference-witness.json"
        _write_json(
            witness_path,
            {
                "task_id": TASK_ID,
                **first_witness,
                "checked_by": "both complete Racket programs",
                "outputs_differ": True,
            },
        )

    canonical_checks_path = private_dir / "canonical-racket-checks.json"
    split_checks_path = private_dir / "split-extrema-racket-checks.json"
    executions_path = private_dir / "racket-executions.json"
    _write_json(canonical_checks_path, canonical_checks)
    _write_json(split_checks_path, split_checks)
    _write_json(executions_path, all_executions)

    source_paths = [
        Path(__file__).resolve(),
        HERE / "README.md",
        Path(generator_path),
        root / "generators" / TASK_ID / "tests" / "test_generator_3a4b67ab16ff.py",
        root / "generators" / TASK_ID / "tests" / "test_parametric_layer_order.py",
    ]
    report = {
        "schema": "3a4b67ab16ff-parametric-layer-order-v1",
        "status": "passed",
        "scope": STATUS,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": PARAMETER_SPEC,
        "invariant_reasoning": [
            "infer the gray bounding rectangle from all color-5 cells",
            "infer each other color bounding box from all of that color's markers",
            "restore the gray rectangle and clear the outside background",
            "fill each bbox intersection in one episode-fixed numeric color order",
            "only overlapping intersections reveal which numeric layer wins",
        ],
        "canonical_default_exact_program_match": True,
        "canonical_pairs_checked_with_default_racket": len(canonical_checks),
        "canonical_pairs_passed_with_default_racket": sum(
            row["passed"] for row in canonical_checks
        ),
        "canonical_checks": {
            "path": str(canonical_checks_path.relative_to(out)),
            "sha256": _sha256_file(canonical_checks_path),
        },
        "split_extrema": {
            "checked": len(split_checks),
            "all_racket_matches": all(
                row["racket_matches_generator"] for row in split_checks
            ),
            "endpoint_shortcut_refuted_count": sum(
                row["endpoint_shortcut_refuted"] for row in split_checks
            ),
            "path": str(split_checks_path.relative_to(out)),
            "sha256": _sha256_file(split_checks_path),
        },
        "programs": rule_records,
        "episodes": episode_summaries,
        "distinguishing_witness": {
            "path": str(witness_path.relative_to(out)),
            "sha256": _sha256_file(witness_path),
            "lawful_overlap_input": True,
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
            "The canonical production rule and its default ascending order are unchanged.",
            "Evidence covers the two declared settings and the retained paired seeds.",
            "All retained episode inputs use the production overlap_priority grammar.",
            "Finite rival checks do not exclude arbitrary alternative programs.",
        ],
        "passed": True,
    }
    _write_json(out / "report.json", report)
    _write_json(
        out / "manifest.json",
        {
            "schema": "3a4b67ab16ff-parametric-layer-order-manifest-v1",
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
    parser.add_argument("--demo-count", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=4)
    args = parser.parse_args(argv)
    report = write_evidence(
        args.out,
        seeds=tuple(args.seeds),
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "task_id": report["task_id"],
                "parameter": report["parameter"],
                "evidence": str(args.out),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
