"""Bounded findings-only audit of source geometry and declared grid overrides.

Run prepare/verify from WORK/repo. Labels come from public arcpuzzles apply.
Only matching canonical task rows are read. No target source is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

TASK = "77181d1aa16c"
HERE = Path(__file__).resolve().parent


def root():
    for ancestor in [HERE, *HERE.parents]:
        for candidate in (ancestor, ancestor / "repo", ancestor / "WORK" / "repo"):
            if (candidate / "generators" / TASK / "generator.py").is_file():
                return candidate
    raise RuntimeError("cannot find packet repository")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def load():
    repo = root()
    sys.path.insert(0, str(repo / "shared/runtime"))
    source = repo / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("audit_77181d1aa16c_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    return gen, source


def largest_rect(grid):
    """Independent prefix-sum implementation preserving canonical scan order."""
    h, w = len(grid), len(grid[0])
    zeros = [[0] * (w + 1) for _ in range(h + 1)]
    for r in range(h):
        for c in range(w):
            zeros[r + 1][c + 1] = zeros[r][c + 1] + zeros[r + 1][c] - zeros[r][c] + (grid[r][c] == 0)
    best = (0, 0, 0, 0, 0)
    for r1 in range(h):
        for r2 in range(r1, h):
            for c1 in range(w):
                for c2 in range(c1, w):
                    area = (r2 - r1 + 1) * (c2 - c1 + 1)
                    holes = zeros[r2 + 1][c2 + 1] - zeros[r1][c2 + 1] - zeros[r2 + 1][c1] + zeros[r1][c1]
                    if area > best[0] and not holes:
                        best = (area, r1, c1, r2, c2)
    return best[1:]


def solve(grid, *, last_indicator=False):
    """Oracle diagnostic plus rival: later same-role indicators take precedence."""
    r1, c1, r2, c2 = largest_rect(grid)
    ph, pw = r2 - r1 + 1, c2 - c1 + 1
    pattern = [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]
    colors = Counter(value for row in pattern for value in row)
    ranked = sorted(colors, key=lambda color: (-colors[color], color))
    assert len(ranked) == 2 and colors[ranked[0]] > colors[ranked[1]]
    def block(r, c):
        return 2 * (r >= r1 + ph) + (c >= c1 + pw)
    def role(r, c):
        lr = r - (r1 + ph if r >= r1 + ph else r1)
        lc = c - (c1 + pw if c >= c1 + pw else c1)
        if not (0 <= lr < ph and 0 <= lc < pw):
            return None
        return pattern[ph - 1 - lr if r >= r1 + ph else lr][pw - 1 - lc if c >= c1 + pw else lc]
    mappings = {}
    indicators = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 or (r1 <= r <= r2 and c1 <= c <= c2):
                continue
            descriptor = (block(r, c), role(r, c))
            indicators.append({"position": [r, c], "block": descriptor[0], "role": descriptor[1], "color": value})
            if last_indicator or descriptor not in mappings:
                mappings[descriptor] = value
    result = []
    for r, row in enumerate(grid):
        target = []
        for c, _ in enumerate(row):
            value = role(r, c)
            target.append(0 if value is None else value if block(r, c) == 0 else mappings.get((block(r, c), value), 0))
        result.append(target)
    groups = Counter((i["block"], i["role"]) for i in indicators)
    return result, {"source_rectangle": [r1, c1, r2, c2], "source_shape": [ph, pw],
                    "pattern_counts": dict(colors), "indicators": indicators,
                    "duplicate_role_groups": [[key[0], key[1], count] for key, count in groups.items() if count > 1]}


def prepare():
    gen, source = load()
    canonical = root() / "shared/data/canonical/puzzles.jsonl"
    rows = []
    for line in canonical.open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rows.append(row)
    unique, occurrences = {}, []
    for row_number, row in enumerate(rows):
        for split in ("train", "test"):
            for index, pair in enumerate(row.get(split, [])):
                if not pair.get("input") or not pair.get("output"):
                    continue
                pair_key = key(pair)
                unique.setdefault(pair_key, pair)
                occurrences.append({"source": row.get("source"), "row": row_number, "split": split, "index": index,
                                    "pair_sha256": pair_key, "self_check": gen.self_check(pair["input"]),
                                    "last_indicator_rival_fits": solve(pair["input"], last_indicator=True)[0] == pair["output"]})
    cases = [{"name": f"canonical-{index}", "kind": "canonical", **pair} for index, pair in enumerate(unique.values())]
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(4):
            seed = 61200 + band_index
            cases.append({"name": f"generated-{band}-{index}", "kind": "generated", "seed": seed,
                          "sample_index": index, "difficulty": band, "overrides": {},
                          "input": gen.generate(seed, index, difficulty=band)})
    overrides = {"grid_h": 6, "grid_w": 6}
    cases.append({"name": "declared-six-by-six-override", "kind": "supported_override",
                  "seed": 77181, "sample_index": 0, "difficulty": "hard", "overrides": overrides,
                  "input": gen.generate(77181, 0, difficulty="hard", **overrides)})
    for case in cases:
        grid = case["input"]
        expected, facts = solve(grid)
        rival, _ = solve(grid, last_indicator=True)
        case.update(self_check=gen.self_check(grid), input_shape=[len(grid), len(grid[0])],
                    python_first_indicator=expected, last_indicator_rival=rival, facts=facts)
        if case["kind"] == "canonical":
            assert expected == case["output"]
        else:
            assert not case["self_check"]
    hashes = {"generator_sha256": sha(source), "version": gen.VERSION, "rule_hash_pin": gen.RULE_HASH,
              "canonical_jsonl_sha256": sha(canonical), "canonical_matching_rows_sha256": key(rows),
              "canonical_program_sha256": sorted({hashlib.sha256(row["program_solution"].encode()).hexdigest() for row in rows}),
              "notes_sha256": sha(source.parent / "notes.md"), "probe_sha256": sha(Path(__file__))}
    summary = {"task_id": TASK, "source_hashes": hashes, "canonical_rows": len(rows),
               "canonical_occurrences": len(occurrences), "canonical_unique_pairs": len(unique),
               "canonical_self_check_acceptance": [sum(not o["self_check"] for o in occurrences), len(occurrences)],
               "canonical_rival_fit": [sum(o["last_indicator_rival_fits"] for o in occurrences), len(occurrences)],
               "declared_grid_axes": {name: gen.AXES[name] for name in ("grid_h", "grid_w")},
               "override_requested_shape": [6, 6], "override_observed_shape": cases[-1]["input_shape"],
               "candidate_count": len(cases), "unique_input_count": len({key(c["input"]) for c in cases}),
               "occurrences": occurrences}
    dump("source-hashes.json", hashes)
    dump("diagnostic.json", summary)
    dump("cases.json", cases)
    dump("input.json", [case["input"] for case in cases])
    print(json.dumps({k: v for k, v in summary.items() if k != "occurrences"}, indent=2))


def verify():
    cases = json.loads((HERE / "cases.json").read_text())
    receipt = json.loads((HERE / "racket.json").read_text())
    assert len(cases) == len(receipt["results"])
    records = []
    for case, actual in zip(cases, receipt["results"]):
        output = actual["output"]
        assert actual["valid_output"] and actual["error"] is None
        assert output == case["python_first_indicator"] == solve(case["input"])[0], case["name"]
        if case["kind"] == "canonical":
            assert output == case["output"]
        records.append({"name": case["name"], "kind": case["kind"], "self_check": case["self_check"],
                        "rival_fits_actual_racket": output == case["last_indicator_rival"],
                        "rival_disagreement_cells": [[r, c] for r, row in enumerate(output) for c, v in enumerate(row) if v != case["last_indicator_rival"][r][c]],
                        "input_shape": case["input_shape"], "output_shape": [len(output), len(output[0])],
                        "source_rectangle": case["facts"]["source_rectangle"]})
    sample = [r for r in records if r["kind"] == "generated"]
    summary = {"task_id": TASK, "generator_sha256": receipt["generator_sha256"],
               "executed_rule_hash": receipt["executed_rule_hash"], "racket_receipt_sha256": sha(HERE / "racket.json"),
               "actual_racket_vs_independent_solver": [len(records), len(records)],
               "canonical_actual_label_agreement": [sum(r["kind"] == "canonical" for r in records)] * 2,
               "generated_sample_self_check_acceptance": [sum(not r["self_check"] for r in sample), len(sample)],
               "generated_sample_last_indicator_rival_agreement": [sum(r["rival_fits_actual_racket"] for r in sample), len(sample)],
               "declared_six_by_six_override_actual_shapes": records[-1], "records": records}
    dump("verification.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "records"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "verify"))
    args = parser.parse_args()
    if args.action == "prepare" and (HERE / "cases.json").exists():
        raise SystemExit("refusing to overwrite earlier evidence")
    globals()[args.action]()
