"""Bounded palette-rank teaching audit; run through review.py run."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from arcpuzzles import Catalog

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
TASK = "677dcb71e2be"
SOURCE = REPO / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audited_generator", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def rival(grid):
    """Count each color but order by fixed palette ranks, never component size."""
    values, errors = gen._coerce_grid(grid)
    assert not errors
    comps = gen._components(values)
    colors = sorted(comp["color"] for comp in comps)
    ranks = (1, 2, 0) if len(colors) == 3 else (1, 3, 0, 2)
    by_color = {comp["color"]: comp for comp in comps}
    return gen._bars_from_components([by_color[colors[i]] for i in ranks])

catalog = Catalog(REPO)
row = catalog.get(TASK)
rule = row["variants"][0]["program_solution"]
identity = {"generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "rule_hash": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12],
            "rule_text_sha256": hashlib.sha256(rule.encode()).hexdigest()}
assert identity["generator_sha256"] == "859002c6301cbe944a18a9405eb86c96c42480110b16cbaf88242456f78ecb8c"
sample_cases = []
for band in ("easy", "medium", "hard"):
    for seed in range(8):
        for index in range(4):
            grid = gen.generate(seed, index, difficulty=band)
            sample_cases.append({"seed": seed, "sample_index": index, "difficulty": band,
                                 "self_check": gen.self_check(grid),
                                 "rival_matches_python_mirror": rival(grid) == gen._official_output(grid)})

# Four consecutive default scenes kill every named competitor. Swapping two
# colors changes no component geometry or occupied-cell counts.
demos_inputs = [gen.generate(42, i, difficulty="medium") for i in range(4)]
original = demos_inputs[0]
comps = sorted(gen._components(original), key=lambda c: -c["size"])
a, b = comps[0]["color"], comps[1]["color"]
query = [[b if value == a else a if value == b else value for value in line] for line in original]
inputs = [*demos_inputs, query]
applied = catalog.apply(TASK, inputs, allow_unapproved=True, timeout=45)
identity["executed_rule_text_sha256"] = applied["rule_text_sha256"]
identity["executed_rule_hash"] = applied["executed_rule_hash"]
(HERE / "reference.json").write_text(json.dumps(applied, indent=2) + "\n")
results = applied["results"]
assert all(result["output"] is not None for result in results)
assert all(rival(grid) == result["output"] for grid, result in zip(demos_inputs, results[:4]))
assert rival(query) != results[4]["output"]
assert gen.self_check(query) == []
demos = [{"input": grid, "output": result["output"]} for grid, result in zip(demos_inputs, results[:4])]
query_pair = {"input": query, "output": results[4]["output"]}
reported = gen.lesson_identifiable(demos, query_pair)
assert reported == []
(HERE / "input.json").write_text(json.dumps(query) + "\n")
(HERE / "rival.json").write_text(json.dumps(rival(query)) + "\n")
(HERE / "expected.json").write_text(json.dumps(results[4]["output"]) + "\n")
report = {"task_id": TASK, "classification": "measured curriculum color-rank shortcut",
          "identity": identity, "probe_scope": sample_cases,
          "sample_count": len(sample_cases),
          "mirror_matches": sum(case["rival_matches_python_mirror"] for case in sample_cases),
          "reference_checks": 5,
          "reference_demo_matches": 4,
          "query_origin": {"seed": 42, "sample_index": 0, "difficulty": "medium",
                           "mutation": {"swap_colors": [a, b]}},
          "query_self_check": gen.self_check(query),
          "query_rival_matches_reference": False,
          "lesson_identifiable_reasons": reported,
          "canonical_rival_matches": [rival(p["input"]) == [[int(c) for c in line] if isinstance(line,str) else line for line in p["output"]] for p in row["variants"][0]["train"]],
          "scope_limit": "No battery or universal empirical claim; canonical outputs compared as stored, not independently re-executed. Fixed rank mapping follows directly from _assign_colors for all generated palettes."}
(HERE / "finding.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: report[k] for k in ("identity", "sample_count", "mirror_matches", "reference_checks", "reference_demo_matches", "query_origin", "query_self_check", "lesson_identifiable_reasons", "canonical_rival_matches")}, indent=2))
