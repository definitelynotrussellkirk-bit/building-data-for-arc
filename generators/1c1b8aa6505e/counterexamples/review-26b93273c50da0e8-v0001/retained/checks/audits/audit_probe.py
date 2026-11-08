from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "repo" / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))


def load(task_id: str):
    path = ROOT / "repo" / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_rows(task_id: str):
    path = ROOT / "repo" / "shared" / "data" / "canonical" / "puzzles.jsonl"
    rows = []
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            rows.append(row)
    return rows


def pairs(rows):
    out = []
    for row in rows:
        out.extend(row.get("train") or [])
        test = row.get("test") or []
        out.extend([test] if isinstance(test, dict) else test)
    return [pair for pair in out if "output" in pair]


def b7_probe():
    task = "b7e4aaffabac"
    gen = load(task)
    profile_counts = Counter()
    orientations = Counter()
    checked = 0
    for band in ("easy", "medium", "hard"):
        for profile in gen.SCENE_PROFILES:
            for seed in range(20):
                grid = gen.generate(seed, 37 * seed + 5, difficulty=band, scene_profile=profile)
                analysis = gen._analysis(grid)
                assert analysis["errors"] == [], (band, profile, seed, analysis["errors"])
                assert gen.observe_overrides(grid) == {"scene_profile": profile}
                assert gen.rule_mirror(grid) == analysis["output"]
                changed = {
                    (r, c)
                    for r in range(len(grid))
                    for c in range(len(grid[0]))
                    if grid[r][c] != analysis["output"][r][c]
                }
                assert changed == analysis["bridge_cells"]
                profile_counts[profile] += 1
                orientations[analysis["orientation"]] += 1
                checked += 1

    canonical = pairs(canonical_rows(task))
    for pair in canonical:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert gen.canonical_profile_signature(pair["input"]) in gen.PUBLIC_PROFILES

    return {
        "status": "no_issue_found",
        "generated_cases_checked": checked,
        "canonical_pairs_checked": len(canonical),
        "profiles": dict(sorted(profile_counts.items())),
        "orientations": dict(sorted(orientations.items())),
        "checks": [
            "self_check/analysis accepted every generated case",
            "scene_profile override round-tripped",
            "Python audit rule matched exact bridge cells",
            "all canonical pairs matched the rule and public profiles",
        ],
    }


def min_side_shortcut(gen, grid):
    counts = tuple(gen._analyze(grid)["counts"])
    red_min = min(counts[0], counts[1])
    yellow_min = min(counts[2], counts[3])
    # Generated profiles never tie. Keep a deterministic tie break for canonical probing.
    winner = 2 if red_min <= yellow_min else 4
    return [[winner, winner], [winner, winner]]


def one_c_probe():
    task = "1c1b8aa6505e"
    gen = load(task)
    generated = []
    window_failures = []
    for band in ("easy", "medium", "hard"):
        for index in range(120):
            grid = gen.generate(1000 + index, index, difficulty=band)
            expected = gen.rule_mirror(grid)
            generated.append(
                {
                    "band": band,
                    "index": index,
                    "counts": list(gen._analyze(grid)["counts"]),
                    "shortcut_matches": min_side_shortcut(gen, grid) == expected,
                }
            )
    assert all(item["shortcut_matches"] for item in generated)

    # Every ordinary 3-demo lesson and its following query remains shortcut-solvable.
    for band in ("easy", "medium", "hard"):
        for start in range(40):
            lesson = [gen.generate(4242, i, difficulty=band) for i in range(start, start + 4)]
            if not all(min_side_shortcut(gen, grid) == gen.rule_mirror(grid) for grid in lesson):
                window_failures.append({"band": band, "start": start})
    assert not window_failures

    canonical_failures = []
    canonical = pairs(canonical_rows(task))
    for i, pair in enumerate(canonical):
        predicted = min_side_shortcut(gen, pair["input"])
        if predicted != pair["output"]:
            canonical_failures.append(
                {
                    "pair_index": i,
                    "counts": list(gen._analyze(pair["input"])["counts"]),
                    "shortcut_output_color": predicted[0][0],
                    "authoritative_output_color": pair["output"][0][0],
                }
            )
    assert canonical_failures

    return {
        "status": "reproduced_shortcut",
        "shortcut": "choose the color with smaller min(top_count, bottom_count), tie -> red",
        "generated_cases_checked": len(generated),
        "generated_matches": sum(item["shortcut_matches"] for item in generated),
        "four_example_windows_checked": 3 * 40,
        "window_failures": window_failures,
        "canonical_pairs_checked": len(canonical),
        "canonical_counterexamples": canonical_failures,
        "root_cause": (
            "Every COUNT_PROFILES tuple gives the authoritative winner the smaller "
            "minimum side count; adding the common count_scale preserves that ordering."
        ),
    }


result = {
    "b7e4aaffabac": b7_probe(),
    "1c1b8aa6505e": one_c_probe(),
}
print(json.dumps(result, indent=2, sort_keys=True))
