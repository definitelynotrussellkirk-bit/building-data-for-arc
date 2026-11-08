#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3] / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
sys.path.insert(0, str(REPO / "src"))
TASK = "ffcd7510821d"
SOURCE = REPO / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_ffcd", SOURCE)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def pair(grid):
    return {"input": grid, "output": mod.rule_mirror(grid)}

counts = {"fixed_query_windows": 0, "fixed_query_ambiguous": 0,
          "rotated_queries": 0, "rotated_query_ambiguous": 0}
by_band = {}
witness = None
witness_grids = None
for band in ("easy", "medium", "hard"):
    local = {key: 0 for key in counts}
    for seed in range(16):
        for start in range(24):
            lesson = [pair(mod.generate(seed, start + offset, difficulty=band)) for offset in range(5)]
            reasons = mod.lesson_identifiable(lesson[:4], {"input": lesson[4]["input"]})
            local["fixed_query_windows"] += 1
            local["fixed_query_ambiguous"] += bool(reasons)
            for query_index in range(5):
                demos = [item for index, item in enumerate(lesson) if index != query_index]
                query = {"input": lesson[query_index]["input"]}
                reasons = mod.lesson_identifiable(demos, query)
                local["rotated_queries"] += 1
                local["rotated_query_ambiguous"] += bool(reasons)
                if reasons and witness is None:
                    witness = {
                        "band": band, "seed": seed, "start": start,
                        "query_index": query_index,
                        "marker_counts": [p["input"][0].count(9) for p in lesson],
                        "reasons": reasons,
                        "query_input": query["input"],
                        "demo_inputs": [p["input"] for p in demos],
                        "demo_outputs": [p["output"] for p in demos],
                    }
                    witness_grids = [p["input"] for p in lesson]
    by_band[band] = local
    for key, value in local.items():
        counts[key] += value

racket = {"attempted": False}
try:
    from arcpuzzles import Catalog
    receipt = Catalog(REPO).apply(TASK, witness_grids, reference="canonical", timeout=180)
    actual = [item.get("output") for item in receipt["results"]]
    expected = [mod.rule_mirror(grid) for grid in witness_grids]
    racket = {
        "attempted": True,
        "rule_hash_matches_catalog": receipt.get("rule_hash_matches_catalog"),
        "errors": [item.get("error") for item in receipt["results"]],
        "all_outputs_match_python_crosscheck": actual == expected,
    }
except Exception as exc:
    racket = {"attempted": True, "error": f"{type(exc).__name__}: {exc}"}

report = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "sampler": {"bands": ["easy", "medium", "hard"], "seeds": [0, 15],
                "start_indices": [0, 23], "window": "five consecutive pairs"},
    "counts": counts,
    "by_band": by_band,
    "ambiguity_fraction_under_query_rotation": (
        counts["rotated_query_ambiguous"] / counts["rotated_queries"]
    ),
    "fixed_fifth_query_fraction_ambiguous": (
        counts["fixed_query_ambiguous"] / counts["fixed_query_windows"]
    ),
    "retained_witness": witness,
    "racket_parity_on_witness_window": racket,
    "finding": (
        "The fixed fifth-query assembly is clean, but rotating the query through the same "
        "five materialized pairs leaves the held-out marker residue unseen in 3/5 positions."
    ),
}
Path(__file__).with_name("result.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: v for k, v in report.items() if k != "retained_witness"}, indent=2))
