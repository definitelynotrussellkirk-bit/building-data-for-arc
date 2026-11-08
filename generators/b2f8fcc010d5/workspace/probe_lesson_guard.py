"""Bounded task-local adversarial probe; prepare labels, then verify Racket apply.

Run through review.py run from the packet's outer folder. The prepare report
explicitly separates Python screening from the later actual Racket receipt.
Every output directory/file must be new; no retained evidence is overwritten.
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import time

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "b2f8fcc010d5"
# Independent coordinates transcribed from the unchanged canonical Racket rule.
POSITIONS = ((0, 0), (1, 1), (0, 4), (1, 3), (2, 2), (3, 1),
             (4, 0), (3, 3), (4, 4))
ALL_CELLS = tuple(product(range(5), repeat=2))


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


def label(grid):
    values = [grid[r][c] for r, c in POSITIONS]
    return {"input": grid, "output": [values[:3], values[3:6], values[6:]]}


def brute_alternatives(demos, query, sources):
    """Enumerate complete one-output substitution rules, independent of the hook."""
    for index in range(9):
        out_r, out_c = divmod(index, 3)
        for source_r, source_c in sources:
            def rival(grid):
                result = label(grid)["output"]
                result[out_r][out_c] = grid[source_r][source_c]
                return result
            if (all(rival(pair["input"]) == pair["output"] for pair in demos)
                    and rival(query["input"]) != query["output"]):
                return True
    return False


def recolor(pair):
    mapping = {0: 0, **{color: 1 + color % 9 for color in range(1, 10)}}
    return {key: [[mapping[value] for value in row] for row in pair[key]]
            for key in ("input", "output")}


def prepare(out, baseline):
    started = time.monotonic()
    root = find_root(__file__)
    gen, source, source_sha = load_selected_generator(TASK, root=root)
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    canonical = canonical_pairs(TASK, root=root)
    canon_demos = [pair for pair in canonical if pair["split"] == "train"]
    canon_query = next(pair for pair in canonical if pair["split"] == "test")
    cases = []

    def retain(name, pair):
        assert not gen.self_check(pair["input"]), name
        cases.append({"name": name, **pair})

    for index, pair in enumerate(canonical):
        retain(f"canonical-{index}", {key: pair[key] for key in ("input", "output")})

    # Surface 1: every sampled-coordinate transposition, and every possible
    # single decoy substitution. Each witness is lawful under self_check.
    swap_count = 0
    for left, right in combinations(range(9), 2):
        grid = [[0] * 5 for _ in range(5)]
        unique = iter(range(2, 9))
        for index, (r, c) in enumerate(POSITIONS):
            grid[r][c] = 1 if index in (left, right) else next(unique)
        demo = label(grid)
        query = deepcopy(demo)
        r, c = POSITIONS[right]
        query["input"][r][c] = 2
        query = label(query["input"])
        assert not gen.self_check(demo["input"]) and not gen.self_check(query["input"])
        assert brute_alternatives([demo], query, POSITIONS)
        assert gen.lesson_identifiable([demo], query), (left, right)
        assert not gen.lesson_identifiable([demo], demo)
        swap_count += 1
        if (left, right) == (0, 8):
            retain("opposite-corner-tie-demo", demo)
            retain("opposite-corner-separated-query", query)

    decoy_count = 0
    for index, decoy in product(range(9), [cell for cell in ALL_CELLS if cell not in POSITIONS]):
        out_r, out_c = divmod(index, 3)
        demos, query = deepcopy(canon_demos), deepcopy(canon_query)
        for demo in demos:
            demo["input"][decoy[0]][decoy[1]] = demo["output"][out_r][out_c]
        expected = query["output"][out_r][out_c]
        replacement = next(value for row in query["output"] for value in row if value != expected)
        query["input"][decoy[0]][decoy[1]] = replacement
        assert all(not gen.self_check(pair["input"]) for pair in [*demos, query])
        findings = gen.lesson_identifiable(demos, query)
        assert any(str((out_r, out_c)) in reason for reason in findings), (index, decoy)
        decoy_count += 1
        if index == 4 and decoy == (0, 2):
            retain("center-copy-decoy-demo", {key: demos[0][key] for key in ("input", "output")})
            retain("center-copy-decoy-query", {key: query[key] for key in ("input", "output")})

    # Surface 2: ordered multi-query lessons, palette/decoy boundaries, and
    # injective foreground recoloring. This is a fixed, bounded Python screen.
    seeds = [*range(32), 67]
    cohort = []
    color_checks = 0
    oracle_checks = 0
    for band in ("easy", "medium", "hard"):
        pairs_by_seed = {}
        for seed in seeds:
            pairs = [label(gen.generate(seed, index, difficulty=band)) for index in range(8)]
            assert all(not gen.self_check(pair["input"]) for pair in pairs)
            pairs_by_seed[seed] = pairs
            if seed == 67 and band == "medium":
                for index, pair in enumerate(pairs):
                    retain(f"seed67-medium-{index}", pair)
        for n_train in (3, 4):
            counts = {"difficulty": band, "n_train": n_train, "episodes": len(seeds),
                      "supported_one_query": 0, "supported_four_queries": 0,
                      "episodes_rejected_only_by_decoys": 0, "unsupported_seeds_four_queries": []}
            for seed, pairs in pairs_by_seed.items():
                demos, queries = pairs[:n_train], pairs[n_train:n_train + 4]
                failures = [bool(gen.lesson_identifiable(demos, query)) for query in queries]
                reverse = [bool(gen.lesson_identifiable(demos, query)) for query in reversed(queries)]
                assert reverse == list(reversed(failures))
                sampled_failures = [brute_alternatives(demos, query, POSITIONS) for query in queries]
                all_failures = [brute_alternatives(demos, query, ALL_CELLS) for query in queries]
                assert failures == all_failures, (band, seed, n_train)
                oracle_checks += len(queries)
                colored = [bool(gen.lesson_identifiable([recolor(pair) for pair in demos], recolor(query)))
                           for query in queries]
                assert colored == failures, (band, seed, n_train)
                color_checks += len(queries)
                counts["supported_one_query"] += not failures[0]
                counts["supported_four_queries"] += not any(failures)
                counts["episodes_rejected_only_by_decoys"] += any(failures) and not any(sampled_failures)
                if any(failures):
                    counts["unsupported_seeds_four_queries"].append(seed)
            cohort.append(counts)

    for band, palette, kind, decoys in product(("easy", "medium", "hard"), (5, 9),
                                              gen.SAMPLED_KINDS, (0, 15)):
        grid = gen.generate(31, 17, difficulty=band, palette_size=palette,
                            sampled_kind=kind, decoy_count=decoys)
        pair = label(grid)
        retain(f"boundary-{band}-palette{palette}-{kind}-decoys{decoys}", pair)
        assert gen.observe_overrides(grid) == {"palette_size": palette,
                                               "sampled_kind": kind, "decoy_count": decoys}

    function_names = ("generate", "_validate_controls", "_draw_decoy_count", "_sampled_values",
                      "_rebut_nonzero_compression", "self_check", "observe_overrides")
    def definitions(path):
        return {node.name: ast.dump(node) for node in ast.parse(path.read_text()).body
                if isinstance(node, ast.FunctionDef) and node.name in function_names}
    unchanged = definitions(baseline) == definitions(source)
    assert unchanged, "per-grid sampling or validation changed"
    for line in canonical_path(root).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            program = row["program_solution"]
            break
    elapsed = time.monotonic() - started
    assert elapsed < 300, "bounded adversarial pass exceeded five minutes"
    report = {
        "schema": "b2f8fcc010d5-coordinate-lesson-probe-v1", "task_id": TASK,
        "generator_sha256": source_sha, "generator_version": gen.VERSION,
        "baseline_generator_sha256": digest(baseline.read_bytes()),
        "unchanged_sampling_and_validation_functions": list(function_names) if unchanged else [],
        "rule_hash": gen.RULE_HASH, "canonical_program_sha256": digest(program.encode()),
        "elapsed_seconds": round(elapsed, 6), "budget_seconds": 300,
        "surfaces": {"sampled_coordinate_swaps": swap_count,
                     "output_coordinate_decoy_substitutions": decoy_count,
                     "explicit_substitution_oracle_query_checks": oracle_checks,
                     "recolored_query_checks": color_checks,
                     "override_boundary_inputs": 36},
        "cohort": {"seeds": seeds, "sample_indices": list(range(8)), "rows": cohort,
                   "label_basis": "Python screening mirror; only selected retained inputs get separate Racket replay"},
        "racket_preparation": {"inputs": len(cases), "input_file": "inputs.json",
                               "expected_file": "expected.json", "executed": False},
        "limits": ["Guard rejects automatic unsupported lessons; it does not retry or alter the sampler.",
                   "Explicit unsupported episodes are diagnostic, not supported training data.",
                   "Finite cohort measures this source and these starts, not all-seed acceptance.",
                   "The rule family selects fixed input coordinates independently; other algorithms remain outside scope."]}
    (out / "inputs.json").write_text(json.dumps({"inputs": [case["input"] for case in cases]}, separators=(",", ":")) + "\n")
    (out / "expected.json").write_text(json.dumps(cases, separators=(",", ":")) + "\n")
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in ("generator_sha256", "elapsed_seconds", "surfaces", "cohort")}, indent=2))


def verify(out, applied_path, workflow_dir=None):
    report = json.loads((out / "report.json").read_text())
    expected = json.loads((out / "expected.json").read_text())
    applied = json.loads(applied_path.read_text())
    assert applied["generator_sha256"] == report["generator_sha256"]
    assert applied["executed_rule_hash"] == report["rule_hash"]
    assert applied["reference"] == "canonical" and applied["rule_hash_matches_catalog"]
    assert len(applied["results"]) == len(expected)
    for case, result in zip(expected, applied["results"], strict=True):
        assert result["error"] is None and result["valid_output"], case["name"]
        assert result["input"] == case["input"] and result["output"] == case["output"], case["name"]
        assert result["generator_domain"] == {"status": "valid", "errors": []}, case["name"]
    verified = {"status": "PASS", "task_id": TASK, "generator_sha256": report["generator_sha256"],
                "executed_rule_hash": applied["executed_rule_hash"],
                "canonical_program_sha256": report["canonical_program_sha256"],
                "executed_callable_sha256": applied["rule_text_sha256"],
                "racket_inputs": len(expected), "domain_valid": len(expected),
                "mirror_matches_actual_racket": len(expected),
                "files_sha256": {path.name: digest(path.read_bytes()) for path in
                                 (out / "report.json", out / "inputs.json", out / "expected.json", applied_path)}}
    if workflow_dir is not None:
        root = find_root(__file__)
        gen, _, source_sha = load_selected_generator(TASK, root=root)
        assert source_sha == report["generator_sha256"]
        files = {name: workflow_dir / name for name in (
            "before/episode.jsonl", "after/explicit-four-query.jsonl",
            "after/supported-four-query.jsonl", "after/automatic-rejection-command.json")}
        before, explicit, supported, rejected = [json.loads(path.read_text()) for path in files.values()]
        assert before["provenance"]["generator_sha256"] == report["baseline_generator_sha256"]
        assert before["lesson_check"]["status"] == "not_declared"
        assert before["sample_indices"] == [0, 1, 2, 3] and not before["rejections"]
        for episode in (explicit, supported):
            assert episode["provenance"]["generator_sha256"] == source_sha
            assert episode["executed_rule_hash"] == report["rule_hash"]
            assert len(episode["train"]) == 3 and len(episode["test"]) == 4
        assert explicit["train"] == before["train"] and explicit["test"][0] == before["test"][0]
        assert explicit["lesson_check"]["status"] == "diagnostic_unsupported"
        assert not explicit["provenance"]["demonstration_policy"]["automatic"]
        flags = [bool(row["reasons"]) for row in explicit["lesson_check"]["queries"]]
        assert flags == [True, False, True, True]
        assert [bool(gen.lesson_identifiable(explicit["train"], query))
                for query in reversed(explicit["test"])] == list(reversed(flags))
        assert supported["lesson_check"]["status"] == "passed_declared_hook"
        assert supported["provenance"]["demonstration_policy"]["automatic"]
        assert all(not row["reasons"] for row in supported["lesson_check"]["queries"])
        assert rejected["returncode"] == 1
        assert not (workflow_dir / "after/automatic-seed67.jsonl").exists()
        assert "Automatic lesson unsupported" in (workflow_dir / "after/automatic-seed67.log").read_text()
        pairs = before["train"] + before["test"]
        rotations = [bool(gen.lesson_identifiable(pairs[:index] + pairs[index + 1:], query))
                     for index, query in enumerate(pairs)]
        assert rotations[3]
        verified["workflow"] = {
            "baseline_automatic_seed67": "accepted_without_declared_check",
            "patched_automatic_seed67": "rejected_exit_1_no_episode_written",
            "patched_explicit_seed67_four_query_unsupported": flags,
            "four_pair_seed67_leave_one_out_unsupported": rotations,
            "query_reversal_preserves_independent_verdicts": True,
            "supported_automatic_seed1": {"demos": 3, "queries": 4, "status": "passed_declared_hook"},
            "before_after_seed67_inputs_and_racket_labels_identical": True,
            "files_sha256": {name: digest(path.read_bytes()) for name, path in files.items()}}
    destination = out / "verified.json"
    if destination.exists():
        raise FileExistsError(destination)
    destination.write_text(json.dumps(verified, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verified, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "verify"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--applied", type=Path)
    parser.add_argument("--workflow-dir", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        if args.baseline is None:
            parser.error("prepare requires --baseline")
        prepare(args.out, args.baseline)
    else:
        if args.applied is None:
            parser.error("verify requires --applied")
        verify(args.out, args.applied, args.workflow_dir)
