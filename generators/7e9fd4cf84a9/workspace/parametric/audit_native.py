"""Bounded, replayable authoring audit for the 7e9fd4cf84a9 native family.

This is reviewer tooling, not an owner-acceptance claim.  It exercises every
setting and every supported demonstration count, checks matched input streams,
finite teaching rivals, labels, distractor preservation, and the 30x30 query.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADAPTER = _load(HERE / "adapter.py", "_arc_7e9fd4cf84a9_audit_adapter")
BASE = _load(TASK_HOME / "generator.py", "_arc_7e9fd4cf84a9_audit_base")
SETTINGS = (
    {"fill_scope": "all_rectangles"},
    {"fill_scope": "largest_only"},
)


def _grid_hash(grid) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def run_audit(seed_count: int = 8) -> dict:
    if type(seed_count) is not int or not 1 <= seed_count <= 64:
        raise ValueError("seed_count must be an exact integer in 1..64")
    failures: list[dict] = []
    episodes = labeled_pairs = stress_cases = query_stability = teaching_checks = 0
    input_hashes: set[str] = set()
    dimensions: set[tuple[int, int]] = set()

    def fail(seed, setting, demos, check, detail):
        failures.append({
            "seed": seed,
            "settings": setting,
            "demos": demos,
            "check": check,
            "detail": detail,
        })

    for seed in range(seed_count):
        setting_episodes = {}
        for setting in SETTINGS:
            reference_queries = None
            for demos in range(2, 7):
                episodes += 1
                try:
                    episode = ADAPTER.generate(seed, setting, demos, 4)
                except Exception as exc:  # retained evidence, not silent retry
                    fail(seed, setting, demos, "generate", repr(exc))
                    continue
                pairs = episode["train"] + episode["test"]
                labeled_pairs += len(pairs)
                if len(episode["train"]) != demos or len(episode["test"]) != 4:
                    fail(seed, setting, demos, "counts", [len(episode["train"]), len(episode["test"])])
                queries = [pair["input"] for pair in episode["test"]]
                if reference_queries is None:
                    reference_queries = queries
                elif queries != reference_queries:
                    fail(seed, setting, demos, "query_bank_stability", "queries changed with demos")
                query_stability += 1
                for pair_index, pair in enumerate(pairs):
                    grid = pair["input"]
                    input_hashes.add(_grid_hash(grid))
                    dimensions.add((len(grid), len(grid[0])))
                    errors = BASE.self_check(grid)
                    if errors:
                        fail(seed, setting, demos, "base_self_check", {"pair": pair_index, "errors": errors})
                    actual = ADAPTER.solve(grid, setting)
                    if actual != pair["output"]:
                        fail(seed, setting, demos, "python_label", {"pair": pair_index})
                    for r, c, color in BASE.analyze_scene(grid)["distractor_cells"]:
                        if pair["output"][r][c] != color:
                            fail(seed, setting, demos, "distractor_preservation", {"pair": pair_index, "cell": [r, c]})
                stress = [pair for pair in episode["test"]
                          if len(pair["input"]) == 30 and len(pair["input"][0]) == 30]
                if len(stress) != 1:
                    fail(seed, setting, demos, "stress_count", len(stress))
                else:
                    stress_cases += 1
                    analysis = BASE.analyze_scene(stress[0]["input"])
                    areas = [h * w for h, w in analysis["rectangle_shapes"]]
                    nonzero = sum(value != 0 for row in stress[0]["input"] for value in row)
                    if len(areas) < 5 or areas.count(max(areas)) != 1 or nonzero < 100:
                        fail(seed, setting, demos, "stress_substance", {"areas": areas, "nonzero": nonzero})
                if demos == 2:
                    teaching_checks += 1
                    survivors = []
                    for candidate in SETTINGS:
                        if all(ADAPTER.solve(pair["input"], candidate) == pair["output"]
                               for pair in episode["train"]):
                            survivors.append(candidate)
                    if survivors != [setting]:
                        fail(seed, setting, demos, "setting_survivor", survivors)
                    rival_survivors = ADAPTER.teaching_survivors(
                        [pair["input"] for pair in episode["train"]], setting)
                    if rival_survivors:
                        fail(seed, setting, demos, "named_rival_survivors", rival_survivors)
                setting_episodes[(setting["fill_scope"], demos)] = episode

        for demos in range(2, 7):
            a = setting_episodes.get(("all_rectangles", demos))
            b = setting_episodes.get(("largest_only", demos))
            if a and b:
                a_inputs = [pair["input"] for pair in a["train"] + a["test"]]
                b_inputs = [pair["input"] for pair in b["train"] + b["test"]]
                if a_inputs != b_inputs:
                    fail(seed, {"cross_setting": True}, demos, "matched_inputs", "input streams differ")

    return {
        "schema": "arcpuzzles-native-parametric-bounded-audit-v1",
        "task_id": "7e9fd4cf84a9",
        "status": "passed" if not failures else "failed",
        "seed_count": seed_count,
        "settings": len(SETTINGS),
        "demonstration_counts": [2, 3, 4, 5, 6],
        "queries_per_episode": 4,
        "episodes": episodes,
        "labeled_pairs": labeled_pairs,
        "query_bank_stability_checks": query_stability,
        "two_demo_teaching_checks": teaching_checks,
        "substantive_30x30_cases": stress_cases,
        "unique_input_grids": len(input_hashes),
        "dimensions": [list(value) for value in sorted(dimensions)],
        "failures": failures,
        "limits": "Finite reviewer-authored census only; owner source review and admission remain separate.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-count", type=int, default=8)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_audit(args.seed_count)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
