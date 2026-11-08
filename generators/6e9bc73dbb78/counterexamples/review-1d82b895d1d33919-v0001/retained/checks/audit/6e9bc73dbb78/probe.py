#!/usr/bin/env python3
"""Adversarial audit probe for generator 6e9bc73dbb78.

This probe is intentionally read-only with respect to the selected generator.
It checks the complete declared exact-control cross product, ordinary draws,
canonical rival behavior, and lesson-level declared-rival identifiability.
"""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
PACKET_ROOT = HERE.parents[4]
REPO = PACKET_ROOT / "WORK" / "repo"
RUNTIME = REPO / "shared" / "runtime"
for path in (RUNTIME, REPO / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from reviewer_support import canonical_pairs  # noqa: E402

TASK = "6e9bc73dbb78"
SOURCE = REPO / "generators" / TASK / "generator.py"
OUT = HERE.parent / "evidence.json"


def load_module():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    gen = load_module()
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    pairs = canonical_pairs(TASK, root=REPO, labeled_only=True)

    canonical_rivals = {}
    for name, rival in gen.SEMANTIC_RIVALS.items():
        matched = 0
        errors = []
        for pair in pairs:
            try:
                if rival(pair["input"]) == pair["output"]:
                    matched += 1
            except Exception as exc:  # retained as evidence, not hidden
                errors.append(f"{type(exc).__name__}: {exc}")
        canonical_rivals[name] = {
            "matched": matched,
            "total": len(pairs),
            "errors": errors,
            "declared_canonical_shortcut": name in gen.CANONICAL_SHORTCUTS,
        }

    values = {
        "grid_h": range(8, 15),
        "grid_w": range(9, 17),
        "n_repeat": range(2, 5),
        "size_profile": gen.SIZE_PROFILES,
        "color_order": gen.COLOR_ORDERS,
        "position_order": gen.POSITION_ORDERS,
    }
    keys = tuple(values)
    override_failures = []
    override_cases = 0
    for case_index, combo in enumerate(itertools.product(*(values[key] for key in keys))):
        overrides = dict(zip(keys, combo))
        override_cases += 1
        try:
            grid = gen.generate(700_000 + case_index, 100 + case_index, difficulty="hard", **overrides)
            errors = gen.self_check(grid)
            observed = gen.observe_overrides(grid)
            if errors or observed != overrides:
                override_failures.append({
                    "case_index": case_index,
                    "overrides": overrides,
                    "self_check": errors,
                    "observed": observed,
                })
        except Exception as exc:
            override_failures.append({
                "case_index": case_index,
                "overrides": overrides,
                "exception": f"{type(exc).__name__}: {exc}",
            })
        if len(override_failures) >= 20:
            break

    ordinary = {"requested": 1200, "generated": 0, "errors": [], "invalid": [], "unique": 0}
    unique = set()
    for index in range(ordinary["requested"]):
        difficulty = ("easy", "medium", "hard")[index % 3]
        try:
            grid = gen.generate(812_345, index, difficulty=difficulty)
            ordinary["generated"] += 1
            errors = gen.self_check(grid)
            if errors:
                ordinary["invalid"].append({"index": index, "errors": errors})
            unique.add(json.dumps(grid, separators=(",", ":")))
        except Exception as exc:
            ordinary["errors"].append({"index": index, "exception": f"{type(exc).__name__}: {exc}"})
    ordinary["unique"] = len(unique)

    # Materialize 200 consecutive six-pair lessons (five demonstrations plus one
    # query) from the production schedule, then hold out every position.  Labels use the input-pure mirror solely for
    # this task-local rival probe; the canonical/Racket authority is not modified.
    lessons = {"lessons": 200, "pairs_per_lesson": 6, "demos_per_rotation": 5, "rotations": 0, "ambiguous": [], "rival_errors": []}
    for lesson_index in range(lessons["lessons"]):
        items = []
        base = lesson_index * 6
        for offset in range(6):
            grid = gen.generate(991_337 + lesson_index, base + offset, difficulty=("easy", "medium", "hard")[lesson_index % 3])
            items.append({"input": grid, "output": gen.rule_mirror(grid)})
        for query_index in range(6):
            demos = [pair for i, pair in enumerate(items) if i != query_index]
            reasons = gen.lesson_identifiable(demos, items[query_index])
            lessons["rotations"] += 1
            if reasons:
                lessons["ambiguous"].append({
                    "lesson_index": lesson_index,
                    "query_index": query_index,
                    "reasons": reasons,
                    "pairs": items,
                })
                if len(lessons["ambiguous"]) >= 5:
                    break
        if len(lessons["ambiguous"]) >= 5:
            break

    report = {
        "schema": "arcpuzzles-adversarial-audit-v1",
        "task_id": TASK,
        "generator_sha256": source_hash,
        "canonical_pair_count": len(pairs),
        "canonical_rivals": canonical_rivals,
        "declared_override_cross_product": {
            "cases_attempted": override_cases,
            "expected_cases": 7 * 8 * 3 * 5 * 2 * 2,
            "failure_count": len(override_failures),
            "first_failures": override_failures,
        },
        "ordinary_draws": ordinary,
        "six_pair_lesson_rotation_probe": lessons,
        "verdict": "no_issue_found" if not override_failures and not ordinary["errors"] and not ordinary["invalid"] and not lessons["ambiguous"] else "issue_found",
        "limitations": [
            "Finite sampling does not prove all seeds or all undeclared semantic rivals.",
            "Lesson labels in this probe use the task-local Python mirror; canonical parity is checked separately by retained tests and canonical pairs.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "generator_sha256": source_hash,
        "canonical_pairs": len(pairs),
        "override_cases": override_cases,
        "override_failures": len(override_failures),
        "ordinary_generated": ordinary["generated"],
        "ordinary_errors": len(ordinary["errors"]),
        "ordinary_invalid": len(ordinary["invalid"]),
        "ordinary_unique": ordinary["unique"],
        "lesson_rotations": lessons["rotations"],
        "lesson_ambiguities": len(lessons["ambiguous"]),
        "verdict": report["verdict"],
    }, indent=2, sort_keys=True))
    return 0 if report["verdict"] == "no_issue_found" else 1


if __name__ == "__main__":
    raise SystemExit(main())
