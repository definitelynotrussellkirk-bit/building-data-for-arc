from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3] / "repo"
TASK = "89704f9047c0"
SOURCE = REPO / "generators" / TASK / "generator.py"
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
OUTDIR = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
assert spec and spec.loader
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)


def normalize(grid):
    return [[int(ch) for ch in row] if isinstance(row, str) else list(row) for row in grid]


def canonical_row():
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise RuntimeError("canonical task not found")


def profile_palette_rival(grid):
    analysis = G._analysis(grid)
    if analysis["errors"]:
        raise ValueError(analysis["errors"])
    profile = analysis["scene_profile"]
    if profile is None:
        raise ValueError("outside generated profile set")
    profile_index = G.SCENE_PROFILES.index(profile)
    colors = sorted(analysis["corners"])
    order = G._PALETTE_ORDERS[profile_index]
    palette = tuple(colors[index] for index in order)
    # Mirror the generator's exact-instance avoidance branch too.  The rival
    # still ignores the observed corner assignment; dimensions plus the color
    # set determine its proxy assignment.
    if (analysis["height"], analysis["width"], palette) in G._OFFICIAL_INPUT_SIGNATURES:
        palette = (palette[1], palette[0], palette[2], palette[3])
    proxy = G.full_grid(analysis["height"], analysis["width"], 0)
    h, w = analysis["height"], analysis["width"]
    proxy[0][0], proxy[0][w - 1], proxy[h - 1][0], proxy[h - 1][w - 1] = palette
    return G.rule_mirror(proxy)


sampled = 0
rival_fits = 0
orders_by_profile: dict[str, set[tuple[int, ...]]] = {name: set() for name in G.SCENE_PROFILES}
for band in ("easy", "medium", "hard"):
    for seed in range(20):
        for sample_index in range(8):
            grid = G.generate(seed, sample_index, difficulty=band)
            analysis = G._analysis(grid)
            if analysis["errors"]:
                raise AssertionError(analysis["errors"])
            sampled += 1
            orders_by_profile[analysis["scene_profile"]].add(tuple(analysis["rank_order"]))
            if profile_palette_rival(grid) == G.rule_mirror(grid):
                rival_fits += 1

row = canonical_row()
pairs = row["train"] + row["test"]
chosen = None
canonical_records = []
for pair_index, pair in enumerate(pairs):
    grid = normalize(pair["input"])
    expected = normalize(pair["output"])
    analysis = G._analysis(grid)
    rival = profile_palette_rival(grid)
    rec = {
        "pair_index": pair_index,
        "profile": analysis["scene_profile"],
        "corners": list(analysis["corners"]),
        "rank_order": list(analysis["rank_order"]),
        "rival_differs": rival != expected,
    }
    canonical_records.append(rec)
    if rival != expected and chosen is None:
        chosen = (pair_index, grid, expected, rival, rec)

if chosen is None:
    raise AssertionError("no lawful profile-conditioned palette counterexample found")

pair_index, counter_input, expected, rival, rec = chosen
input_path = OUTDIR / "counterexample-input.json"
input_path.write_text(json.dumps({"input": counter_input}, indent=2) + "\n", encoding="utf-8")
report = {
    "schema": "arc-audit-probe-v1",
    "task_id": TASK,
    "finding": "scene profile plus color set deterministically reveals corner-color assignment",
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "rule_hash": G.RULE_HASH,
    "ordinary_draws_checked": sampled,
    "profile_palette_rival_fits": rival_fits,
    "orders_by_profile": {key: [list(order) for order in sorted(value)] for key, value in orders_by_profile.items()},
    "fixed_profile_order_with_one_declared_collision_branch": True,
    "canonical_pairs": canonical_records,
    "counterexample": {
        "canonical_pair_index": pair_index,
        "profile": rec["profile"],
        "input": counter_input,
        "canonical_expected_output": expected,
        "profile_palette_rival_output": rival,
        "rival_differs": rival != expected,
        "apply_input": input_path.name,
    },
    "conclusion": (
        "A solver can ignore the observed corner-to-color assignment, sort the four colors, "
        "choose a profile-specific fixed permutation, and mirror the declared exact-instance "
        "avoidance swap. It fits every sampled ordinary draw but fails a lawful canonical "
        "input of the same generated profile."
    ),
}
(OUTDIR / "probe.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("task_id", "generator_sha256", "ordinary_draws_checked", "profile_palette_rival_fits", "fixed_profile_order_with_one_declared_collision_branch")}, indent=2))
