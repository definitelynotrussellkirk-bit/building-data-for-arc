#!/usr/bin/env python3
"""Proposed frequency-order/tie-break variants for ARC task 1189131c32a4.

This is a task-local, unapproved prototype.  The production generator and its
canonical rule remain unchanged.  Inputs are sampled independently of the
private setting; only the output-ranking rule changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from contextlib import nullcontext
from functools import lru_cache
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "1189131c32a4"
VERSION = "proposed-frequency-rings-v1"
CANONICAL_SOURCE_SHA256 = "cb24e365264238c0be9d5cd2e869bbb19a300270ad43bf90ddef138a66986722"
GENERATOR_SOURCE_SHA256 = "563d9029027d65a06a2c7c01716171eb39685c7284cdb16d6024f6181cb74c8d"

FREQUENCY_ORDERS = ("most_outside", "least_outside")
TIE_BREAKS = ("descending_numeric", "ascending_numeric")
DEFAULT_SETTINGS = {
    "frequency_order": "most_outside",
    "tie_break": "descending_numeric",
}
ALL_SETTINGS = tuple(
    {"frequency_order": frequency_order, "tie_break": tie_break}
    for frequency_order in FREQUENCY_ORDERS
    for tie_break in TIE_BREAKS
)

_CANONICAL_SORT = "(sorted-c (reverse (sort-by colors (lambda (c) (length (find-color g c))))))"
_SORT_EXPRESSIONS = {
    ("most_outside", "descending_numeric"): _CANONICAL_SORT,
    ("most_outside", "ascending_numeric"): "(sorted-c (sort-by colors (lambda (c) (- 0 (length (find-color g c))))))",
    ("least_outside", "descending_numeric"): "(sorted-c (reverse (sort-by colors (lambda (c) (- 0 (length (find-color g c)))))))",
    ("least_outside", "ascending_numeric"): "(sorted-c (sort-by colors (lambda (c) (length (find-color g c)))))",
}


def _sha256(value: str | bytes) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def settings_key(settings: Any) -> tuple[str, str]:
    checked = normalize_settings(settings)
    return checked["frequency_order"], checked["tie_break"]


def normalize_settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"frequency_order", "tie_break"}:
        raise ValueError("settings must name exactly frequency_order and tie_break")
    frequency_order = settings["frequency_order"]
    tie_break = settings["tie_break"]
    if type(frequency_order) is not str or frequency_order not in FREQUENCY_ORDERS:
        raise ValueError(f"frequency_order must be one of {FREQUENCY_ORDERS!r}")
    if type(tie_break) is not str or tie_break not in TIE_BREAKS:
        raise ValueError(f"tie_break must be one of {TIE_BREAKS!r}")
    return {"frequency_order": frequency_order, "tie_break": tie_break}


def _validated_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    return seed


def _validated_count(value: Any, *, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be a literal integer in {minimum}..{maximum}")
    return value


def canonical_source(*, root: str | Path | None = None) -> str:
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    sources = {
        row["program_solution"]
        for line in canonical_path(root_path).read_text(encoding="utf-8").splitlines()
        if line.strip()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    if len(sources) != 1:
        raise ValueError(f"expected one canonical source for {TASK_ID}, found {len(sources)}")
    source = sources.pop()
    if _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("canonical source differs from the pinned task rule")
    if source.count(_CANONICAL_SORT) != 1:
        raise ValueError("pinned canonical source lacks the guarded ranking expression")
    return source


def program(settings: Any, *, root: str | Path | None = None) -> str:
    checked = normalize_settings(settings)
    source = canonical_source(root=root)
    replacement = _SORT_EXPRESSIONS[settings_key(checked)]
    if replacement == _CANONICAL_SORT:
        return source
    return source.replace(_CANONICAL_SORT, replacement, 1)


def _ranked_colors(grid: list[list[int]], settings: Any) -> list[int]:
    checked = normalize_settings(settings)
    counts = Counter(cell for row in grid for cell in row if cell != 7)
    if not counts:
        raise ValueError("input must contain at least one non-7 color")
    count_sign = -1 if checked["frequency_order"] == "most_outside" else 1
    color_sign = -1 if checked["tie_break"] == "descending_numeric" else 1
    return sorted(counts, key=lambda color: (count_sign * counts[color], color_sign * color))


def transform(grid: Any, settings: Any) -> list[list[int]]:
    normalized = normalize_grid(grid)
    ranked = _ranked_colors(normalized, settings)
    count = len(ranked)
    size = 2 * count - 1
    center = count - 1
    return [
        [ranked[count - 1 - max(abs(row - center), abs(col - center))] for col in range(size)]
        for row in range(size)
    ]


@lru_cache(maxsize=8)
def _selected_generator(root_text: str):
    module, _source, digest = load_selected_generator(TASK_ID, root=Path(root_text))
    if digest != GENERATOR_SOURCE_SHA256:
        raise ValueError("selected generator differs from the prototype's pinned input grammar")
    return module


def _frozen(grid: Any) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in normalize_grid(grid))


def _input_schedule(seed: int, *, root: str | Path | None = None) -> tuple[list, list]:
    """Create fixed 8-demo/8-query prefixes independent of settings/counts."""
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    generator = _selected_generator(str(root_path))
    seen: set[tuple[tuple[int, ...], ...]] = set()
    sections: list[list[list[list[int]]]] = [[], []]
    for section, base in enumerate((0, 100_000)):
        for slot in range(8):
            for retry in range(64):
                profile = ("tie_two_way", "tie_three_way")[(slot + retry) % 2]
                sample_index = base + slot * 64 + retry
                grid = generator.generate(
                    seed,
                    sample_index,
                    difficulty="hard",
                    scene_profile=profile,
                )
                key = _frozen(grid)
                if key in seen or generator.self_check(grid):
                    continue
                outputs = {_frozen(transform(grid, settings)) for settings in ALL_SETTINGS}
                if len(outputs) != len(ALL_SETTINGS):
                    continue
                seen.add(key)
                sections[section].append(grid)
                break
            else:
                raise ValueError(
                    f"could not sample unique identifying {'demo' if section == 0 else 'query'} {slot}"
                )
    return sections[0], sections[1]


def settings_for_seed(seed: Any) -> dict[str, str]:
    checked_seed = _validated_seed(seed)
    return dict(random.Random(checked_seed ^ 0x1189131C32A4).choice(ALL_SETTINGS))


def generate_episode(
    seed: Any,
    settings: Any | None = None,
    *,
    demos: Any = 3,
    queries: Any = 4,
    root: str | Path | None = None,
) -> dict[str, Any]:
    checked_seed = _validated_seed(seed)
    checked_demos = _validated_count(demos, name="demos", minimum=2, maximum=8)
    checked_queries = _validated_count(queries, name="queries", minimum=1, maximum=8)
    checked_settings = settings_for_seed(checked_seed) if settings is None else normalize_settings(settings)
    demo_inputs, query_inputs = _input_schedule(checked_seed, root=root)

    def pair(grid):
        return {"input": grid, "output": transform(grid, checked_settings)}

    train = [pair(grid) for grid in demo_inputs[:checked_demos]]
    test = [pair(grid) for grid in query_inputs[:checked_queries]]
    survivors = fit_settings(train)
    if survivors != [checked_settings]:
        raise ValueError(f"demonstrations do not uniquely identify settings: {survivors!r}")
    return {
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "seed": checked_seed,
        "settings": checked_settings,
        "train": train,
        "test": test,
        "program_solution": program(checked_settings, root=root),
    }


def fit_settings(demonstrations: Any) -> list[dict[str, str]]:
    if type(demonstrations) is not list or not demonstrations:
        raise ValueError("demonstrations must be a nonempty list")
    survivors = []
    for settings in ALL_SETTINGS:
        try:
            fits = all(
                transform(pair["input"], settings) == normalize_grid(pair["output"])
                for pair in demonstrations
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("each demonstration needs valid input and output grids") from exc
        if fits:
            survivors.append(dict(settings))
    return survivors


def _rule_callable(source: str) -> str:
    if type(source) is not str or not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    body = source[len("(rule! ") : -1].strip()
    if not body.startswith("(lambda (g)"):
        raise ValueError("rule must contain a lambda over g")
    return body


def _grid_literal(grid: Any) -> str:
    normalized = normalize_grid(grid)
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in normalized) + ")"


def execute_rule(source: str, grid: Any, *, bridge: RacketBridge | None = None) -> list[list[int]]:
    expression = f"({_rule_callable(source)} {_grid_literal(grid)})"
    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        return normalize_grid(active.eval_text(expression))


def verify_episode(
    episode: Any,
    *,
    root: str | Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    settings = normalize_settings(episode.get("settings"))
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode needs nonempty train/test lists")
    pairs = train + test
    sources = {settings_key(candidate): program(candidate, root=root) for candidate in ALL_SETTINGS}
    manager = nullcontext(bridge) if bridge is not None else RacketBridge(max_calls_before_restart=256)
    with manager as active:
        predictions: dict[tuple[str, str], list[list[list[int]]]] = {}
        checks = []
        for candidate in ALL_SETTINGS:
            key = settings_key(candidate)
            source = sources[key]
            rows = []
            for index, pair in enumerate(pairs):
                racket_output = execute_rule(source, pair["input"], bridge=active)
                python_output = transform(pair["input"], candidate)
                matches_python = racket_output == python_output
                checks.append(
                    {
                        "settings": dict(candidate),
                        "pair_index": index,
                        "program_sha256": _sha256(source),
                        "matches_python": matches_python,
                    }
                )
                if not matches_python:
                    raise ValueError(f"Racket/Python disagreement for {candidate!r} pair {index}")
                rows.append(racket_output)
            predictions[key] = rows

    selected_key = settings_key(settings)
    for index, pair in enumerate(pairs):
        if predictions[selected_key][index] != normalize_grid(pair["output"]):
            raise ValueError(f"selected Racket rule disagrees with episode label {index}")
    survivors = [
        dict(candidate)
        for candidate in ALL_SETTINGS
        if all(
            predictions[settings_key(candidate)][index] == normalize_grid(pair["output"])
            for index, pair in enumerate(train)
        )
    ]
    query_offset = len(train)
    all_query_predictions_distinct = all(
        len({_frozen(predictions[settings_key(candidate)][query_offset + index]) for candidate in ALL_SETTINGS})
        == len(ALL_SETTINGS)
        for index in range(len(test))
    )
    return {
        "settings": settings,
        "label_count": len(pairs),
        "surviving_settings": survivors,
        "all_query_predictions_distinct": all_query_predictions_distinct,
        "program_checks": checks,
    }


def write_evidence(
    out: str | Path,
    *,
    seed: int,
    demos: int,
    queries: int,
    all_settings: bool,
    selected_settings: dict[str, str] | None = None,
    root: str | Path | None = None,
) -> Path:
    destination = Path(out)
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"refusing nonempty evidence directory: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    episode_settings = ALL_SETTINGS if all_settings else (selected_settings or settings_for_seed(seed),)
    episodes = [generate_episode(seed, settings, demos=demos, queries=queries, root=root) for settings in episode_settings]
    with RacketBridge(max_calls_before_restart=256) as bridge:
        reports = [verify_episode(episode, root=root, bridge=bridge) for episode in episodes]
        runtime_identity = bridge.runtime_identity
        default_source = program(DEFAULT_SETTINGS, root=root)
        canonical_checks = [
            execute_rule(default_source, pair["input"], bridge=bridge) == pair["output"]
            for pair in canonical_pairs(TASK_ID, root=find_root(__file__) if root is None else Path(root), labeled_only=True)
        ]
    records = []
    episodes_dir = destination / "episodes"
    episodes_dir.mkdir(exist_ok=True)
    for index, (episode, report) in enumerate(zip(episodes, reports, strict=True)):
        path = episodes_dir / f"episode-{index:02d}.json"
        path.write_text(json.dumps({"episode": episode, "verification": report}, indent=2, sort_keys=True) + "\n")
        records.append(
            {
                "path": str(path.relative_to(destination)),
                "settings": episode["settings"],
                "program_sha256": _sha256(episode["program_solution"]),
                "input_sha256": [
                    _sha256(json.dumps(pair["input"], separators=(",", ":")))
                    for pair in episode["train"] + episode["test"]
                ],
                "surviving_settings": report["surviving_settings"],
                "all_query_predictions_distinct": report["all_query_predictions_distinct"],
            }
        )
    summary = {
        "schema": "arcpuzzles-parametric-frequency-rings-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "seed": seed,
        "demos": demos,
        "queries": queries,
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "generator_source_sha256": GENERATOR_SOURCE_SHA256,
        "runtime_identity": runtime_identity,
        "canonical_pair_checks": canonical_checks,
        "episodes": records,
    }
    summary_path = destination / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--frequency-order", choices=FREQUENCY_ORDERS)
    parser.add_argument("--tie-break", choices=TIE_BREAKS)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    explicit = None
    if args.frequency_order is not None or args.tie_break is not None:
        if args.frequency_order is None or args.tie_break is None:
            parser.error("--frequency-order and --tie-break must be supplied together")
        explicit = {"frequency_order": args.frequency_order, "tie_break": args.tie_break}
    if args.all_settings and explicit is not None:
        parser.error("--all-settings cannot be combined with explicit settings")
    path = write_evidence(
        args.out,
        seed=args.seed,
        demos=args.demos,
        queries=args.queries,
        all_settings=args.all_settings,
        selected_settings=explicit,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
