"""Finite, findings-only audit of the unchanged 48a4d72eb621 generator."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

TASK = "48a4d72eb621"
HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
SOURCE = REPO / "generators" / TASK / "generator.py"
CANONICAL = REPO / "shared/data/canonical/puzzles.jsonl"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def grid(value):
    return [[int(cell) for cell in row] for row in value]


def counts(value):
    return Counter(c for row in value for c in row if c != 0)


def capped(value):
    hist = counts(value)
    out = [c for c in sorted(hist) for _ in range(min(2, hist[c]))]
    return [out or [0]]


def omit_five(value):
    return [sorted(c for row in value for c in row if c not in (0, 5)) or [0]]


def main():
    spec = importlib.util.spec_from_file_location("audited_generator", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    canonical = next(json.loads(line) for line in CANONICAL.read_text().splitlines()
                     if json.loads(line).get("task_id") == TASK)
    cases = []
    for split in ("train", "test"):
        pairs = canonical[split]
        if isinstance(pairs, dict):
            pairs = [pairs]
        for index, pair in enumerate(pairs):
            inp = grid(pair["input"])
            histogram = counts(inp)
            errors = module.self_check(inp)
            cases.append({
                "name": f"canonical_{split}_{index}",
                "canonical_split": split, "canonical_pair_index": index,
                "input": inp, "canonical_output": grid(pair["output"]),
                "self_check_errors": errors,
                "passes_self_check": not errors,
                "declared_invariants_hold": len(histogram) >= 3 and all(1 <= n <= 2 for n in histogram.values()),
                "reachable_by_normal_generator": 3 <= len(histogram) <= 4 and all(n <= 2 for n in histogram.values()) and 5 not in histogram and 6 <= len(inp) <= 8 and 7 <= len(inp[0]) <= 9,
                "counts": dict(sorted(histogram.items())),
                "rival_cap_each_color_at_two": capped(inp),
                "rival_discard_color_five": omit_five(inp),
            })
    seed, sample_index, difficulty = 0, 0, "medium"
    base = module.generate(seed, sample_index, difficulty=difficulty)
    generated_index = len(cases)
    cases.append({
        "name": "generated_baseline", "input": base,
        "seed": seed, "sample_index": sample_index,
        "difficulty": difficulty, "overrides": {},
        "self_check_errors": module.self_check(base),
        "passes_self_check": not module.self_check(base),
        "declared_invariants_hold": True,
        "reachable_by_normal_generator": True,
        "counts": dict(sorted(counts(base).items())),
        "rival_cap_each_color_at_two": capped(base),
        "rival_discard_color_five": omit_five(base),
    })
    controls = []
    overrides_list = [
        {"n_colors": 5}, {"palette_size": 5}, {"n_distinct_colors": 5},
        {"grid_h": 5}, {"grid_h": 12}, {"grid_w": 6}, {"grid_w": 12},
    ]
    for overrides in overrides_list:
        record = {"seed": seed, "sample_index": sample_index,
                  "difficulty": difficulty, "overrides": overrides}
        try:
            result = module.generate(seed, sample_index, difficulty=difficulty, **overrides)
            record.update({"input": result, "distinct_nonbackground_colors": len(counts(result)),
                           "same_input_as_baseline": result == base,
                           "self_check_errors": module.self_check(result),
                           "passes_self_check": not module.self_check(result),
                           "racket_input_index": generated_index if result == base else None})
        except Exception as exc:
            record.update({"exception_type": type(exc).__name__, "exception_message": str(exc)})
        controls.append(record)
    data = {
        "task_id": TASK, "audit_only": True, "source_modified": False,
        "generator_version": module.VERSION,
        "generator_path": str(SOURCE.relative_to(PACKET)),
        "generator_sha256": sha(SOURCE.read_bytes()),
        "canonical_path": str(CANONICAL.relative_to(PACKET)),
        "canonical_file_sha256": sha(CANONICAL.read_bytes()),
        "canonical_rule_sha256": sha(canonical["program_solution"].encode()),
        "canonical_rule_hash_definition": "SHA-256 of exact UTF-8 program_solution string",
        "declared_axes": module.AXES,
        "canonical_shortcuts_declared": getattr(module, "CANONICAL_SHORTCUTS", None),
        "lesson_competitors_declared": getattr(module, "LESSON_COMPETITORS", None),
        "cases": cases, "controls": controls,
        "scope": "Five canonical pairs, one generated baseline at seed 0/index 0/medium, and seven exact-control probes; no battery or solve data.",
        "membership_interpretation": "Normal generator excludes all degenerate textures. Reachability field is a necessary-support check from source, not a proof that a particular RNG seed produces canonical placements. Canonical data is an explicitly documented task domain; declared invariants and actual generation support are reported separately.",
    }
    (HERE / "input.json").write_text(json.dumps([case["input"] for case in cases]) + "\n")
    (HERE / "probe.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({"generator_sha256": data["generator_sha256"],
                      "canonical_rule_sha256": data["canonical_rule_sha256"],
                      "canonical_self_check_failures": [case["name"] for case in cases[:5] if case["self_check_errors"]],
                      "baseline_counts": cases[-1]["counts"],
                      "control_results": [{k: v for k, v in record.items() if k != "input"} for record in controls]}, indent=2))


if __name__ == "__main__":
    main()
