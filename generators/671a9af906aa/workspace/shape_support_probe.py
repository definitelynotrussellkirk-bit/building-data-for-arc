"""Focused size/profile crossing evidence, with executed canonical Racket labels.

Run via review.py run so this checkout's Racket and Python dependencies are used.
The dimension-gated rival matches the rule at height 7 and returns identity at
larger heights. It fit every default v2.0.0 scene; the repaired default schedule
must expose its error on enlarged reachable examples.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from maze_probe import canonical_record, classify, rule_output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    gen, _, source_sha = load_selected_generator("671a9af906aa", root=repo)
    canonical = canonical_record(repo)
    rule = canonical["program_solution"]
    report = {"generator_sha256": source_sha, "rule_hash": gen.RULE_HASH,
              "rule_sha256": hashlib.sha256(rule.encode()).hexdigest(),
              "seed": 671900, "bands": {}, "racket_cases": [],
              "limits": "One complete 25-scene support cycle per difficulty; finite rival only."}
    with RacketBridge() as bridge:
        for band in ("easy", "medium", "hard"):
            counts, first, strict, shortcut_disagreements = Counter(), {}, [], 0
            for index in range(25):
                grid = gen.generate(671900, index, difficulty=band)
                assert gen.self_check(grid) == []
                mode = classify(grid)
                size = "canonical" if len(grid) == 7 else "enlarged"
                assert (size == "canonical") == (not gen.strict_canonical_like(grid))
                counts[f"{mode}:{size}"] += 1
                strict.append(size == "canonical")
                truth = rule_output(grid)
                rival = truth if len(grid) == 7 else grid
                shortcut_disagreements += rival != truth
                first.setdefault((mode, size), (index, grid))
            assert len(first) == 6
            assert shortcut_disagreements == 4
            for mode in gen.SCHEDULE_PROFILES:
                assert counts[f"{mode}:canonical"] == 4 * counts[f"{mode}:enlarged"]
            floor = min(sum((strict + strict)[i:i + 6]) / 6 for i in range(25))
            assert floor >= gen.MIN_STRICT_FRAC
            report["bands"][band] = {"counts": dict(counts),
                "dimension_gated_rival_disagreements": shortcut_disagreements,
                "minimum_six_pair_strict_fraction": floor}
            for (mode, size), (index, grid) in first.items():
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")"
                                           for row in grid) + ")"
                output = bridge.eval_text(f"({wrap_rule(rule)} {literal})")
                assert output == rule_output(grid) == gen.rule_mirror(grid)
                assert (output == grid) == (mode == "unreachable")
                report["racket_cases"].append({"difficulty": band, "sample_index": index,
                    "route_mode": mode, "size": size, "input": grid, "output": output,
                    "dimension_gated_rival_disagrees": len(grid) != 7 and output != grid})
        canonical_pairs = canonical["train"] + canonical["test"]
        for pair in canonical_pairs:
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")"
                                       for row in pair["input"]) + ")"
            assert bridge.eval_text(f"({wrap_rule(rule)} {literal})") == pair["output"]
        report["canonical_pairs_racket_checked"] = len(canonical_pairs)
    report["passed"] = True
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "racket_generated_cases": len(report["racket_cases"]),
                      "canonical_pairs": len(canonical_pairs), "generator_sha256": source_sha}))


if __name__ == "__main__":
    main()
