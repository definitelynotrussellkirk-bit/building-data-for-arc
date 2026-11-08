"""Bounded teaching, shortcut, and causal audit for c878420172c2."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SETTINGS = (
    {"overlap_mode": "all_overlap"},
    {"overlap_mode": "largest_component"},
)


def _load_adapter():
    path = HERE / "adapter.py"
    spec = importlib.util.spec_from_file_location("audit_c878_adapter", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load adjacent adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _paint(cells, height: int, width: int):
    out = [[0] * width for _ in range(height)]
    for row, column in cells:
        out[row][column] = 8
    return out


def _remove_only_singletons(adapter, grid):
    retained = set()
    for component in adapter.components(adapter.stage_a(grid)):
        if len(component) > 1:
            retained.update(component)
    return _paint(retained, len(grid), len(grid[0]))


def _largest_eight_connected(adapter, grid):
    remaining = set(adapter.stage_a(grid))
    parts = []
    while remaining:
        first = min(remaining)
        component = {first}
        stack = [first]
        remaining.remove(first)
        while stack:
            row, column = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    neighbor = (row + dr, column + dc)
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        component.add(neighbor)
                        stack.append(neighbor)
        parts.append(component)
    parts.sort(key=lambda part: (-len(part), min(part)))
    return _paint(parts[0] if parts else set(), len(grid), len(grid[0]))


def run_audit(destination: Path | str | None = None, *, seeds=(0, 17, 29, 63)) -> dict:
    adapter = _load_adapter()
    checked_settings = 0
    unique_survivors = 0
    alternative_pairs = 0
    differs_skip_a = 0
    unique_largest = 0
    nontrivial_secondary = 0
    singleton_deletion_disagreements = 0
    eight_connectivity_disagreements = 0
    shortcut_checked = 0
    shortcut_refuted = 0
    shortcut_query_disagreements = 0

    shortcut_rivals = (
        lambda grid: _remove_only_singletons(adapter, grid),
        lambda grid: _largest_eight_connected(adapter, grid),
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
                labels = [adapter.solve(pair["input"], candidate["overlap_mode"])
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
                intersection = adapter.stage_a(pair["input"])
                parts = adapter.components(intersection)
                sizes = [len(part) for part in parts]
                alternative_pairs += 1
                unique_largest += len(sizes) >= 2 and sizes[0] > sizes[1]
                nontrivial_secondary += len(sizes) >= 2 and sizes[1] > 1
                wrong = adapter.stage_b(
                    adapter.normalize_color(pair["input"], 2),
                    len(pair["input"]), len(pair["input"][0]),
                )
                differs_skip_a += wrong != pair["output"]
                singleton_deletion_disagreements += (
                    _remove_only_singletons(adapter, pair["input"]) != pair["output"]
                )
                eight_connectivity_disagreements += (
                    _largest_eight_connected(adapter, pair["input"]) != pair["output"]
                )

    passed = (
        unique_survivors == checked_settings
        and unique_largest == alternative_pairs
        and nontrivial_secondary == alternative_pairs
        and differs_skip_a == alternative_pairs
        and singleton_deletion_disagreements == alternative_pairs
        and eight_connectivity_disagreements == alternative_pairs
        and shortcut_refuted == shortcut_checked
        and shortcut_query_disagreements == shortcut_checked
    )
    report = {
        "schema": "arcpuzzles-parametric-bounded-audit-v1",
        "task_id": "c878420172c2",
        "status": "pass" if passed else "fail",
        "seeds": list(seeds),
        "settings_checked": checked_settings,
        "minimum_demo_survivors": unique_survivors,
        "alternative_pairs_checked": alternative_pairs,
        "differs_from_skip_a": differs_skip_a,
        "unique_largest_intermediates": unique_largest,
        "nontrivial_secondary_components": nontrivial_secondary,
        "singleton_deletion_disagreements": singleton_deletion_disagreements,
        "eight_connectivity_disagreements": eight_connectivity_disagreements,
        "shortcut_rivals": ["remove_only_singletons", "eight_connected_largest"],
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
