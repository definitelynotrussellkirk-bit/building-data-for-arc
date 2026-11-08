"""Bounded, reproducible self-review for the 0d27a69b5a98 family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

HERE = Path(__file__).resolve().parent
_FAMILY_NAME = "_0d27a69b5a98_audit_family"
_spec = importlib.util.spec_from_file_location(_FAMILY_NAME, HERE / "family.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("unable to load family.py")
family = importlib.util.module_from_spec(_spec)
sys.modules[_FAMILY_NAME] = family
_spec.loader.exec_module(family)


def run_audit(seeds: Iterable[int] = range(32)) -> dict:
    tested_seeds = list(seeds)
    failures: list[dict] = []
    winner_colors: set[int] = set()
    winner_ranks: set[int] = set()
    orientations: set[str] = set()
    pair_count = 0
    episode_count = 0
    wrong_order_disagreements = 0
    counterexample = None
    stress_minimums = {
        "non_axis_foreground": 10**9,
        "completed_non_axis_foreground": 10**9,
        "color_count": 10**9,
    }

    for seed in tested_seeds:
        canonical = family.generate_episode(seed, "canonical", demos=6, queries=4)
        highlighted = family.generate_episode(
            seed, "largest_completed_color_highlight", demos=6, queries=4
        )
        episode_count += 2
        canonical_pairs = canonical["train"] + canonical["test"]
        highlighted_pairs = highlighted["train"] + highlighted["test"]
        if [p["input"] for p in canonical_pairs] != [p["input"] for p in highlighted_pairs]:
            failures.append({"seed": seed, "kind": "setting_changed_input_bank"})
        for index, (base, composed) in enumerate(zip(canonical_pairs, highlighted_pairs)):
            pair_count += 2
            grid = base["input"]
            trace = family.trace(grid)
            winner_colors.add(trace["post_winner_color"])
            winner_ranks.add(trace["post_winner_original_rank"])
            orientations.add(trace["axis_orientation"])
            if trace["pre_winner_color"] == trace["post_winner_color"]:
                failures.append({"seed": seed, "index": index, "kind": "no_winner_swap"})
            if base["output"] != family.solve(grid, "canonical"):
                failures.append({"seed": seed, "index": index, "kind": "canonical_label"})
            if composed["output"] != family.solve(grid, "largest_completed_color_highlight"):
                failures.append({"seed": seed, "index": index, "kind": "composed_label"})
            wrong = family.solve_wrong_order(grid)
            if wrong != composed["output"]:
                wrong_order_disagreements += 1
                if counterexample is None:
                    counterexample = {
                        "seed": seed,
                        "split": "train" if index < 6 else "test",
                        "index": index if index < 6 else index - 6,
                        "input": grid,
                        "intermediate": trace["intermediate"],
                        "expected": composed["output"],
                        "wrong_order": wrong,
                        "pre_counts": trace["pre_counts"],
                        "post_counts": trace["post_counts"],
                        "pre_winner_color": trace["pre_winner_color"],
                        "post_winner_color": trace["post_winner_color"],
                    }
            else:
                failures.append({"seed": seed, "index": index, "kind": "wrong_order_agreed"})

        stress = family.trace(canonical["test"][3]["input"])
        for key in stress_minimums:
            stress_minimums[key] = min(stress_minimums[key], stress[key])

        demos = highlighted["train"]
        for color in range(1, 8):
            if all(family.solve_fixed_color(pair["input"], color) == pair["output"] for pair in demos):
                failures.append({"seed": seed, "kind": "fixed_color_shortcut", "color": color})
        for rank in range(1, 7):
            if all(
                family.solve_fixed_original_rank(pair["input"], rank) == pair["output"]
                for pair in demos
            ):
                failures.append({"seed": seed, "kind": "fixed_rank_shortcut", "rank": rank})

    if counterexample is None:
        failures.append({"kind": "no_counterexample"})
    return {
        "schema": "arcpuzzles-parametric-self-review-v1",
        "task_id": family.TASK_ID,
        "scope": "finite deterministic audit; no universal claim",
        "tested_seeds": tested_seeds,
        "settings": list(family.MODES),
        "episode_count": episode_count,
        "pair_count": pair_count,
        "wrong_order_disagreements": wrong_order_disagreements,
        "winner_color_count": len(winner_colors),
        "winner_rank_count": len(winner_ranks),
        "winner_colors": sorted(winner_colors),
        "winner_ranks": sorted(winner_ranks),
        "axis_orientations": sorted(orientations),
        "stress_minimums": stress_minimums,
        "failures": failures,
        "counterexample": counterexample,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument(
        "--out",
        type=Path,
        default=HERE / "evidence" / "current" / "self-review.json",
    )
    args = parser.parse_args()
    if not 1 <= args.seeds <= 256:
        parser.error("--seeds must be in [1, 256]")
    report = run_audit(range(args.seeds))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(args.out),
        "failures": len(report["failures"]),
        "episodes": report["episode_count"],
        "pairs": report["pair_count"],
    }, sort_keys=True))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
