"""Findings-only authoring probe. Replay through the packet's public wrapper.

prepare: select source via public reviewer_support; emit at most 64 inputs.
analyze: compare retained actual Racket labels against independent area rival.
No reference execution or private runner imports occur in this script.
"""
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs, load_selected_generator

TASK = "d5440a0106ef"
EXPECTED_SHA = "4c1ae153297c2ba94904bb1e09dc357326e31889226158fc86af87e39dbe882c"

def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")

def panels(grid):
    separators = [c for c in range(len(grid[0])) if all(row[c] == 9 for row in grid)]
    bounds = [-1] + separators + [len(grid[0])]
    return [[row[a+1:b] for row in grid] for a, b in zip(bounds, bounds[1:]) if b > a+1]

def area_rival(grid):
    sizes = [sum(v not in (0, 9) for row in panel for v in row) for panel in panels(grid)]
    return [[8 if size == sizes[0] else 0 for size in sizes[1:]]]

def depth_hist(panel):
    cur = {(r, c) for r, row in enumerate(panel) for c, v in enumerate(row) if v not in (0, 9)}
    hist = []
    while cur:
        edge = {p for p in cur if any((p[0]+dr, p[1]+dc) not in cur for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)))}
        hist.append(len(edge))
        cur -= edge
    return hist

def combine(motifs):
    out = [[] for _ in range(5)]
    for k, cells in enumerate(motifs):
        if k:
            for row in out:
                row.append(9)
        for r, row in enumerate(out):
            row.extend(1 if (r, c) in cells else 0 for c in range(4))
    return out

def prepare():
    module, source, digest = load_selected_generator(TASK, root=REPO)
    assert digest == EXPECTED_SHA, digest
    canon = canonical_pairs(TASK, root=REPO, labeled_only=True)
    records = [{"kind": "canonical", "variant": p["variant"], "split": p["split"], "pair_index": p["pair_index"], "input": p["input"], "expected_output": p["output"]} for p in canon]
    for seed in range(32):
        records.append({"kind": "generated", "seed": seed, "sample_index": 0, "difficulty": "medium", "overrides": {}, "input": module.generate(seed=seed, sample_index=0, difficulty="medium")})
    square = {(r, c) for r in range(1, 4) for c in range(3)}
    snake = {(0,0), (0,1), (0,2), (0,3), (1,3), (2,3), (2,2), (2,1), (2,0)}
    translated = {(r, c+1) for r, c in square}
    small = square - {(1, 0)}
    records.append({"kind": "outside_emitted_support", "construction": "four 5x4 panels; first and third 3x3 blocks; second connected nine-cell path; fourth eight-cell block", "seed": None, "sample_index": None, "overrides": None, "input": combine([square, snake, translated, small])})
    for record in records:
        record["panel_areas"] = [sum(hist) for hist in map(depth_hist, panels(record["input"]))]
        record["panel_histograms"] = [depth_hist(p) for p in panels(record["input"])]
        record["rival_output"] = area_rival(record["input"])
        record["input_sha256"] = hashlib.sha256(json.dumps(record["input"], separators=(",", ":")).encode()).hexdigest()
    # Canonical widths 31/39 exceed public apply's 30-column limit. Keep their
    # authored labels for rival fitting, but submit only supported sizes.
    dump("input.json", [p["input"] for p in records if p["kind"] != "canonical"])
    dump("cases.json", {"task_id": TASK, "generator_sha256": digest, "source": source.relative_to(REPO).as_posix(), "declared_canonical_shortcuts": getattr(module, "CANONICAL_SHORTCUTS", None), "declared_lesson_competitors": getattr(module, "LESSON_COMPETITORS", None), "validator_declared": callable(getattr(module, "self_check", None)), "records": records})
    print(json.dumps({"prepared": len(records), "canonical": len(canon), "generated": 32, "outside_emitted_support": 1, "generator_sha256": digest}))

def analyze():
    cases = json.loads((HERE / "cases.json").read_text())
    actual = json.loads((HERE / "racket.json").read_text())
    print(json.dumps({"racket_report_keys": list(actual)}))
    assert all(p["valid_output"] and p["error"] is None for p in actual["results"])
    outputs = [p["output"] for p in actual["results"]]
    submitted = [p for p in cases["records"] if p["kind"] != "canonical"]
    assert len(outputs) == len(submitted)
    for record, output in zip(submitted, outputs):
        record["racket_output"] = output
        record["rival_matches_racket"] = record["rival_output"] == output
    canon = [p for p in cases["records"] if p["kind"] == "canonical"]
    for record in canon:
        record["rival_fits_canonical"] = record["rival_output"] == record["expected_output"]
        record["racket_status"] = "not executed: canonical width exceeds public apply 30-column limit"
    gen = [p for p in cases["records"] if p["kind"] == "generated"]
    from collections import Counter
    summary = {"task_id": TASK, "generator_sha256": cases["generator_sha256"], "canonical_pairs": len(canon), "canonical_rival_matches": sum(p["rival_fits_canonical"] for p in canon), "canonical_racket_execution": "not run; public apply rejects widths 31 and 39", "generated_samples": len(gen), "unique_generated_inputs": len({p["input_sha256"] for p in gen}), "seed_range_inclusive": [0,31], "sample_index": 0, "difficulty": "medium", "generated_rival_matches": sum(p["rival_matches_racket"] for p in gen), "generated_match_count_histogram": dict(sorted(Counter(sum(v==8 for v in p["racket_output"][0]) for p in gen).items())), "outside_emitted_support_rival_mismatches": sum(not p["rival_matches_racket"] for p in cases["records"] if p["kind"] == "outside_emitted_support"), "generator_domain_status_counts": dict(Counter(p["generator_domain"]["status"] for p in actual["results"])), "rule_text_sha256": actual["rule_text_sha256"], "executed_rule_hash": actual["executed_rule_hash"], "racket_provenance": {k:v for k,v in actual.items() if k != "results"}}
    dump("rival.json", cases)
    dump("summary.json", summary)
    print(json.dumps(summary))

if __name__ == "__main__":
    {"prepare": prepare, "analyze": analyze}[sys.argv[1]]()
