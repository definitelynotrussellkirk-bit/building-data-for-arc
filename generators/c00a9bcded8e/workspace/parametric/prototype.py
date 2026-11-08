#!/usr/bin/env python3
"""Proposed episode-level horizontal read-direction parameter.

This authoring prototype is isolated from selected production execution; the
canonical authority remains unchanged.  It preserves the original task's complete
reasoning pipeline:

1. identify large, nearly solid non-background same-color components;
2. group their centers into spatial rows;
3. read each row's rectangle colors.

Only step 3 is parameterized once per episode:

``left_to_right`` (canonical/default)
    Sort each spatial row by increasing center column.
``right_to_left`` (proposed alternative)
    Sort each spatial row by decreasing center column.

Prototype demonstrations use the selected production sampler with its
five-target-color column-repeat signature, so every demonstration refutes the
other setting while retaining canonical geometry, noise, and output shape.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "c00a9bcded8e"
PROTOTYPE_VERSION = "horizontal-read-direction-v2"
PARAMETER_NAME = "horizontal_read_direction"
SETTINGS = ("left_to_right", "right_to_left")
DEFAULT_SETTING = "left_to_right"
_CANONICAL_ORDER_EXPR = "(sort-by cur-row second)"
_ALTERNATIVE_ORDER_EXPR = "(reverse (sort-by cur-row second))"
_BANDS = ("easy", "medium", "hard", "medium")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalized_rule_hash(source: str) -> str:
    return sha256_text(" ".join(source.split()))


def grid_sha256(grid: Any) -> str:
    normalized = normalize_grid(grid)
    return sha256_text(json.dumps(normalized, separators=(",", ":")))


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise TypeError("episode seed must be a nonnegative integer (not bool)")
    return seed


def _validate_setting(value: Any) -> str:
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER_NAME} must be one of {SETTINGS}, found {value!r}")
    return value


def choose_setting(seed: int) -> str:
    """Choose one setting deterministically and exactly once per episode."""
    seed = _validate_seed(seed)
    return SETTINGS[seed % len(SETTINGS)]


def other_setting(value: str) -> str:
    selected = _validate_setting(value)
    return SETTINGS[1] if selected == SETTINGS[0] else SETTINGS[0]


def canonical_rule_source(*, root: Path | str | None = None) -> str:
    """Return the unique selected canonical source from an explicit tree."""
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(
                row.get("program_solution"), str
            ):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(f"expected one canonical program_solution for {TASK_ID}")
    source = sources.pop()
    if source.count(_CANONICAL_ORDER_EXPR) != 2:
        raise ValueError(
            "canonical source no longer has exactly two within-row ordering sites"
        )
    if _ALTERNATIVE_ORDER_EXPR in source:
        raise ValueError("canonical source unexpectedly contains reverse row ordering")
    return source


def instantiate_rule(
    horizontal_read_direction: str = DEFAULT_SETTING,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    """Materialize the exact Racket program for one parameter setting."""
    setting = _validate_setting(horizontal_read_direction)
    canonical = canonical_rule_source(root=root) if source is None else source
    if canonical.count(_CANONICAL_ORDER_EXPR) != 2:
        raise ValueError("source must contain exactly two canonical row-sort expressions")
    if setting == DEFAULT_SETTING:
        return canonical
    alternative = canonical.replace(
        _CANONICAL_ORDER_EXPR,
        _ALTERNATIVE_ORDER_EXPR,
    ).replace(
        "left-to-right order",
        "right-to-left order",
    )
    if alternative == canonical or alternative.count(_ALTERNATIVE_ORDER_EXPR) != 2:
        raise AssertionError("failed to instantiate right-to-left Racket rule")
    return alternative


def _same_color_components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Independent 4-connected component analysis for prototype verification."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            top, bottom = min(rows), max(rows)
            left, right = min(cols), max(cols)
            area = (bottom - top + 1) * (right - left + 1)
            result.append(
                {
                    "color": color,
                    "size": len(cells),
                    "area": area,
                    "density": len(cells) / area,
                    "center_r": (top + bottom) / 2,
                    "center_c": (left + right) / 2,
                }
            )
    return result


def solve_python(
    grid: Any,
    *,
    horizontal_read_direction: str = DEFAULT_SETTING,
) -> list[list[int]]:
    """Independent Python reference for the two proposed rule settings."""
    setting = _validate_setting(horizontal_read_direction)
    normalized = normalize_grid(grid)
    rectangles = [
        component
        for component in _same_color_components(normalized)
        if component["size"] >= 9 and component["density"] >= 0.9
    ]
    rectangles.sort(key=lambda component: component["center_r"])

    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    last_row: float | None = None
    for rectangle in rectangles:
        if last_row is None or rectangle["center_r"] - last_row < 4:
            current.append(rectangle)
        else:
            groups.append(current)
            current = [rectangle]
        last_row = rectangle["center_r"]
    if current:
        groups.append(current)

    if len(groups) not in (2, 3, 4) or any(len(group) != 3 for group in groups):
        raise ValueError(
            "prototype domain requires 2..4 spatial rows of exactly three rectangles"
        )
    reverse = setting == "right_to_left"
    return [
        [
            rectangle["color"]
            for rectangle in sorted(
                group,
                key=lambda component: component["center_c"],
                reverse=reverse,
            )
        ]
        for group in groups
    ]


def _derived_seed(episode_seed: int, pair_index: int) -> int:
    digest = hashlib.sha256(
        f"{TASK_ID}:{PROTOTYPE_VERSION}:{episode_seed}:{pair_index}".encode("utf-8")
    ).hexdigest()
    return int(digest[:12], 16)


def _fixtures(
    episode_seed: int,
    *,
    root: Path | str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    episode_seed = _validate_seed(episode_seed)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    generator, source_path, source_sha256 = load_selected_generator(
        TASK_ID,
        root=root_path,
    )
    fixtures: list[dict[str, Any]] = []
    for pair_index, difficulty in enumerate(_BANDS):
        sample_index = pair_index
        seed = _derived_seed(episode_seed, pair_index)
        overrides = {"color_pattern": "column_repeat"}
        grid = generator.generate(
            seed,
            sample_index,
            difficulty=difficulty,
            **overrides,
        )
        errors = generator.self_check(
            grid,
            difficulty=difficulty,
            meta={"overrides": overrides},
        )
        if errors:
            raise AssertionError(
                f"prototype fixture {pair_index} violates selected generator: {errors}"
            )
        left = solve_python(grid, horizontal_read_direction="left_to_right")
        right = solve_python(grid, horizontal_read_direction="right_to_left")
        if left != generator.rule_mirror(grid):
            raise AssertionError(
                f"prototype fixture {pair_index} default diverges from selected mirror"
            )
        if left == right:
            raise AssertionError(
                f"prototype fixture {pair_index} does not distinguish read directions"
            )
        fixtures.append(
            {
                "fixture_id": f"pair-{pair_index}",
                "input": normalize_grid(grid),
                "input_sha256": grid_sha256(grid),
                "generation": {
                    "seed": seed,
                    "sample_index": sample_index,
                    "difficulty": difficulty,
                    "overrides": overrides,
                },
            }
        )
    return fixtures, {
        "path": source_path.relative_to(root_path).as_posix(),
        "sha256": source_sha256,
    }


def build_episode(
    episode_seed: int,
    *,
    horizontal_read_direction: str | None = None,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Build a three-demonstration/one-query episode with one fixed setting."""
    episode_seed = _validate_seed(episode_seed)
    setting = (
        choose_setting(episode_seed)
        if horizontal_read_direction is None
        else _validate_setting(horizontal_read_direction)
    )
    fixtures, generator_source = _fixtures(episode_seed, root=root)
    pairs = [
        {
            "fixture_id": fixture["fixture_id"],
            "input": deepcopy(fixture["input"]),
            "output": solve_python(
                fixture["input"],
                horizontal_read_direction=setting,
            ),
            "input_sha256": fixture["input_sha256"],
            "generation": fixture["generation"],
        }
        for fixture in fixtures
    ]
    source = instantiate_rule(setting, root=root)
    episode = {
        "schema": "c00a9bcded8e-horizontal-read-direction-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": episode_seed,
        "parameter": {PARAMETER_NAME: setting},
        "canonical_default": setting == DEFAULT_SETTING,
        "program": source,
        "program_sha256": sha256_text(source),
        "normalized_rule_hash": normalized_rule_hash(source),
        "generator_source": generator_source,
        "input_constraints": {
            "selected_generator_domain": True,
            "color_pattern": "column_repeat",
            "exactly_five_target_colors": True,
            "every_pair_distinguishes_settings": True,
        },
        "train": pairs[:3],
        "test": pairs[3:],
    }
    errors = episode_errors(episode)
    if errors:
        raise AssertionError("built invalid episode: " + "; ".join(errors))
    return episode


