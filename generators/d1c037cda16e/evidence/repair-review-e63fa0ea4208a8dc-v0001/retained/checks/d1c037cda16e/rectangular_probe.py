"""Bounded in-domain square-block rival; run from packet via review.py run."""
from pathlib import Path
import hashlib
import json

from reviewer_support import canonical_pairs, load_selected_generator
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

TASK = "d1c037cda16e"
root = Path.cwd().resolve()
out = Path(__file__).resolve().parent / "rectangular_probe.json"
generator, source, source_sha = load_selected_generator(TASK, root=root)
with (root / "shared/data/canonical/puzzles.jsonl").open() as handle:
    records = [json.loads(line) for line in handle
               if line.strip() and json.loads(line).get("task_id") == TASK]
programs = {record["program_solution"] for record in records}
assert len(programs) == 1
canonical = programs.pop()
# The rival assumes square tiles with side height/3 and preserves the number
# of resulting horizontal tiles. This is a hypothesis, not selected code.
assert canonical.count("(bw (quotient w 3))") == 1
assert canonical.count("(build-grid 3\n                         3") == 1
rival = canonical.replace("(bw (quotient w 3))", "(bw (quotient h 3))")
rival = rival.replace("(build-grid 3\n                         3",
                      "(build-grid 3\n                         (quotient w bw)")
pairs = [pair for pair in canonical_pairs(TASK, root=root)
         if pair["split"] == "train"]
args = {"seed": 731, "sample_index": 0, "difficulty": "medium",
        "block_h": 2, "block_w": 4}
query = generator.generate(**args)
errors = generator.self_check(query, difficulty="medium", meta={})
assert errors == []
assert len(query) == 6 and len(query[0]) == 12
bh, bw = 2, 4
revealed = []
for bi in range(3):
    for bj in range(3):
        values = [query[bi * bh + dr][bj * bw + dc]
                  for dr in range(bh) for dc in range(bw)
                  if query[bi * bh + dr][bj * bw + dc] != 0]
        assert len(values) == 1
        revealed.extend(values)
assert sorted(revealed) == list(range(1, 10))
runtime = root / "shared/runtime"
with _local_imports(runtime, root):
    apply, identity, bridge = _real_evaluator(runtime)
    try:
        demos = []
        for pair in pairs:
            reference = apply(canonical, pair["input"])
            alternative = apply(rival, pair["input"])
            assert reference == pair["output"] == alternative
            demos.append({**pair, "racket_reference": reference,
                          "racket_rival": alternative})
        reference = apply(canonical, query)
        alternative = apply(rival, query)
        assert reference != alternative
    finally:
        bridge.close()
report = {
    "schema": "arcpuzzles-focused-learnability-probe-v1",
    "task_id": TASK, "generator_sha256": source_sha,
    "canonical_program_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
    "rival_program_sha256": hashlib.sha256(rival.encode()).hexdigest(),
    "canonical_program": canonical, "rival_program": rival,
    "runtime_identity": identity, "racket_evaluations": 2 * (len(demos) + 1),
    "finding": "All three square canonical demonstrations admit an aspect-preserving square-tile rival; a lawful generated rectangle distinguishes it.",
    "demonstrations": demos,
    "query": {"generator_arguments": args, "input": query,
              "self_check_errors": errors, "nonzero_per_block": 1,
              "foreground_colors": sorted(revealed),
              "racket_reference": reference, "racket_rival": alternative},
    "limits": ["One generated rectangle only; no random seed sweep or full battery.",
               "No rule defect or canonical-label error claimed.",
               "No generator/rule edits, parametric qualification or training admission.",
               "Existing multi-cell and validator audits were not replayed.",
               "Rival ambiguity is relative to the three visible canonical demonstrations, not every possible generated episode."]}
out.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"evidence": str(out), "racket_evaluations": report["racket_evaluations"],
                  "demo_agreements": len(demos), "query_reference": reference,
                  "query_rival": alternative, "source_sha256": source_sha}))
