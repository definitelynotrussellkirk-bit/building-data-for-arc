#!/usr/bin/env python3
"""Audit a lesson-adaptive proxy: infer transform from distractor count."""
from __future__ import annotations
from copy import deepcopy
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
GEN = REPO / "generators/d62a0e470ae8/generator.py"

spec = importlib.util.spec_from_file_location("audit_d62", GEN)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def intended(grid):
    return module.rule_mirror(deepcopy(grid))


def proxy_output(grid, learned_offset):
    facts = module.observe_overrides(grid)
    proxy_key = 1 + ((facts["n_distractors"] + learned_offset) % 4)
    work = deepcopy(grid)
    work[0][0] = proxy_key
    return module.rule_mirror(work), proxy_key

bands = ("easy", "medium", "hard")
lesson_rows = []
rotation_total = rotation_matches = 0
for band in bands:
    for lesson_index in range(100):
        seed = 620000 + lesson_index
        start = lesson_index * 7
        grids = [module.generate(seed, start + offset, difficulty=band) for offset in range(5)]
        facts = [module.observe_overrides(grid) for grid in grids]
        offsets = [(row["key"] - 1 - row["n_distractors"]) % 4 for row in facts]
        for query_index in range(5):
            demo_offsets = {offset for i, offset in enumerate(offsets) if i != query_index}
            assert len(demo_offsets) == 1
            learned = next(iter(demo_offsets))
            proxy, proxy_key = proxy_output(grids[query_index], learned)
            rotation_total += 1
            if proxy == intended(grids[query_index]) and proxy_key == facts[query_index]["key"]:
                rotation_matches += 1
        lesson_rows.append({
            "band": band,
            "lesson_index": lesson_index,
            "seed": seed,
            "sample_indices": list(range(start, start + 5)),
            "key_distractor_pairs": [[row["key"], row["n_distractors"]] for row in facts],
            "offsets": offsets,
        })

# Retain one exact production-shaped lesson.
rep = lesson_rows[0]
rep_grids = [module.generate(rep["seed"], index, difficulty=rep["band"]) for index in rep["sample_indices"]]
rep_facts = [module.observe_overrides(grid) for grid in rep_grids]
learned_offset = rep["offsets"][0]
rep_outputs = [intended(grid) for grid in rep_grids]

# Break only the corner-key/count correlation while staying inside self_check.
base = deepcopy(rep_grids[-1])
proxy, proxy_key = proxy_output(base, learned_offset)
foreground = next(value for row in base for value in row if value not in (0, base[0][0]))
counterfactual = None
for key in (1, 2, 3, 4):
    if key in (proxy_key, foreground):
        continue
    candidate = deepcopy(base)
    candidate[0][0] = key
    if module.self_check(candidate):
        continue
    if intended(candidate) != proxy:
        counterfactual = candidate
        break
assert counterfactual is not None

report = {
    "schema": "arc-audit-lesson-adaptive-proxy-v1",
    "task_id": "d62a0e470ae8",
    "generator_sha256": hashlib.sha256(GEN.read_bytes()).hexdigest(),
    "rule_hash": module.RULE_HASH,
    "claim": (
        "For a fixed lesson seed, key and distractor count advance in lockstep modulo four. "
        "A solver can infer the offset from demos, ignore the corner key, and dispatch solely "
        "from distractor count on every production-shaped query rotation."
    ),
    "assembly_tested": "five consecutive sample indices with one fixed seed; four demos plus one query",
    "bands": list(bands),
    "lessons_per_band": 100,
    "lessons_total": len(lesson_rows),
    "query_rotations_total": rotation_total,
    "query_rotations_proxy_matches": rotation_matches,
    "all_lessons_constant_offset": all(len(set(row["offsets"])) == 1 for row in lesson_rows),
    "representative_lesson": {
        **rep,
        "facts": rep_facts,
        "inputs": rep_grids,
        "intended_outputs": rep_outputs,
        "learned_offset": learned_offset,
    },
    "counterfactual": {
        "input": counterfactual,
        "self_check_errors": module.self_check(counterfactual),
        "facts": module.observe_overrides(counterfactual),
        "learned_offset": learned_offset,
        "proxy_key": proxy_key,
        "actual_key": counterfactual[0][0],
        "proxy_output": proxy,
        "intended_python_mirror": intended(counterfactual),
    },
}
inputs = rep_grids + [counterfactual]
(ROOT / "checks/audit/d62a0e470ae8/inputs.json").write_text(json.dumps({"inputs": inputs}, indent=2) + "\n")
(ROOT / "checks/audit/d62a0e470ae8/probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "lessons": len(lesson_rows),
    "rotations": rotation_total,
    "proxy_matches": rotation_matches,
    "constant_offset": report["all_lessons_constant_offset"],
    "representative_pairs": rep["key_distractor_pairs"],
    "counterfactual_facts": report["counterfactual"]["facts"],
    "proxy_key": proxy_key,
    "actual_key": counterfactual[0][0],
    "counterfactual_differs": proxy != intended(counterfactual),
}, indent=2))
