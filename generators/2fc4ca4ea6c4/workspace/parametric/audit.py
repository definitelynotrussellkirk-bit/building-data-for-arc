"""Bounded teaching, shortcut, and causal audit for 2fc4ca4ea6c4."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SETTINGS = (
    {"completion_mode": "midpoints"},
    {"completion_mode": "connect_aligned"},
)


def _load_adapter():
    path = HERE / "adapter.py"
    spec = importlib.util.spec_from_file_location("audit_2fc_adapter", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load adjacent adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _has_singleton(grid) -> bool:
    for row in grid:
        column = 0
        while column < len(row):
            if row[column] == 0:
                column += 1
                continue
            color = row[column]
            start = column
            while column < len(row) and row[column] == color:
                column += 1
            if column - start == 1:
                return True
    return False


def _connect_ignoring_blockers(adapter, grid):
    source = adapter.stage_a(grid)
    height, width = len(source), len(source[0])
    out = [row[:] for row in source]
    for column in range(width):
        for color in {source[row][column] for row in range(height)} - {0}:
            hits = [row for row in range(height) if source[row][column] == color]
            if len(hits) == 2:
                for row in range(hits[0], hits[1] + 1):
                    out[row][column] = color
    return out


def _connect_two_or_more(adapter, grid):
    source = adapter.stage_a(grid)
    height, width = len(source), len(source[0])
    out = [row[:] for row in source]
    for column in range(width):
        for color in {source[row][column] for row in range(height)} - {0}:
            hits = [row for row in range(height) if source[row][column] == color]
            if len(hits) >= 2:
                for row in range(min(hits), max(hits) + 1):
                    out[row][column] = color
    return out


def run_audit(destination: Path | str | None = None, *, seeds=(0, 17, 29, 63)) -> dict:
    adapter = _load_adapter()
    checked_settings = 0
    unique_survivors = 0
    alternative_pairs = 0
    differs_skip_a = 0
    differs_skip_b = 0
    singleton_pairs = 0
    shortcut_checked = 0
    shortcut_refuted = 0
    shortcut_query_disagreements = 0

    shortcut_rivals = (
        lambda grid: _connect_ignoring_blockers(adapter, grid),
        lambda grid: _connect_two_or_more(adapter, grid),
    )

    for seed in seeds:
        inputs_by_setting = []
        for chosen, setting in enumerate(SETTINGS):
            episode = adapter.generate(seed, setting, 2, 4)
            inputs_by_setting.append([
                pair["input"] for split in ("train", "test") for pair in episode[split]
            ])
            survivors = []
            for rival, candidate in enumerate(SETTINGS):
                labels = [adapter.solve(pair["input"], candidate["completion_mode"])
                          for pair in episode["train"]]
                if labels == [pair["output"] for pair in episode["train"]]:
                    survivors.append(rival)
            checked_settings += 1
            unique_survivors += survivors == [chosen]
        if inputs_by_setting[0] != inputs_by_setting[1]:
            raise AssertionError(f"settings changed the input bank for seed {seed}")

        minimum = adapter.generate(seed, SETTINGS[1], 2, 4)
        expected_train = [pair["output"] for pair in minimum["train"]]
        for rival in shortcut_rivals:
            shortcut_checked += 1
            shortcut_refuted += [rival(pair["input"]) for pair in minimum["train"]] != expected_train
            shortcut_query_disagreements += any(
                rival(pair["input"]) != pair["output"] for pair in minimum["test"]
            )

        episode = adapter.generate(seed, SETTINGS[1], 6, 4)
        for split in ("train", "test"):
            for pair in episode[split]:
                expected = pair["output"]
                alternative_pairs += 1
                differs_skip_a += expected != adapter.stage_b(pair["input"])
                differs_skip_b += expected != adapter.stage_a(pair["input"])
                singleton_pairs += _has_singleton(pair["input"])

    passed = (
        unique_survivors == checked_settings
        and differs_skip_a == alternative_pairs
        and differs_skip_b == alternative_pairs
        and singleton_pairs == alternative_pairs
        and shortcut_refuted == shortcut_checked
        and shortcut_query_disagreements == shortcut_checked
    )
    report = {
        "schema": "arcpuzzles-parametric-bounded-audit-v1",
        "task_id": "2fc4ca4ea6c4",
        "status": "pass" if passed else "fail",
        "seeds": list(seeds),
        "settings_checked": checked_settings,
        "minimum_demo_survivors": unique_survivors,
        "alternative_pairs_checked": alternative_pairs,
        "differs_from_skip_a": differs_skip_a,
        "differs_from_skip_b": differs_skip_b,
        "singleton_pairs": singleton_pairs,
        "shortcut_rivals": ["ignore_blockers", "connect_two_or_more"],
        "shortcut_rivals_checked": shortcut_checked,
        "shortcut_rivals_refuted_by_minimum_demos": shortcut_refuted,
        "shortcut_rivals_disagree_on_queries": shortcut_query_disagreements,
    }
    if destination is not None:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_audit(args.out)
    print(json.dumps(report, sort_keys=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
