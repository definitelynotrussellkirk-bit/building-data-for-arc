"""Bounded deterministic self-review for the selection-mode family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_task_39ad_audit_prototype", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit(seed_count: int) -> dict:
    module = _load()
    checked_pairs = 0
    large_queries = 0
    observed_sizes: set[tuple[int, int]] = set()
    observed_lengths: set[int] = set()
    max_segments = 0
    for seed in range(seed_count):
        episodes = {mode: module.generate(seed, {"selection_mode": mode}, 6, 4)
                    for mode in ("all", "longest")}
        all_inputs = [pair["input"] for pair in episodes["all"]["train"] + episodes["all"]["test"]]
        long_inputs = [pair["input"] for pair in episodes["longest"]["train"] + episodes["longest"]["test"]]
        if all_inputs != long_inputs:
            raise AssertionError("input generation depends on private setting")
        for mode, episode in episodes.items():
            if module.fit_settings(episode["train"][:2]) != [{"selection_mode": mode}]:
                raise AssertionError("minimum demonstrations do not identify the setting")
            for demos in range(2, 7):
                prefix = module.generate(seed, {"selection_mode": mode}, demos, 4)
                if prefix["train"] != episode["train"][:demos] or prefix["test"] != episode["test"]:
                    raise AssertionError("demonstration count changed another stream")
            for queries in range(1, 5):
                prefix = module.generate(seed, {"selection_mode": mode}, 2, queries)
                if prefix["test"] != episode["test"][:queries]:
                    raise AssertionError("query stream is not prefix stable")
        for grid in all_inputs:
            segments = module._segments(grid)
            orientations = {orientation for orientation, _ in segments}
            lengths = [len(cells) for _, cells in segments]
            if orientations != {"h", "v"} or len(set(lengths)) < 2:
                raise AssertionError("scene lost orientation or length variation")
            if module.transform(grid, {"selection_mode": "all"}) == module.transform(
                grid, {"selection_mode": "longest"}
            ):
                raise AssertionError("settings agree on a generated scene")
            if module.orientation_only(grid, "h") in (
                module.transform(grid, {"selection_mode": "all"}),
                module.transform(grid, {"selection_mode": "longest"}),
            ):
                raise AssertionError("horizontal-only shortcut fits a generated label")
            if module.orientation_only(grid, "v") in (
                module.transform(grid, {"selection_mode": "all"}),
                module.transform(grid, {"selection_mode": "longest"}),
            ):
                raise AssertionError("vertical-only shortcut fits a generated label")
            observed_sizes.add((len(grid), len(grid[0])))
            observed_lengths.update(lengths)
            max_segments = max(max_segments, len(segments))
            checked_pairs += 1
        large = [grid for grid in all_inputs[-4:] if len(grid) == 30 and len(grid[0]) == 30]
        if len(large) != 1 or sum(len(cells) for _, cells in module._segments(large[0])) < 70:
            raise AssertionError("four-query bank lacks substantive 30x30 stress")
        large_queries += 1
    return {
        "schema": "arcpuzzles-task-parametric-self-review-v1",
        "task_id": module.TASK_ID,
        "status": "passed",
        "seed_count": seed_count,
        "episodes": seed_count * 2,
        "generated_pairs_checked": checked_pairs,
        "large_query_banks": large_queries,
        "observed_sizes": [list(size) for size in sorted(observed_sizes)],
        "observed_segment_lengths": sorted(observed_lengths),
        "maximum_segments_in_scene": max_segments,
        "checks": [
            "setting-independent matched inputs",
            "2..6 demonstration stream independence",
            "1..4 query prefix stability",
            "two-demo finite-setting identification",
            "mixed horizontal/vertical scenes",
            "all versus longest disagreement",
            "horizontal-only and vertical-only shortcut rejection",
            "one substantive 30x30 scene in every four-query bank",
        ],
        "limits": "Finite deterministic audit; it does not prove uniqueness against all conceivable rules.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 512:
        raise ValueError("--seeds must be in 1..512")
    result = audit(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "pairs": result["generated_pairs_checked"], "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
