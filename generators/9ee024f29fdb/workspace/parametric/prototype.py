#!/usr/bin/env python3
"""Racket-backed period/paint parametric prototype for 9ee024f29fdb.

The canonical/default rule is preserved byte-for-byte.  Inputs are sampled from
one setting-independent grammar, parameters are fixed for the whole episode,
and retained public filenames hash visible bytes only.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "9ee024f29fdb"
VERSION = "period-paint-prototype-v2"
ALLOWED_PERIODS = (3, 4, 5)
ALLOWED_PAINT_COLORS = (2, 4)
DEFAULT_PERIOD = 4
DEFAULT_PAINT_COLOR = 2
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
HERE = Path(__file__).resolve().parent

_DEMO_SIZES = ((13, 13), (13, 17), (17, 13), (17, 17), (20, 22), (22, 20))
_QUERY_SIZES = ((15, 19), (19, 15), (24, 24), (30, 30))


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable_rng(seed: int, role: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{VERSION}:{seed}:{role}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def validate_seed(seed: int) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (bool rejected)")
    return seed


def validate_count(name: str, value: int, lo: int, hi: int) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an integer in [{lo},{hi}]")
    return value


def normalize_settings(settings: dict[str, Any] | None = None) -> dict[str, int]:
    if settings is None:
        settings = {}
    if not isinstance(settings, dict):
        raise TypeError("settings must be a dictionary")
    unknown = sorted(set(settings) - {"period", "paint_color"})
    if unknown:
        raise ValueError(f"unknown setting(s): {', '.join(unknown)}")
    period = settings.get("period", DEFAULT_PERIOD)
    paint_color = settings.get("paint_color", DEFAULT_PAINT_COLOR)
    if type(period) is not int or period not in ALLOWED_PERIODS:
        raise ValueError(f"period must be one of {ALLOWED_PERIODS}")
    if type(paint_color) is not int or paint_color not in ALLOWED_PAINT_COLORS:
        raise ValueError(f"paint_color must be one of {ALLOWED_PAINT_COLORS}")
    return {"period": period, "paint_color": paint_color}


@lru_cache(maxsize=1)
def canonical_program(root: str | Path | None = None) -> str:
    root_path = find_root(root or __file__)
    matches = []
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one canonical row for {TASK_ID}")
    return str(matches[0]["program_solution"])


def render_program(
    period: int = DEFAULT_PERIOD,
    paint_color: int = DEFAULT_PAINT_COLOR,
    *,
    root: str | Path | None = None,
) -> str:
    selected = normalize_settings({"period": period, "paint_color": paint_color})
    canonical = canonical_program(root)
    if selected == {"period": DEFAULT_PERIOD, "paint_color": DEFAULT_PAINT_COLOR}:
        return canonical
    replacements = (
        ("(mod r 4)", f"(mod r {period})"),
        ("(mod c 4)", f"(mod c {period})"),
        ("(if (= v 8) 0 2)", f"(if (= v 8) 0 {paint_color})"),
    )
    source = canonical
    for old, new in replacements:
        if source.count(old) != 1:
            raise ValueError(f"canonical source occurrence drift for {old!r}")
        source = source.replace(old, new, 1)
    return source


def python_apply(
    grid: list[list[int]],
    *,
    period: int = DEFAULT_PERIOD,
    paint_color: int = DEFAULT_PAINT_COLOR,
) -> list[list[int]]:
    normalize_settings({"period": period, "paint_color": paint_color})
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
        or any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row)
    ):
        raise ValueError("grid must be a nonempty rectangular ARC integer grid")
    return [
        [
            0 if row % period == 0 or col % period == 0 or value == 8 else paint_color
            for col, value in enumerate(values)
        ]
        for row, values in enumerate(grid)
    ]


def _fixture(seed: int, role: str, index: int, height: int, width: int) -> list[list[int]]:
    rng = _stable_rng(seed, role, index)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    # The untouched 6x3 witness block guarantees that every period and paint
    # choice is observable in every example: rows 3/4/5 distinguish periods,
    # while (1,1) distinguishes paint colors away from all candidate lattices.
    grid[1][2] = 8
    grid[2][1] = 7
    for row in range(height):
        for col in range(width):
            if row < 6 and col < 3:
                continue
            draw = rng.random()
            if draw < 0.34:
                grid[row][col] = 8
            elif draw < 0.47:
                grid[row][col] = rng.choice((1, 3, 5, 6, 7, 9))

    # Add boundary contacts and long structured cyan/noncyan strokes so the
    # largest queries exercise the whole canvas rather than pad a tiny witness.
    for col in range(0, width, 2 + index % 3):
        grid[height - 1][col] = 8 if (col + index) % 3 else 6
    for row in range(0, height, 3 + index % 2):
        grid[row][width - 1] = 8 if (row + index) % 2 else 9
    if min(height, width) >= 24:
        for offset in range(7, min(height, width) - 3):
            grid[offset][offset] = 8 if offset % 3 else 5
            grid[offset][width - 1 - offset] = 8 if offset % 4 else 7
    return grid


def episode_inputs(
    seed: int,
    *,
    demos: int = 3,
    queries: int = 4,
) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    validate_seed(seed)
    demos = validate_count("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = validate_count("queries", queries, MIN_QUERIES, MAX_QUERIES)
    train = [
        _fixture(seed, "demo", index, *_DEMO_SIZES[index])
        for index in range(demos)
    ]
    test = [
        _fixture(seed, "query", index, *_QUERY_SIZES[index])
        for index in range(queries)
    ]
    grids = train + test
    if len({json.dumps(grid, separators=(",", ":")) for grid in grids}) != len(grids):
        raise RuntimeError("episode input sampler produced a duplicate")
    return train, test


def fixture_inputs(seed: int) -> list[list[list[int]]]:
    """Compatibility helper returning the retained 3-demo/4-query input set."""
    train, test = episode_inputs(seed, demos=3, queries=4)
    return train + test


def build_episode_python(
    seed: int,
    settings: dict[str, Any] | None = None,
    *,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    selected = normalize_settings(settings)
    train_inputs, test_inputs = episode_inputs(seed, demos=demos, queries=queries)

    def pair(grid: list[list[int]]) -> dict[str, Any]:
        return {
            "input": grid,
            "output": python_apply(grid, **selected),
        }

    return {
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": render_program(**selected),
    }


def _all_settings() -> tuple[tuple[int, int], ...]:
    return tuple((period, color) for period in ALLOWED_PERIODS for color in ALLOWED_PAINT_COLORS)


def generate_episode_python(
    seed: int,
    *,
    period: int | None = None,
    paint_color: int | None = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    selected = normalize_settings(
        {
            "period": DEFAULT_PERIOD if period is None else period,
            "paint_color": DEFAULT_PAINT_COLOR if paint_color is None else paint_color,
        }
    )
    base = build_episode_python(seed, selected, demos=demos, queries=queries)
    grids = [pair["input"] for pair in base["train"] + base["test"]]
    chosen_outputs = [pair["output"] for pair in base["train"] + base["test"]]
    rivals = []
    for rival_period, rival_color in _all_settings():
        rival_outputs = [
            python_apply(grid, period=rival_period, paint_color=rival_color)
            for grid in grids
        ]
        rivals.append(
            {
                "parameters": {"period": rival_period, "paint_color": rival_color},
                "demo_differences": [
                    index
                    for index in range(demos)
                    if rival_outputs[index] != chosen_outputs[index]
                ],
                "query_differences": [
                    index
                    for index in range(queries)
                    if rival_outputs[demos + index] != chosen_outputs[demos + index]
                ],
            }
        )
    return {
        "schema": "9ee024f29fdb-parametric-period-paint-v2",
        "seed": seed,
        "parameters": selected,
        "program": base["program_solution"],
        "train": base["train"],
        "test": base["test"],
        "rivals": rivals,
        "label_authority": "independent Python parity oracle; retained evidence executes Racket",
    }


def execute(bridge: Any, source: str, grid: list[list[int]]) -> list[list[int]]:
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("expected a rule! wrapper")
    bridge.define_grid("g", grid)
    body = source[len("(rule! ") : -1]
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    result = bridge.eval_text(expression)
    if (
        type(result) is not list
        or not result
        or type(result[0]) is not list
        or not result[0]
        or any(type(row) is not list or len(row) != len(result[0]) for row in result)
        or any(type(cell) is not int or not 0 <= cell <= 9 for row in result for cell in row)
    ):
        raise ValueError("Racket rule returned a non-ARC grid")
    return result


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_public_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(public_challenge_bytes(payload))


def _source_hashes(root: Path) -> dict[str, str]:
    paths = [
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE / "README.md",
        HERE.parents[1] / "tests" / "test_parametric_period_paint.py",
    ]
    return {
        path.relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in paths
        if path.is_file()
    }


def materialize(output: str | Path, *, base_seed: int = 20261019) -> dict[str, Any]:
    validate_seed(base_seed)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    settings = _all_settings()
    train_inputs, test_inputs = episode_inputs(base_seed, demos=3, queries=4)
    grids = train_inputs + test_inputs

    from arc_repl.racket_bridge import RacketBridge

    outputs: dict[tuple[int, int], list[list[list[int]]]] = {}
    with RacketBridge() as bridge:
        for setting in settings:
            source = render_program(*setting)
            rows = [execute(bridge, source, grid) for grid in grids]
            expected = [python_apply(grid, period=setting[0], paint_color=setting[1]) for grid in grids]
            if rows != expected:
                raise ValueError(f"Racket/Python parity failure for setting {setting}")
            outputs[setting] = rows
        runtime_identity = bridge.runtime_identity

    seen_ids: set[str] = set()
    complete = []
    all_teaching = True
    for chosen in settings:
        train = [
            {"input": deepcopy(grids[index]), "output": deepcopy(outputs[chosen][index])}
            for index in range(3)
        ]
        test = [
            {"input": deepcopy(grids[3 + index]), "output": deepcopy(outputs[chosen][3 + index])}
            for index in range(4)
        ]
        rivals = []
        survivors = []
        for candidate in settings:
            demo_differences = [index for index in range(3) if outputs[candidate][index] != outputs[chosen][index]]
            query_differences = [index for index in range(4) if outputs[candidate][3 + index] != outputs[chosen][3 + index]]
            if not demo_differences:
                survivors.append(candidate)
            rivals.append(
                {
                    "parameters": {"period": candidate[0], "paint_color": candidate[1]},
                    "demo_differences": demo_differences,
                    "query_differences": query_differences,
                }
            )
        teaching_pass = survivors == [chosen]
        all_teaching = all_teaching and teaching_pass
        source = render_program(*chosen)
        private = {
            "schema": "9ee024f29fdb-parametric-period-paint-v2",
            "seed": base_seed,
            "parameters": {"period": chosen[0], "paint_color": chosen[1]},
            "program": source,
            "program_sha256": _sha256(source.encode()),
            "train": train,
            "test": test,
            "rivals": rivals,
            "demo_only_survivors": [
                {"period": period, "paint_color": color} for period, color in survivors
            ],
            "demo_only_teaching_pass": teaching_pass,
            "label_authority": "bundled Racket bridge executing exact instantiated programs",
        }
        public = public_challenge(private)
        identifier = public_challenge_id(public)
        if identifier in seen_ids:
            raise ValueError("duplicate visible challenge across settings")
        seen_ids.add(identifier)
        name = f"challenge-{identifier}"
        private["public_id"] = identifier
        private["public_file"] = f"public/{name}.json"
        _write_public_json(output / "public" / f"{name}.json", public)
        _write_json(output / "private" / "episodes" / f"{name}.json", private)
        rule_path = output / "private" / "rules" / f"period-{chosen[0]}-paint-{chosen[1]}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(source, encoding="utf-8")
        complete.append(private)

    max_query_shape = max(
        ([len(pair["input"]), len(pair["input"][0])] for row in complete for pair in row["test"]),
        key=lambda shape: shape[0] * shape[1],
    )
    report = {
        "schema": "9ee024f29fdb-parametric-period-paint-report-v2",
        "status": "prototype",
        "task_id": TASK_ID,
        "version": VERSION,
        "parameters": {"period": list(ALLOWED_PERIODS), "paint_color": list(ALLOWED_PAINT_COLORS)},
        "default": {"period": DEFAULT_PERIOD, "paint_color": DEFAULT_PAINT_COLOR},
        "default_program_exact_canonical": render_program(4, 2) == canonical_program(),
        "complete_episodes": len(complete),
        "pairs_per_episode": {"train": 3, "test": 4},
        "racket_rule_applications": len(settings) * len(grids),
        "all_labels_and_rivals_executed_in_racket": True,
        "all_racket_outputs_match_python_parity_oracle": True,
        "all_demo_only_teaching_checks_pass": all_teaching,
        "input_sampling_independent_of_settings": True,
        "max_query_shape": max_query_shape,
        "runtime_identity": runtime_identity,
        "source_sha256": _source_hashes(root),
        "bounded_adversarial_checks": [
            {
                "surface": "query-count/prefix contract",
                "result": "repaired",
                "detail": "the prior fixed one-query gallery now supports 1..4 queries with invariant first-query content and four distinct retained queries",
            },
            {
                "surface": "public serialization and identifier leakage",
                "result": "repaired",
                "detail": "setting-associated ordinals, truncated IDs, and pretty-printed public JSON were replaced by exact canonical public bytes and packet-conformant challenge-<full-visible-byte-SHA-256>.json filenames; private answer mutation does not change the ID",
            },
        ],
        "limitations": [
            "Proposed task-local prototype only; production remains fixed to the canonical rule.",
            "Only periods 3,4,5 and paint colors 2,4 are covered.",
            "Finite setting/seed evidence is not universal identifiability or measured training gain.",
        ],
    }
    _write_json(output / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-seed", type=int, default=20261019)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = materialize(args.out, base_seed=args.base_seed)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(
        json.dumps(
            {
                "status": report["status"],
                "complete_episodes": report["complete_episodes"],
                "racket_rule_applications": report["racket_rule_applications"],
                "out": str(args.out),
            }
        )
    )
    return 0 if report["all_demo_only_teaching_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
