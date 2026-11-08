"""Focused findings-only audit; public reviewer helpers and saved Racket labels."""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, load_selected_generator

TASK = "038f266f3acf"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit" / TASK


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def rectangles(grid):
    """Independent four-neighbor solid-rectangle reader, without generator internals."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    found = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        cells = {start}
        pending = deque([start])
        while pending:
            r, c = pending.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                cell = (r + dr, c + dc)
                if cell in unseen:
                    unseen.remove(cell)
                    cells.add(cell)
                    pending.append(cell)
        r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
        c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
        assert len(cells) == (r2 - r1 + 1) * (c2 - c1 + 1)
        reds = [(r, c) for r, c in cells if grid[r][c] == 2]
        assert len(reds) == 1
        r, c = reds[0]
        possibilities = []
        if r == r1:
            possibilities.append((-1, 0, r2-r))
        if r == r2:
            possibilities.append((1, 0, r-r1))
        if c == c1:
            possibilities.append((0, -1, c2-c))
        if c == c2:
            possibilities.append((0, 1, c-c1))
        assert len(possibilities) == 1
        dr, dc, depth = possibilities[0]
        found.append({"bbox": [r1, c1, r2, c2], "marker": [r, c],
                      "direction": [dr, dc], "depth": depth})
    return sorted(found, key=lambda rect: rect["marker"])


def capped_width_rival(grid):
    """Otherwise normal beams, but cap the green wing half-width at four."""
    result = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for rect in rectangles(grid):
        r, c = rect["marker"]
        dr, dc = rect["direction"]
        half = min(rect["depth"], 4)
        r, c = r + dr, c + dc
        while 0 <= r < h and 0 <= c < w:
            result[r][c] = 2
            for k in range(1, half + 1):
                for sign in (-1, 1):
                    rr = r + sign*k if dc else r
                    cc = c if dc else c + sign*k
                    if 0 <= rr < h and 0 <= cc < w:
                        result[rr][cc] = 3
            r, c = r + dr, c + dc
    return result


def small_witness():
    grid = [[0] * 10 for _ in range(7)]
    for r in range(4, 7):
        for c in range(2, 8):
            grid[r][c] = 3
    grid[5][2] = 2
    for r in range(0, 3):
        for c in range(7, 9):
            grid[r][c] = 3
    grid[1][8] = 2
    return grid


def build():
    gen, source_path, digest = load_selected_generator(TASK, root=ROOT)
    pairs = canonical_pairs(TASK, root=ROOT)
    records = []
    for index in range(5):
        grid = gen.generate(20261012, index, difficulty="easy")
        records.append({"label": f"generated_{index}", "seed": 20261012,
                        "sample_index": index, "difficulty": "easy", "overrides": {},
                        "input": grid})
    canonical = next(pair for pair in pairs if any(rect["depth"] > 4 for rect in rectangles(pair["input"])))
    records.append({"label": "canonical_depth_five", "seed": None,
                    "sample_index": None, "overrides": None,
                    "canonical_identity": {k: canonical[k] for k in ("variant", "split", "pair_index")},
                    "input": canonical["input"], "recorded_canonical_output": canonical["output"]})
    records.append({"label": "small_depth_five", "seed": None,
                    "sample_index": None, "overrides": None,
                    "construction": "7x10 grid, right-firing 3x2 rectangle at (0,7); left-firing 3x6 at (4,2)",
                    "input": small_witness()})
    for record in records:
        grid = record["input"]
        record.update(self_check=gen.self_check(grid), strict_canonical_like=gen.strict_canonical_like(grid),
                      observed_overrides=gen.observe_overrides(grid), rectangles=rectangles(grid),
                      domain_legal=all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
                      and 1 <= len(grid) <= 30 and 1 <= len(grid[0]) <= 30,
                      rival_output=capped_width_rival(grid), mirror_output=gen.rule_mirror(grid))
    # This census is cheap Python evidence, not additional authoritative labels.
    census = []
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 17, 20261012):
            for index in range(8):
                grid = gen.generate(seed, index, difficulty=band)
                census.append({"seed": seed, "sample_index": index, "difficulty": band, "overrides": {},
                               "depths": [x["depth"] for x in rectangles(grid)],
                               "self_check": gen.self_check(grid),
                               "rival_equals_mirror": capped_width_rival(grid) == gen.rule_mirror(grid)})
    canonical_census = []
    for pair in pairs:
        canonical_census.append({**{k: pair[k] for k in ("variant", "split", "pair_index")},
                                 "depths": [x["depth"] for x in rectangles(pair["input"])],
                                 "self_check": gen.self_check(pair["input"]),
                                 "rival_equals_recorded_output": capped_width_rival(pair["input"]) == pair["output"]})
    authority_path = ROOT / "shared/data/base/solutions/training/b527c5c6__038f266f3acf.json"
    authority = json.loads(authority_path.read_text())["racket_target"]["target_code"]
    identity = {"task_id": TASK, "generator_path": str(source_path.relative_to(ROOT.parent)),
                "generator_sha256": digest, "declared_rule_hash": gen.RULE_HASH,
                "authority_file": str(authority_path.relative_to(ROOT.parent)),
                "authority_file_sha256": hashlib.sha256(authority_path.read_bytes()).hexdigest(),
                "authority_source_sha256": hashlib.sha256(authority.encode()).hexdigest(),
                "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    dump("source_identity.json", identity)
    dump("cases.json", records)
    dump("input.json", [record["input"] for record in records])
    dump("canonical_input.json", canonical["input"])
    dump("small_input.json", records[-1]["input"])
    dump("python_census.json", {"population": census, "canonical": canonical_census})
    print(json.dumps({"identity": identity, "cases": [{k: rec[k] for k in ("label", "self_check", "rectangles")} for rec in records],
                      "python_census_count": len(census), "canonical_count": len(canonical_census)}, indent=2))


def analyze():
    gen, _, digest = load_selected_generator(TASK, root=ROOT)
    identity = json.loads((OUT / "source_identity.json").read_text())
    assert digest == identity["generator_sha256"]
    cases = json.loads((OUT / "cases.json").read_text())
    result = json.loads((OUT / "racket.json").read_text())
    outputs = [row["output"] for row in result["results"]]
    assert len(outputs) == len(cases)
    comparisons = []
    for case, output in zip(cases, outputs):
        diffs = [[r,c,output[r][c],case["rival_output"][r][c]]
                 for r, row in enumerate(output) for c, _ in enumerate(row)
                 if output[r][c] != case["rival_output"][r][c]]
        comparisons.append({"label": case["label"], "self_check": case["self_check"],
                            "domain_legal": case["domain_legal"], "rival_equals_racket": not diffs,
                            "rival_differing_cells": diffs, "mirror_equals_racket": output == case["mirror_output"],
                            "matches_recorded_canonical": (output == case["recorded_canonical_output"])
                            if "recorded_canonical_output" in case else None})
    demos = [{"input": cases[i]["input"], "output": outputs[i]} for i in range(4)]
    lessons = []
    for i in (4, 5, 6):
        query = {"input": cases[i]["input"], "output": outputs[i]}
        lessons.append({"query_case": cases[i]["label"], "demonstration_cases": [x["label"] for x in cases[:4]],
                        "lesson_identifiable": gen.lesson_identifiable(demos, query),
                        "rival_fits_all_demos": all(capped_width_rival(d["input"]) == d["output"] for d in demos),
                        "rival_changes_query": capped_width_rival(query["input"]) != query["output"]})
    dump("comparison.json", {"identity": identity, "comparisons": comparisons, "lessons": lessons,
                             "racket_metadata": {k: v for k, v in result.items() if k != "results"},
                             "racket_domain_results": [{k:v for k,v in row.items() if k not in ("input", "output")}
                                                       for row in result["results"]]})
    dump("lesson.json", {"demos": demos, "queries": [{"case": cases[i]["label"], "input": cases[i]["input"],
                         "racket_output": outputs[i], "rival_output": cases[i]["rival_output"]} for i in (4,5,6)]})
    dump("small_racket_output.json", outputs[6])
    dump("small_rival_output.json", cases[6]["rival_output"])
    print(json.dumps({"comparisons": comparisons, "lessons": lessons}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("build", "analyze"))
    mode = parser.parse_args().mode
    OUT.mkdir(parents=True, exist_ok=True)
    (build if mode == "build" else analyze)()
