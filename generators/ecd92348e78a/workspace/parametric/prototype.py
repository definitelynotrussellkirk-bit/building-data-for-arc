#!/usr/bin/env python3
"""Runnable two-axis rule-family prototype for ARC task ecd92348e78a.

The selected production rule is the canonical default:
``sort_order=descending`` and ``bar_alignment=top``.  This prototype keeps
input generation unchanged and chooses the two rule parameters once per
lesson, then executes the matching Racket program to label every pair.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid


TASK_ID = "ecd92348e78a"
SCHEMA = "arcpuzzles-parametric-bar-chart-v1"
PUBLIC_SCHEMA = "arcpuzzles-parametric-public-v1"
DEFAULT_PARAMETERS = {
    "sort_order": "descending",
    "bar_alignment": "top",
}
SETTINGS = (
    ("descending", "top"),
    ("ascending", "top"),
    ("descending", "bottom"),
    ("ascending", "bottom"),
)
PARAMETER_SPEC = {
    "sort_order": {
        "values": ["descending", "ascending"],
        "default": "descending",
        "meaning": "order output columns by measured bbox height",
    },
    "bar_alignment": {
        "values": ["top", "bottom"],
        "default": "top",
        "meaning": "anchor each shorter output bar at the top or bottom",
    },
}

DESCENDING_FRAGMENT = (
    "(sorted (sort color-heights (lambda (a b) (> (first a) (first b)))))"
)
ASCENDING_FRAGMENT = (
    "(sorted (sort color-heights (lambda (a b) (< (first a) (first b)))))"
)
FIRST_BAR_HEIGHT_FRAGMENT = "(max-h (first (first sorted)))"
TRUE_MAX_HEIGHT_FRAGMENT = "(max-h (max-list (map first sorted)))"
TOP_ALIGNMENT_FRAGMENT = "(if (< r (first entry)) (second entry) 0)"
BOTTOM_ALIGNMENT_FRAGMENT = (
    "(if (>= r (- max-h (first entry))) (second entry) 0)"
)


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha_text(text: str) -> str:
    return _sha_bytes(text.encode("utf-8"))


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _root(root=None) -> Path:
    return Path(root).resolve() if root is not None else find_root(__file__)


def freeze(grid):
    """Hashable grid form used by tests and diversity evidence."""
    return tuple(tuple(row) for row in normalize_grid(grid))


def setting_key(setting) -> str:
    sort_order, bar_alignment = setting
    _validate_setting(sort_order, bar_alignment)
    return f"{sort_order}-{bar_alignment}"


def _validate_setting(sort_order: str, bar_alignment: str) -> None:
    setting = (sort_order, bar_alignment)
    if setting not in SETTINGS:
        raise ValueError(f"unsupported parameter setting: {setting!r}")


def choose_parameters(seed: int) -> tuple[str, str]:
    """Choose once per episode; seeds 0..3 intentionally cover the family."""
    if type(seed) is not int or seed < 0:
        raise TypeError("seed must be a nonnegative integer")
    return SETTINGS[seed % len(SETTINGS)]


def canonical_program(*, root=None) -> str:
    """Read the exact selected canonical default from the source-bound ledger."""
    matches = []
    with canonical_path(_root(root)).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("content_hash") == TASK_ID:
                matches.append(row["program_solution"])
    if len(matches) != 1:
        raise ValueError(f"expected one canonical {TASK_ID} row, found {len(matches)}")
    return matches[0]


def program_for(sort_order: str, bar_alignment: str, *, root=None) -> str:
    """Produce one matching Racket rule without changing the default bytes."""
    _validate_setting(sort_order, bar_alignment)
    program = canonical_program(root=root)
    if program.count(DESCENDING_FRAGMENT) != 1:
        raise ValueError("canonical sort fragment changed")
    if program.count(FIRST_BAR_HEIGHT_FRAGMENT) != 1:
        raise ValueError("canonical canvas-height fragment changed")
    if program.count(TOP_ALIGNMENT_FRAGMENT) != 1:
        raise ValueError("canonical alignment fragment changed")
    if sort_order == "ascending":
        program = program.replace(DESCENDING_FRAGMENT, ASCENDING_FRAGMENT, 1)
        # The canonical descending rule can take max-h from its first column.
        # Ascending order must compute the true maximum independently or the
        # output canvas truncates every taller bar after the first.
        program = program.replace(
            FIRST_BAR_HEIGHT_FRAGMENT,
            TRUE_MAX_HEIGHT_FRAGMENT,
            1,
        )
    if bar_alignment == "bottom":
        program = program.replace(TOP_ALIGNMENT_FRAGMENT, BOTTOM_ALIGNMENT_FRAGMENT, 1)
    return program


def _bbox_stats(grid):
    """Sorted-color measurements matching Racket ``grid-colors`` semantics."""
    grid = normalize_grid(grid)
    colors = sorted({value for row in grid for value in row if value != 0})
    stats = []
    for color in colors:
        cells = [
            (row_index, col_index)
            for row_index, row in enumerate(grid)
            for col_index, value in enumerate(row)
            if value == color
        ]
        rows = [row for row, _col in cells]
        cols = [col for _row, col in cells]
        stats.append(
            (
                color,
                max(rows) - min(rows) + 1,
                max(cols) - min(cols) + 1,
            )
        )
    return stats


def solve_variant(grid, sort_order: str, bar_alignment: str):
    """Independent Python oracle for one member of the proposed family."""
    _validate_setting(sort_order, bar_alignment)
    measurements = [(height, color) for color, height, _width in _bbox_stats(grid)]
    ordered = sorted(
        measurements,
        key=lambda item: item[0],
        reverse=(sort_order == "descending"),
    )
    if not ordered:
        return []
    maximum = max(height for height, _color in ordered)
    out = [[0 for _ in ordered] for _ in range(maximum)]
    for col_index, (height, color) in enumerate(ordered):
        first_row = 0 if bar_alignment == "top" else maximum - height
        for row_index in range(first_row, first_row + height):
            out[row_index][col_index] = color
    return out


def _racket_datum(value) -> str:
    if type(value) is int:
        return str(value)
    if isinstance(value, (list, tuple)):
        return "(" + " ".join(_racket_datum(item) for item in value) + ")"
    raise TypeError(f"unsupported Racket datum: {type(value).__name__}")


def execute_program(bridge: RacketBridge, program: str, grid):
    body = strip_rule_wrapper(program)
    expression = f"({body} (quote {_racket_datum(normalize_grid(grid))}))"
    return normalize_grid(bridge.eval_text(expression))


def _episode_inputs(seed: int, *, root=None):
    root = _root(root)
    module, source_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    difficulties = ("easy", "medium", "hard", "medium")
    inputs = [
        normalize_grid(module.generate(seed, index, difficulty=difficulty))
        for index, difficulty in enumerate(difficulties)
    ]
    for index, grid in enumerate(inputs):
        reasons = list(module.strict_canonical_like(grid))
        if reasons:
            raise ValueError(f"generated input {index} left the strict manifold: {reasons}")
    return inputs, source_path, generator_sha256


def public_challenge(private_episode: dict) -> dict:
    return {
        "schema": PUBLIC_SCHEMA,
        "task_id": TASK_ID,
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in private_episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in private_episode["test"]],
    }


def materialize_episode(seed: int, *, root=None, bridge: RacketBridge | None = None) -> dict:
    """Generate one source-bound episode and execute all four Racket variants."""
    root = _root(root)
    selected_setting = choose_parameters(seed)
    selected_key = setting_key(selected_setting)
    inputs, generator_path, generator_sha256 = _episode_inputs(seed, root=root)
    programs = {
        setting_key(setting): program_for(*setting, root=root)
        for setting in SETTINGS
    }

    manager = nullcontext(bridge) if bridge is not None else RacketBridge(
        max_calls_before_restart=64
    )
    outputs_by_setting = {}
    with manager as live_bridge:
        for setting in SETTINGS:
            key = setting_key(setting)
            racket_outputs = [
                execute_program(live_bridge, programs[key], grid)
                for grid in inputs
            ]
            python_outputs = [solve_variant(grid, *setting) for grid in inputs]
            if racket_outputs != python_outputs:
                raise AssertionError(
                    f"Python/Racket mismatch for {key}: "
                    f"racket={racket_outputs!r} python={python_outputs!r}"
                )
            outputs_by_setting[key] = racket_outputs

    selected_outputs = outputs_by_setting[selected_key]
    rival_demo_differences = {}
    rival_query_differs = {}
    for setting in SETTINGS:
        key = setting_key(setting)
        if key == selected_key:
            continue
        rival_demo_differences[key] = [
            index
            for index in range(3)
            if outputs_by_setting[key][index] != selected_outputs[index]
        ]
        rival_query_differs[key] = outputs_by_setting[key][3] != selected_outputs[3]
        if not rival_demo_differences[key]:
            raise AssertionError(f"demonstrations do not distinguish rival {key}")
        if not rival_query_differs[key]:
            raise AssertionError(f"query does not distinguish rival {key}")

    parameters = {
        "sort_order": selected_setting[0],
        "bar_alignment": selected_setting[1],
    }
    private_episode = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": parameters,
        "parameter_spec": PARAMETER_SPEC,
        "train": [
            {"input": inputs[index], "output": selected_outputs[index]}
            for index in range(3)
        ],
        "test": [{"input": inputs[3], "output": selected_outputs[3]}],
        "program_solution": programs[selected_key],
        "program_sha256": _sha_text(programs[selected_key]),
        "all_program_sha256": {
            key: _sha_text(program) for key, program in programs.items()
        },
        "generator_source": str(generator_path.relative_to(root)),
        "generator_sha256": generator_sha256,
        "canonical_ledger_sha256": _sha_file(canonical_path(root)),
        "rival_demonstration_differences": rival_demo_differences,
        "rival_query_differs": rival_query_differs,
        "racket_verified": True,
    }
    return {
        "parameters": parameters,
        "private": private_episode,
        "public": public_challenge(private_episode),
        "programs": programs,
        "racket_verified": True,
        "rival_demonstration_differences": rival_demo_differences,
        "rival_query_differs": rival_query_differs,
    }


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_evidence(seeds, out_dir: Path, *, root=None) -> Path:
    root = _root(root)
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    rules_dir = out_dir / "rules"
    rules_dir.mkdir(exist_ok=True)
    programs = {
        setting_key(setting): program_for(*setting, root=root)
        for setting in SETTINGS
    }
    for key, program in programs.items():
        (rules_dir / f"{key}.rkt").write_text(program + "\n", encoding="utf-8")

    episodes = []
    with RacketBridge(max_calls_before_restart=128) as bridge:
        for seed in seeds:
            episode = materialize_episode(seed, root=root, bridge=bridge)
            private_path = out_dir / f"episode-{seed:04d}-private.json"
            public_path = out_dir / f"episode-{seed:04d}-public.json"
            _write_json(private_path, episode["private"])
            _write_json(public_path, episode["public"])
            episodes.append(
                {
                    "seed": seed,
                    "parameters": episode["parameters"],
                    "private_path": private_path.name,
                    "private_sha256": _sha_file(private_path),
                    "public_path": public_path.name,
                    "public_sha256": _sha_file(public_path),
                    "rival_demonstration_differences": episode[
                        "rival_demonstration_differences"
                    ],
                    "rival_query_differs": episode["rival_query_differs"],
                    "racket_verified": episode["racket_verified"],
                }
            )

    summary = {
        "schema": "arcpuzzles-parametric-evidence-v1",
        "task_id": TASK_ID,
        "canonical_default": DEFAULT_PARAMETERS,
        "parameter_spec": PARAMETER_SPEC,
        "settings": [
            {
                "sort_order": setting[0],
                "bar_alignment": setting[1],
                "key": setting_key(setting),
                "program_path": f"rules/{setting_key(setting)}.rkt",
                "program_sha256": _sha_text(programs[setting_key(setting)]),
            }
            for setting in SETTINGS
        ],
        "episodes": episodes,
        "all_settings_observed": {
            setting_key(setting): any(
                item["parameters"]
                == {"sort_order": setting[0], "bar_alignment": setting[1]}
                for item in episodes
            )
            for setting in SETTINGS
        },
        "limits": [
            "Only sort order and vertical alignment are parameterized; the measured quantity remains bbox height.",
            "Evidence is finite and establishes the four declared settings on retained seeds, not universal identifiability.",
            "This is a task-local proposal; it does not alter the selected production path or grant training approval.",
        ],
    }
    summary_path = out_dir / "summary.json"
    _write_json(summary_path, summary)
    return summary_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3])
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "evidence",
    )
    args = parser.parse_args(argv)
    if not args.seeds or any(type(seed) is not int or seed < 0 for seed in args.seeds):
        parser.error("--seeds requires one or more nonnegative integers")
    summary = build_evidence(args.seeds, args.out_dir)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