def episode_errors(episode: Any) -> list[str]:
    """Validate constancy, labels, and two-setting demonstration separation."""
    if not isinstance(episode, dict):
        return ["episode must be a mapping"]
    parameter = episode.get("parameter")
    if not isinstance(parameter, dict) or PARAMETER_NAME not in parameter:
        return [f"episode must declare {PARAMETER_NAME!r}"]
    try:
        setting = _validate_setting(parameter[PARAMETER_NAME])
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    try:
        expected_program = instantiate_rule(setting)
    except (TypeError, ValueError) as exc:
        return [f"cannot instantiate episode program: {exc}"]
    if episode.get("program") != expected_program:
        return ["episode program does not match its selected setting"]

    train, test = episode.get("train"), episode.get("test")
    if not isinstance(train, list) or len(train) != 3:
        return ["episode must contain exactly three demonstrations"]
    if not isinstance(test, list) or len(test) != 1:
        return ["episode must contain exactly one query"]

    errors: list[str] = []
    rival = other_setting(setting)
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                errors.append(f"{split_name}[{index}] must contain input and output")
                continue
            try:
                expected = solve_python(
                    pair["input"],
                    horizontal_read_direction=setting,
                )
                competing = solve_python(
                    pair["input"],
                    horizontal_read_direction=rival,
                )
            except (TypeError, ValueError) as exc:
                errors.append(f"{split_name}[{index}] invalid: {exc}")
                continue
            if pair["output"] != expected:
                errors.append(f"{split_name}[{index}] output disagrees with setting")
            if competing == expected:
                errors.append(f"{split_name}[{index}] does not distinguish settings")
    return errors


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove hidden semantics, Racket source, metadata, and query answers."""
    errors = episode_errors(episode)
    if errors:
        raise ValueError("invalid episode: " + "; ".join(errors))
    return {
        "schema": "c00a9bcded8e-horizontal-read-direction-public-v1",
        "train": [
            {
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _grid_literal(grid: Any) -> str:
    normalized = normalize_grid(grid)
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in normalized
    )
    return f"'({rows})"


def _racket_callable(source: str) -> str:
    """Extract the callable lambda without importing repository-only wrappers."""
    stripped = source.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("prototype program must have one outer rule! wrapper")
    body = stripped[len("(rule!") : -1].strip()
    if not body.startswith("(lambda (g)"):
        raise ValueError("prototype program must wrap a lambda accepting g")
    return body


def _rule_application(source: str, grid: Any) -> str:
    return f"({_racket_callable(source)} {_grid_literal(grid)})"


def racket_outputs(
    grids: Iterable[Any],
    *,
    horizontal_read_direction: str = DEFAULT_SETTING,
    root: Path | str | None = None,
) -> list[list[list[int]]]:
    """Execute one materialized setting through the pinned Racket bridge."""
    from arc_repl.racket_bridge import RacketBridge

    setting = _validate_setting(horizontal_read_direction)
    source = instantiate_rule(setting, root=root)
    outputs: list[list[list[int]]] = []
    with RacketBridge() as bridge:
        for grid in grids:
            outputs.append(normalize_grid(bridge.eval_text(_rule_application(source, grid))))
    return outputs


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_evidence_report(
    seed: int,
    *,
    root: Path | str | None = None,
    verify_racket: bool = True,
) -> dict[str, Any]:
    """Build both complete episodes and optionally verify every label in Racket."""
    seed = _validate_seed(seed)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    episodes = {
        setting: build_episode(
            seed,
            horizontal_read_direction=setting,
            root=root_path,
        )
        for setting in SETTINGS
    }
    left_pairs = episodes["left_to_right"]["train"] + episodes["left_to_right"]["test"]
    right_pairs = episodes["right_to_left"]["train"] + episodes["right_to_left"]["test"]
    if [pair["input"] for pair in left_pairs] != [pair["input"] for pair in right_pairs]:
        raise AssertionError("setting episodes must share exact inputs")

    racket_receipts: dict[str, Any] = {}
    for setting, episode in episodes.items():
        pairs = episode["train"] + episode["test"]
        expected = [pair["output"] for pair in pairs]
        if verify_racket:
            actual = racket_outputs(
                [pair["input"] for pair in pairs],
                horizontal_read_direction=setting,
                root=root_path,
            )
            if actual != expected:
                raise AssertionError(f"Racket/Python mismatch for {setting}")
            racket_receipts[setting] = {
                "executed": True,
                "pair_count": len(actual),
                "output_sha256": [grid_sha256(grid) for grid in actual],
                "all_match_python": True,
            }
        else:
            racket_receipts[setting] = {
                "executed": False,
                "pair_count": 0,
                "all_match_python": None,
            }

    witness_input = left_pairs[0]["input"]
    witness = {
        "fixture_id": left_pairs[0]["fixture_id"],
        "input": witness_input,
        "input_sha256": grid_sha256(witness_input),
        "outputs": {
            setting: solve_python(
                witness_input,
                horizontal_read_direction=setting,
            )
            for setting in SETTINGS
        },
    }
    witness["distinguishes_settings"] = (
        witness["outputs"][SETTINGS[0]] != witness["outputs"][SETTINGS[1]]
    )
    if not witness["distinguishes_settings"]:
        raise AssertionError("cross-setting witness unexpectedly collapsed")

    source_path = Path(__file__).resolve()
    return {
        "schema": "c00a9bcded8e-horizontal-read-direction-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "status": "verified" if verify_racket else "python_only",
        "parameter_contract": {
            "name": PARAMETER_NAME,
            "allowed_values": list(SETTINGS),
            "default": DEFAULT_SETTING,
            "selection_scope": "once_per_episode",
        },
        "prototype_source": {
            "path": source_path.relative_to(root_path).as_posix(),
            "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        },
        "rules": {
            setting: {
                "source": instantiate_rule(setting, root=root_path),
                "sha256": sha256_text(instantiate_rule(setting, root=root_path)),
                "normalized_sha256": normalized_rule_hash(
                    instantiate_rule(setting, root=root_path)
                ),
                "canonical_default_exact": (
                    setting == DEFAULT_SETTING
                    and instantiate_rule(setting, root=root_path)
                    == canonical_rule_source(root=root_path)
                ),
            }
            for setting in SETTINGS
        },
        "episodes": episodes,
        "racket_verification": racket_receipts,
        "cross_setting_witness": witness,
        "limitations": [
            "Prototype only; the production generate(...) API remains canonical.",
            "Evidence covers one seed and two bounded settings, not all seeds.",
            "Episodes force the five-color column_repeat signature solely to guarantee identifiability.",
            "Finite two-setting separation does not prove universal rule induction.",
        ],
    }


def public_filename(episode: dict[str, Any]) -> str:
    """Opaque identifier derived only from visible puzzle content."""
    visible = {
        "schema": "c00a9bcded8e-horizontal-read-direction-public-v1",
        "train": [{"input": p["input"], "output": p["output"]} for p in episode["train"]],
        "test": [{"input": p["input"]} for p in episode["test"]],
    }
    raw = json.dumps(visible, sort_keys=True, separators=(",", ":")).encode()
    return "challenge-" + hashlib.sha256(raw).hexdigest() + ".json"


def materialize_artifacts(
    report: dict[str, Any],
    *,
    output_path: Path,
    examples_dir: Path,
    rules_dir: Path,
) -> None:
    _write_json(output_path, report)
    examples_dir.mkdir(parents=True, exist_ok=True)
    rules_dir.mkdir(parents=True, exist_ok=True)
    for setting in SETTINGS:
        rule_path = rules_dir / f"{setting}.rkt"
        rule_path.write_text(report["rules"][setting]["source"] + "\n", encoding="utf-8")
        _write_json(
            examples_dir / public_filename(report["episodes"][setting]),
            public_challenge(report["episodes"][setting]),
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--examples-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "examples",
    )
    parser.add_argument(
        "--rules-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "rules",
    )
    parser.add_argument(
        "--python-only",
        action="store_true",
        help="build artifacts without Racket execution (not sufficient for final evidence)",
    )
    args = parser.parse_args(argv)
    report = build_evidence_report(
        args.seed,
        verify_racket=not args.python_only,
    )
    materialize_artifacts(
        report,
        output_path=args.out,
        examples_dir=args.examples_dir,
        rules_dir=args.rules_dir,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "out": str(args.out),
                "settings": list(SETTINGS),
                "witness": report["cross_setting_witness"]["input_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
