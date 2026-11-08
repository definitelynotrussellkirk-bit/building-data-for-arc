"""Findings-only, exact-source audit; uses the existing runtime, no snapshot."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import types

from reviewer_support import canonical_pairs, find_root, load_selected_generator
from arcpuzzles.catalog import Catalog


TASK_ID = "6b4b56166bfd"
EXPECTED_SOURCE = "f5199baa50a2c21157599f14b282471082818630273d028e420116e61353e84b"
EVIDENCE = Path(__file__).resolve().parent
ROOT = find_root(__file__)

# The library stores runtime scripts under shared/tools.  Expose that exact
# existing directory as a package in this process; do not copy or edit it.
if "scripts" not in sys.modules:
    scripts = types.ModuleType("scripts")
    scripts.__path__ = [str(ROOT / "shared/tools")]
    sys.modules["scripts"] = scripts

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators import runner
from puzzle_generators.rule_wrap import wrap_rule
from scripts.generator_semantic_gate import check_canonical_ambiguity


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def changes(actual, rival):
    return [
        {"row": r, "column": c, "reference": value, "rival": rival[r][c]}
        for r, row in enumerate(actual)
        for c, value in enumerate(row)
        if value != rival[r][c]
    ]


def rotate_only_at_or_above_pivot(grid):
    """Copy only seeds on or above the pivot row; preserve other input cells."""
    pivots = [(r, c) for r, row in enumerate(grid)
              for c, value in enumerate(row) if value == 5]
    if len(pivots) != 1:
        raise ValueError("expected one pivot")
    pr, pc = pivots[0]
    result = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color in (0, 5) or r > pr:
                continue
            dr, dc = r - pr, c - pc
            for rr, cc in ((dr, dc), (dc, -dr), (-dr, -dc), (-dc, dr)):
                nr, nc = pr + rr, pc + cc
                if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]):
                    result[nr][nc] = color
    return result


def rotation_scores(pairs):
    fits = [rotate_only_at_or_above_pivot(pair["input"]) == pair["output"]
            for pair in pairs]
    return [
        {"query_index": query,
         "demonstration_indices": [i for i in range(len(pairs)) if i != query],
         "rival_fits_all_demonstrations": all(fits[i] for i in range(len(pairs)) if i != query),
         "rival_agrees_query": fits[query],
         "status": ("ambiguous" if all(fits[i] for i in range(len(pairs)) if i != query)
                    and not fits[query] else "survived_all" if all(fits) else "refuted")}
        for query in range(len(pairs))
    ]


def main():
    gen, source_path, source_hash = load_selected_generator(TASK_ID, root=ROOT)
    assert source_hash == EXPECTED_SOURCE, (source_path, source_hash)
    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    variants = Catalog(ROOT).get(TASK_ID)["variants"]
    rule_sources = {variant["program_solution"] for variant in variants}
    assert len(rule_sources) == 1
    source = rule_sources.pop()
    rule_hash = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert rule_hash == gen.RULE_HASH == "f2aaf100dc45"
    callable_text = wrap_rule(source)
    bundle = runner.GeneratorBundle(
        task_id=TASK_ID, rule_task_id=TASK_ID, rule_source=source,
        rule_callable_text=callable_text,
        rule_file="shared/data/canonical/puzzles.jsonl",
        generator_module=gen, allow_identity_output=False, kind="per_puzzle",
    )
    # Any unexpected runner rejection artifacts must stay in this audit folder.
    runner.REJECT_DIR = EVIDENCE / "rejections"
    result = {
        "schema": "arcpuzzles-findings-only-probe-v1",
        "task_id": TASK_ID,
        "generator_source": str(source_path.relative_to(ROOT)),
        "generator_sha256": source_hash,
        "generator_version": gen.VERSION,
        "rule_hash": rule_hash,
        "rule_file": bundle.rule_file,
        "rule_source": source,
        "rule_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "rule_callable_sha256": hashlib.sha256(callable_text.encode()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "root": str(ROOT),
        "cwd": str(Path.cwd()),
        "execution": "existing RacketBridge and runner.run_one; no runtime copy or official check",
        "helper_hashes": {
            rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
            for rel in (
                "shared/runtime/reviewer_support.py",
                "shared/runtime/puzzle_generators/runner.py",
                "shared/runtime/puzzle_generators/rule_wrap.py",
                "shared/runtime/arc_repl/racket_bridge.py",
                "shared/tools/generator_semantic_gate.py",
                "docs/SEMANTIC_GATE_CONTRACT.md",
            )
        },
        "canonical": [], "lessons": [],
    }
    with RacketBridge(timeout=10.0) as bridge:
        function_name = "__audit_rule_6b4b56166bfd"
        bridge.eval_text(f"(define {function_name} {callable_text})")
        for pair in canonical:
            actual = runner._apply_rule(bridge, function_name, pair["input"])
            assert actual == pair["output"]
            assert actual == gen.rule_mirror(pair["input"])
            half = gen.CANONICAL_SHORTCUTS["half_turn_only"](pair["input"])
            upper = rotate_only_at_or_above_pivot(pair["input"])
            result["canonical"].append({
                **pair, "racket_output": actual,
                "canonical_label_matches_racket": True,
                "self_check": gen.self_check(pair["input"]),
                "declared_half_turn_shortcut_output": half,
                "declared_half_turn_shortcut_agrees": half == actual,
                "declared_half_turn_shortcut_differences": changes(actual, half),
                "upper_seed_rival_output": upper,
                "upper_seed_rival_agrees": upper == actual,
            })
        for label, difficulty, seed, start in (
            ("default", None, 1, 3),
            ("easy", "easy", 1, 33),
            ("hard", "hard", 1, 3),
        ):
            axes = {} if difficulty is None else {"difficulty": difficulty}
            instance = runner.run_one(
                TASK_ID, seed, start, n_train=3, n_test=1,
                bundle=bundle, bridge=bridge, fn_name=function_name, **axes,
            )
            pairs = instance["train"] + instance["test"]
            assert len({digest(pair["input"]) for pair in pairs}) == 4
            assert all(gen.self_check(pair["input"]) == [] for pair in pairs)
            assert all(gen.rule_mirror(pair["input"]) == pair["output"] for pair in pairs)
            fits = [rotate_only_at_or_above_pivot(pair["input"]) == pair["output"]
                    for pair in pairs]
            assert fits == [True, True, True, False], (label, fits)
            rival_output = rotate_only_at_or_above_pivot(instance["test"][0]["input"])
            result["lessons"].append({
                "difficulty_label": label, "difficulty_argument": difficulty,
                "overrides": {}, "instance": instance,
                "instance_sha256": digest(instance),
                "rival": "rotate_only_at_or_above_pivot",
                "rival_fits_each_pair": fits,
                "declared_lesson_hook_reasons": gen.lesson_identifiable(
                    copy.deepcopy(instance["train"]), copy.deepcopy(instance["test"][0])),
                "rival_query_output": rival_output,
                "query_differences": changes(instance["test"][0]["output"], rival_output),
                "rotations": rotation_scores(pairs),
            })
        result["racket_binary"] = bridge.racket_binary
    result["canonical_shortcut_checker_component"] = check_canonical_ambiguity(
        TASK_ID, declared_shortcuts=gen.CANONICAL_SHORTCUTS,
        rival_claims={}, witness_rivals=gen.WITNESS_RIVALS,
    )
    result["summary"] = {
        "canonical_pairs_executed": len(canonical),
        "canonical_labels_matching_racket": len(canonical),
        "declared_half_turn_canonical_matches": sum(
            pair["declared_half_turn_shortcut_agrees"] for pair in result["canonical"]),
        "upper_seed_rival_canonical_matches": sum(
            pair["upper_seed_rival_agrees"] for pair in result["canonical"]),
        "generated_lessons_materialized": len(result["lessons"]),
        "generated_pairs_racket_executed": 4 * len(result["lessons"]),
        "production_ambiguities": len(result["lessons"]),
        "ambiguous_rotations": sum(
            row["status"] == "ambiguous"
            for lesson in result["lessons"] for row in lesson["rotations"]),
        "target_changed": hashlib.sha256(source_path.read_bytes()).hexdigest() != EXPECTED_SOURCE,
    }
    assert not result["summary"]["target_changed"]
    (EVIDENCE / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"], indent=2))
    print("Evidence:", EVIDENCE / "probe.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
