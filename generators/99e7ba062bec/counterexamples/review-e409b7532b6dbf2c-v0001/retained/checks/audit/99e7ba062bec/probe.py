from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3] / "repo"
TASK = "99e7ba062bec"
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


row = canonical_row()
pairs = row["train"] + row["test"]
ambiguous = []
chosen = None
for pair_index, pair in enumerate(pairs):
    grid = normalize(pair["input"])
    expected = normalize(pair["output"])
    analysis = G._analyze(grid)
    matches = tuple(analysis["facts"]["matches"])
    if len(matches) > 1:
        first = G._apply_grid(analysis["facts"]["c"], matches[0])
        last = G._apply_grid(analysis["facts"]["c"], matches[-1])
        record = {
            "pair_index": pair_index,
            "matches": list(matches),
            "first_equals_expected": first == expected,
            "last_equals_expected": last == expected,
            "first_output": first,
            "last_output": last,
        }
        ambiguous.append(record)
        if first == expected and last != expected and chosen is None:
            chosen = (pair_index, grid, expected, record)

if chosen is None:
    raise AssertionError("no canonical first-match counterexample found")

sampled = 0
rival_fits = 0
unique_match_draws = 0
match_histogram: dict[str, int] = {}
for band in ("easy", "medium", "hard"):
    for seed in (0, 1, 2, 17, 91, 31337):
        for sample_index in range(28):
            grid = G.generate(seed, sample_index, difficulty=band)
            analysis = G._analyze(grid)
            if analysis["errors"]:
                raise AssertionError(analysis["errors"])
            matches = tuple(analysis["facts"]["matches"])
            sampled += 1
            match_histogram[str(matches)] = match_histogram.get(str(matches), 0) + 1
            unique_match_draws += int(len(matches) == 1)
            # Rival: use the LAST matching transform rather than the canonical first.
            rival = G._apply_grid(analysis["facts"]["c"], matches[-1])
            if rival == G.rule_mirror(grid):
                rival_fits += 1

pair_index, counter_input, expected, record = chosen
input_path = OUTDIR / "counterexample-input.json"
input_path.write_text(json.dumps({"input": counter_input}, indent=2) + "\n", encoding="utf-8")
report = {
    "schema": "arc-audit-probe-v1",
    "task_id": TASK,
    "finding": "ordinary generation never teaches canonical first-match precedence",
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "rule_hash": G.RULE_HASH,
    "ordinary_draws_checked": sampled,
    "last_match_rival_fits": rival_fits,
    "ordinary_unique_match_draws": unique_match_draws,
    "all_ordinary_draws_unique_match": unique_match_draws == sampled,
    "ordinary_match_histogram": match_histogram,
    "canonical_ambiguous_pairs": ambiguous,
    "counterexample": {
        "canonical_pair_index": pair_index,
        "input": counter_input,
        "canonical_expected_output": expected,
        "matching_codes": record["matches"],
        "last_match_rival_output": record["last_output"],
        "rival_differs": record["last_output"] != expected,
        "apply_input": input_path.name,
    },
    "conclusion": (
        "A solver that uses the last matching transform agrees on every sampled ordinary "
        "draw because generated A masks have a unique match, but fails a lawful canonical "
        "pair where code-order precedence changes the output."
    ),
}
(OUTDIR / "probe.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("task_id", "generator_sha256", "ordinary_draws_checked", "last_match_rival_fits", "all_ordinary_draws_unique_match")}, indent=2))
