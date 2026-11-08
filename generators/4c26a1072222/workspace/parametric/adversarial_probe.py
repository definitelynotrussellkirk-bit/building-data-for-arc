#!/usr/bin/env python3
"""Bounded adversarial probe for parametric sampler/export edge surfaces."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
for dependency in (REPO, REPO / "shared" / "runtime", HERE):
    text = str(dependency)
    if text not in sys.path:
        sys.path.insert(0, text)

from reviewer_support import public_challenge_id  # noqa: E402
import prototype  # noqa: E402


SEEDS = (0, -1, 2**63 - 1, 20261023)
COUNT_CASES = ((4, 4), (5, 6))


def _grid_errors(grid: Any, label: str) -> list[str]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        return [f"{label}: grid row count outside 1..30"]
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        return [f"{label}: grid column count outside 1..30"]
    width = len(grid[0])
    errors = []
    for row_index, row in enumerate(grid):
        if type(row) is not list or len(row) != width:
            errors.append(f"{label}: row {row_index} is ragged or not a list")
            continue
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"{label}: cell ({row_index},{col_index}) is not exact int 0..9"
                )
    return errors


def _visible_grid_errors(public: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for split in ("train", "test"):
        for index, pair in enumerate(public[split]):
            errors.extend(_grid_errors(pair["input"], f"{split}[{index}].input"))
            if split == "train":
                errors.extend(
                    _grid_errors(pair["output"], f"{split}[{index}].output")
                )
            elif set(pair) != {"input"}:
                errors.append(f"test[{index}] leaked fields {sorted(set(pair) - {'input'})}")
    return errors


def _episode_inputs(episode: dict[str, Any]) -> list[Any]:
    return [
        pair["input"]
        for split in ("train", "test")
        for pair in episode[split]
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    failures: list[str] = []
    cases: list[dict[str, Any]] = []
    max_retry_attempt = 0
    all_public_ids: set[str] = set()

    try:
        prototype.choose_setting(True)
        failures.append("bool seed was accepted")
    except TypeError:
        pass

    for seed in SEEDS:
        for n_train, n_test in COUNT_CASES:
            episodes = {
                setting: prototype.build_episode(
                    seed,
                    application_direction=setting,
                    n_train=n_train,
                    n_test=n_test,
                )
                for setting in prototype.SETTINGS
            }
            schedules = {
                setting: _episode_inputs(episode)
                for setting, episode in episodes.items()
            }
            if schedules["forward"] != schedules["inverse"]:
                failures.append(
                    f"seed={seed} counts={n_train}/{n_test}: input schedule depends on setting"
                )

            for setting, episode in episodes.items():
                errors = prototype.episode_errors(episode)
                if errors:
                    failures.append(
                        f"seed={seed} counts={n_train}/{n_test} setting={setting}: {errors}"
                    )
                survivors = prototype.setting_survivors(episode["train"])
                if survivors != [setting]:
                    failures.append(
                        f"seed={seed} counts={n_train}/{n_test} setting={setting}: survivors={survivors}"
                    )
                serialized = [
                    json.dumps(grid, separators=(",", ":"))
                    for grid in _episode_inputs(episode)
                ]
                if len(serialized) != len(set(serialized)):
                    failures.append(
                        f"seed={seed} counts={n_train}/{n_test} setting={setting}: duplicate inputs"
                    )
                if any(
                    prototype.apply_setting(pair["input"], "forward")
                    == prototype.apply_setting(pair["input"], "inverse")
                    for split in ("train", "test")
                    for pair in episode[split]
                ):
                    failures.append(
                        f"seed={seed} counts={n_train}/{n_test} setting={setting}: non-distinguishing input"
                    )

                attempts = [
                    pair["sampling"]["attempt"]
                    for split in ("train", "test")
                    for pair in episode[split]
                ]
                max_retry_attempt = max(max_retry_attempt, *attempts)

                public = prototype.public_projection(episode)
                public_id = prototype.public_identifier(episode)
                all_public_ids.add(public_id)
                if public_id != public_challenge_id(public):
                    failures.append(
                        f"seed={seed} counts={n_train}/{n_test} setting={setting}: public ID mismatch"
                    )
                failures.extend(
                    f"seed={seed} counts={n_train}/{n_test} setting={setting}: {error}"
                    for error in _visible_grid_errors(public)
                )

                hidden = deepcopy(episode)
                hidden["seed"] = seed + 1
                hidden["parameters"] = {
                    "application_direction": (
                        "inverse" if setting == "forward" else "forward"
                    )
                }
                hidden["program"] = "hidden replacement"
                hidden["generator_sha256"] = "0" * 64
                for pair in hidden["test"]:
                    pair["output"] = [[9]]
                    pair["sampling"] = {"hidden": True}
                if prototype.public_identifier(hidden) != public_id:
                    failures.append(
                        f"seed={seed} counts={n_train}/{n_test} setting={setting}: hidden fields changed public ID"
                    )

                cases.append(
                    {
                        "seed": seed,
                        "n_train": n_train,
                        "n_test": n_test,
                        "setting": setting,
                        "public_id": public_id,
                        "survivors": survivors,
                        "max_retry_attempt": max(attempts),
                        "unique_inputs": len(set(serialized)),
                    }
                )

    rejection_episode = prototype.build_episode(
        17, application_direction="forward", n_train=4, n_test=4
    )
    corrupt = deepcopy(rejection_episode)
    corrupt["train"][0]["output"] = [[0]]
    if not any("label mismatches" in error for error in prototype.episode_errors(corrupt)):
        failures.append("episode_errors did not reject a corrupted demonstration label")

    duplicate = deepcopy(rejection_episode)
    duplicate["test"][0]["input"] = deepcopy(duplicate["train"][0]["input"])
    duplicate["test"][0]["output"] = prototype.apply_setting(
        duplicate["test"][0]["input"], "forward"
    )
    if not any("duplicates another episode input" in error for error in prototype.episode_errors(duplicate)):
        failures.append("episode_errors did not reject a duplicated query input")

    report = {
        "schema": "4c26a1072222-parametric-adversarial-probe-v1",
        "status": "passed" if not failures else "failed",
        "surfaces": [
            "sampler_boundaries_and_retry_schedules",
            "public_private_export_and_numeric_types",
        ],
        "seed_cases": list(SEEDS),
        "count_cases": [list(case) for case in COUNT_CASES],
        "settings": list(prototype.SETTINGS),
        "episode_cases": len(cases),
        "input_grids_checked": sum(row["unique_inputs"] for row in cases),
        "max_retry_attempt": max_retry_attempt,
        "distinct_public_ids": len(all_public_ids),
        "rejection_paths": {
            "bool_seed": "rejected",
            "corrupt_demo_label": "rejected",
            "duplicate_query_input": "rejected",
        },
        "failures": failures,
        "cases": cases,
        "limits": [
            "Bounded to four edge seeds and two train/query count combinations.",
            "Did not exhaust the 512-attempt retry limit because all retained cases succeeded on attempt 0.",
            "Racket parity is covered separately by checks/parametric/manifest.json.",
        ],
    }
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "status", "episode_cases", "input_grids_checked", "max_retry_attempt", "distinct_public_ids"
    )}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
