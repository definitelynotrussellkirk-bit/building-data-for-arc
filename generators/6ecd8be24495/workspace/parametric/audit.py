"""Bounded repeatable audit for the 6ecd8be24495 parametric family.

The audit checks matched inputs, metric disagreement, local-majority rendering,
finite rival rejection, query diversity, and the 30x30 stress case.  It is a
scoped authoring check, not a substitute for protected-Racket qualification.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable, Any


HERE = Path(__file__).resolve().parent
TASK_ID = "6ecd8be24495"


def _load_family():
    source = HERE / "family.py"
    name = "_audit_family_6ecd8be24495_" + hashlib.sha256(str(source).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:  # pragma: no cover - import guard
        raise ImportError(f"cannot load adjacent family: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _freeze_grid(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def run_audit(seeds: Iterable[int]) -> dict[str, Any]:
    family = _load_family()
    seed_list = list(seeds)
    failures: list[dict[str, Any]] = []
    chamber_counts: set[int] = set()
    total_ranks: set[int] = set()
    distinct_ranks: set[int] = set()
    majority_colors: set[int] = set()
    query_shapes: set[tuple[int, int]] = set()
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    max_stress_changed = 0
    metric_disagreement_pairs = 0
    setting_episodes = 0
    generated_pairs = 0

    for seed in seed_list:
        episodes: dict[str, dict[str, Any]] = {}
        for metric in ("total_seeds", "distinct_colors"):
            setting_episodes += 1
            settings = {"selection_metric": metric}
            try:
                episode = family.generate(seed, settings, 2, 4)
                episodes[metric] = episode
                check = family.teaching_check(episode, settings)
                if check["survivors"] != [settings] or check["surviving_rivals"]:
                    failures.append({"seed": seed, "metric": metric, "kind": "teaching", "detail": check})
                local_inputs: set[tuple[tuple[int, ...], ...]] = set()
                for split in ("train", "test"):
                    for pair in episode[split]:
                        generated_pairs += 1
                        frozen = _freeze_grid(pair["input"])
                        local_inputs.add(frozen)
                        unique_inputs.add(frozen)
                        if pair["output"] != family.transform(pair["input"], settings):
                            failures.append({"seed": seed, "metric": metric, "kind": "python_label_mismatch"})
                        facts = family.analyze(pair["input"])
                        chamber_counts.add(len(facts["chambers"]))
                        total_ranks.add(facts["total_winner"])
                        distinct_ranks.add(facts["distinct_winner"])
                        if facts["total_winner"] != facts["distinct_winner"]:
                            metric_disagreement_pairs += 1
                        selected_rank = facts["total_winner"] if metric == "total_seeds" else facts["distinct_winner"]
                        selected = facts["chambers"][selected_rank]
                        majority_colors.add(selected["majority_color"])
                        changed = {
                            (r, c)
                            for r in range(len(pair["input"]))
                            for c in range(len(pair["input"][0]))
                            if pair["input"][r][c] != pair["output"][r][c]
                        }
                        if not changed or not changed <= set(selected["cells"]):
                            failures.append({"seed": seed, "metric": metric, "kind": "wrong_changed_cells"})
                        elif {pair["output"][r][c] for r, c in changed} != {selected["majority_color"]}:
                            failures.append({"seed": seed, "metric": metric, "kind": "wrong_fill_color"})
                        if split == "test":
                            shape = (len(pair["input"]), len(pair["input"][0]))
                            query_shapes.add(shape)
                            if shape == (30, 30):
                                max_stress_changed = max(max_stress_changed, len(changed))
                if len(local_inputs) != 6:
                    failures.append({"seed": seed, "metric": metric, "kind": "duplicate_input", "count": len(local_inputs)})
            except Exception as exc:
                failures.append({"seed": seed, "metric": metric, "kind": "exception", "detail": f"{type(exc).__name__}: {exc}"})

        if set(episodes) == {"total_seeds", "distinct_colors"}:
            for split in ("train", "test"):
                left = [pair["input"] for pair in episodes["total_seeds"][split]]
                right = [pair["input"] for pair in episodes["distinct_colors"][split]]
                if left != right:
                    failures.append({"seed": seed, "kind": "unmatched_inputs", "split": split})
                for a, b in zip(episodes["total_seeds"][split], episodes["distinct_colors"][split]):
                    if a["output"] == b["output"]:
                        failures.append({"seed": seed, "kind": "settings_equivalent", "split": split})

    # Every generated pair is counted once per setting above, so all should
    # exhibit a selector disagreement in this matched-input grammar.
    if metric_disagreement_pairs != generated_pairs:
        failures.append({
            "kind": "metric_disagreement_coverage",
            "observed": metric_disagreement_pairs,
            "expected": generated_pairs,
        })

    return {
        "schema": "arc-review-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "scope": "Finite Python mirror/rival audit; protected-Racket qualification remains separate.",
        "seeds": seed_list,
        "seed_count": len(seed_list),
        "setting_episodes": setting_episodes,
        "generated_pairs": generated_pairs,
        "unique_input_count": len(unique_inputs),
        "metric_disagreement_pairs": metric_disagreement_pairs,
        "query_shapes": [list(shape) for shape in sorted(query_shapes)],
        "total_selected_ranks": sorted(total_ranks),
        "distinct_selected_ranks": sorted(distinct_ranks),
        "majority_colors": sorted(majority_colors),
        "chamber_counts": sorted(chamber_counts),
        "max_30x30_changed_cells": max_stress_changed,
        "program_sha256": {
            metric: hashlib.sha256(family.program({"selection_metric": metric}).encode()).hexdigest()
            for metric in ("total_seeds", "distinct_colors")
        },
        "failure_count": len(failures),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=40, help="audit seeds 0..N-1")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    report = run_audit(range(args.seeds))
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 1 if report["failure_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
