"""Bounded findings-only probe; rivals are review predictions, not labels."""
import json
from pathlib import Path
import sys

for ancestor in Path(__file__).resolve().parents:
    support = ancestor / "repo" / "shared" / "runtime"
    if (support / "reviewer_support.py").is_file():
        sys.path.insert(0, str(support))
        break
else:
    raise RuntimeError("No packet-local support")

from reviewer_support import canonical_pairs, find_root, load_selected_generator

OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)
m, source, digest = load_selected_generator("341758fa9de1", root=ROOT)


def rival(grid):
    key = grid[-1][-2]
    return [[v if v == key else 0 for v in row] for row in grid]


def mirror(grid):
    key = next(v for row in grid for v in row if v)
    return [[v if v == key else 0 for v in row] for row in grid]


if "--verify" in sys.argv:
    report = json.loads((OUT / "probe.json").read_text())
    official = json.loads((OUT / "racket.json").read_text())
    results = official["results"]
    assert report["source_sha256"] == official["generator_sha256"] == digest
    assert official["executed_rule_hash"] == official["catalog_rule_hash"] == m.RULE_HASH
    assert len(results) == 5 and all(r["error"] is None and r["valid_output"] for r in results)
    assert all(r["generator_domain"]["status"] == "valid" for r in results)
    assert results[0]["output"] == report["control_mirror"] == report["control_rival"]
    assert results[1]["output"] == report["counterexample_mirror"]
    assert results[1]["output"] != report["counterexample_rival"]
    pairs = canonical_pairs("341758fa9de1", root=ROOT, labeled_only=True)
    assert all(r["output"] == p["output"] for r, p in zip(results[2:], pairs))
    verified = {"task_id": "341758fa9de1", "source_sha256": digest,
                "executed_rule_hash": official["executed_rule_hash"],
                "rule_text_sha256": official["rule_text_sha256"],
                "official_inputs": len(results), "valid_generator_domain_inputs": len(results),
                "generated_control_shortcut_matches_official": True,
                "manifold_counterexample_refutes_shortcut_officially": True,
                "canonical_outputs_match_public_labels": len(pairs),
                "counterexample_input_sha256": results[1]["input_sha256"],
                "counterexample_output_sha256": results[1]["output_sha256"]}
    (OUT / "verification.json").write_text(json.dumps(verified, indent=2) + "\n")
    print(json.dumps(verified))
    raise SystemExit(0)


draws = []
for seed in (0, 17, 301):
    for band in ("easy", "medium", "hard"):
        for index in range(12):
            grid = m.generate(seed, index, difficulty=band)
            draws.append({"seed": seed, "index": index, "difficulty": band,
                          "shortcut_matches_mirror": rival(grid) == mirror(grid),
                          "domain_errors": m.self_check(grid)})
assert len(draws) == 108 and all(d["shortcut_matches_mirror"] for d in draws)
assert all(not d["domain_errors"] for d in draws)

control = m.generate(17, 0, difficulty="medium")
changed = [row[:] for row in control]
key = next(v for row in changed for v in row if v)
assert changed[-1][-2] == key
changed[-1][-2] = 0
destination = next((r, c) for r, row in enumerate(changed) for c, v in enumerate(row)
                   if v == 0 and (r, c) != (len(changed)-1, len(row)-2)
                   and r * len(row) + c > 1)
changed[destination[0]][destination[1]] = key
assert not m.self_check(changed)
assert rival(changed) != mirror(changed)
pairs = canonical_pairs("341758fa9de1", root=ROOT, labeled_only=True)
canonical = [{"variant": p["variant"], "split": p["split"], "index": p["pair_index"],
              "shortcut_matches_public_label": rival(p["input"]) == p["output"],
              "mirror_matches_public_label": mirror(p["input"]) == p["output"]} for p in pairs]
inputs = [control, changed] + [p["input"] for p in pairs]
(OUT / "input.json").write_text(json.dumps({"inputs": inputs}, indent=2) + "\n")
report = {"task_id": "341758fa9de1", "source_sha256": digest,
          "declared_rule_hash": m.RULE_HASH, "generated_draws": len(draws),
          "generated_results": draws, "canonical_results": canonical,
          "control_parameters": {"seed": 17, "sample_index": 0, "difficulty": "medium"},
          "counterexample_domain_errors": m.self_check(changed),
          "control_rival": rival(control), "control_mirror": mirror(control),
          "counterexample_rival": rival(changed), "counterexample_mirror": mirror(changed),
          "relocated_key_destination": list(destination),
          "official_input_order": ["generated_control", "manifold_counterexample"] +
                                  [f"canonical-{i}" for i in range(len(pairs))]}
(OUT / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"source_sha256": digest, "generated_draws": len(draws),
                  "generated_shortcut_matches": sum(d["shortcut_matches_mirror"] for d in draws),
                  "canonical_pairs": len(pairs),
                  "canonical_shortcut_matches": sum(d["shortcut_matches_public_label"] for d in canonical),
                  "counterexample_domain_errors": m.self_check(changed)}))
