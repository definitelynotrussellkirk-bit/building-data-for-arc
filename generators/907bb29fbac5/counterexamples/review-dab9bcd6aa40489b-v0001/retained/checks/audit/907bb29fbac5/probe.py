#!/usr/bin/env python3
"""Bounded findings-only audit; reference execution uses the public apply CLI."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
TASK = "907bb29fbac5"
GEN_PATH = REPO / "generators" / TASK / "generator.py"
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "shared/runtime"))


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_generator_907bb29fbac5", GEN_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gallery(grid, mode):
    """Independent expected/rival definitions; keep diagonal blank for fair rivals."""
    masks = [[grid[r][p * 5 + c] != 0 for r in range(4) for c in range(4)]
             for p in range(3)]
    out = [[0] * 14 for _ in range(14)]
    for a in range(3):
        for b in range(3):
            if a == b:
                continue
            for k in range(16):
                av, bv = masks[a][k], masks[b][k]
                if mode == "xor":
                    keep = av != bv
                elif mode == "or":
                    keep = av or bv
                elif mode == "and":
                    keep = av and bv
                elif mode == "left_minus_right":
                    keep = av and not bv
                elif mode == "global_core_erasure":
                    # A plausible wrong shortcut: remove only overlap shared by all panels.
                    keep = (av or bv) and not all(m[k] for m in masks)
                else:
                    raise ValueError(mode)
                if keep:
                    out[5 * a + k // 4][5 * b + k % 4] = 7
    return out


def prepare():
    gen = load_generator()
    rows = []
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rows.append(row)
    assert len(rows) == 1, len(rows)
    canonical = rows[0]
    rule = canonical["program_solution"]
    normalized = " ".join(rule.split())
    rule_hash = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    identity = {
        "task_id": TASK,
        "generator_path": str(GEN_PATH),
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "generator_version": gen.VERSION,
        "declared_rule_hash": gen.RULE_HASH,
        "canonical_rule_hash": rule_hash,
        "canonical_rule_sha256_raw": hashlib.sha256(rule.encode()).hexdigest(),
        "canonical_rule_sha256_normalized": hashlib.sha256(normalized.encode()).hexdigest(),
        "hash_definition": "sha256(space-joined rule.split())[:12]",
    }
    assert rule_hash == gen.RULE_HASH
    write("identity.json", identity)
    write("canonical_task.json", canonical)
    cases = []
    for split in ("train", "test"):
        for index, pair in enumerate(canonical[split]):
            cases.append({
                "name": f"canonical_{split}_{index}", "origin": "canonical",
                "split": split, "index": index, "input": pair["input"],
                "canonical_output": pair["output"],
            })
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            sample_index = 3 * seed + 1
            kwargs = {"difficulty": band}
            cases.append({
                "name": f"default_{band}_seed_{seed}", "origin": "generated_default",
                "seed": seed, "sample_index": sample_index, "kwargs": kwargs,
                "input": gen.generate(seed, sample_index, **kwargs),
            })
        for count in range(4, 8):
            for profile in ("balanced", "shared_core"):
                kwargs = {"difficulty": band, "grid_h": 4, "grid_w": 14,
                          "panel_cell_count": count, "overlap_profile": profile}
                cases.append({
                    "name": f"axes_{band}_count_{count}_{profile}",
                    "origin": "generated_joint_axes", "seed": 177, "sample_index": 23,
                    "kwargs": kwargs, "input": gen.generate(177, 23, **kwargs),
                })
    assert len(cases) == 53
    validation = []
    rivals = []
    mirror = []
    expected = []
    for case in cases:
        grid = case["input"]
        domain = gen.self_check(grid)
        facts = gen.semantic_observables(grid)
        observed = gen.observe_overrides(grid)
        independent = gallery(grid, "xor")
        mirrored = gen.rule_mirror(grid)
        details = {
            "name": case["name"], "origin": case["origin"], "self_check_errors": domain,
            "facts": facts, "observed_axes": observed,
            "independent_matches_generator_mirror": independent == mirrored,
        }
        if case["origin"] == "canonical":
            details["canonical_signature"] = gen.canonical_profile_signature(grid)
            details["independent_matches_canonical"] = independent == case["canonical_output"]
            assert details["independent_matches_canonical"], case["name"]
        else:
            details["deterministic_replay"] = grid == gen.generate(
                case["seed"], case["sample_index"], **case["kwargs"])
            details["all_pair_truth_branches_present"] = all(
                all(n > 0 for n in truth.values())
                for truth in facts["pair_truth_counts"].values())
            requested = {k: v for k, v in case["kwargs"].items() if k != "difficulty"}
            details["overrides_match"] = all(observed.get(k) == v for k, v in requested.items())
            assert details["deterministic_replay"]
            assert details["all_pair_truth_branches_present"]
            assert details["overrides_match"]
        assert not domain, (case["name"], domain)
        assert independent == mirrored, case["name"]
        validation.append(details)
        expected.append(independent)
        mirror.append(mirrored)
        rivals.append({name: gallery(grid, name) for name in (
            "or", "and", "left_minus_right", "global_core_erasure")})
    mutations = [{"name": name, "input": grid, "self_check_errors": gen.self_check(grid)}
                 for name, grid in gen.mutation_fixtures()]
    assert len(mutations) == 5 and all(item["self_check_errors"] for item in mutations)
    write("input.json", [case["input"] for case in cases])
    write("cases.json", cases)
    write("expected.json", expected)
    write("generator_mirror.json", mirror)
    write("rivals.json", rivals)
    write("domain_validation.json", {"cases": validation, "negative_fixtures": mutations})
    print(json.dumps({"prepared": len(cases), "canonical": 5, "generated": 48,
                      "negative_fixtures_rejected": len(mutations), **identity}, indent=2))


def compare():
    cases = json.loads((HERE / "cases.json").read_text())
    expected = json.loads((HERE / "expected.json").read_text())
    rivals = json.loads((HERE / "rivals.json").read_text())
    validation = json.loads((HERE / "domain_validation.json").read_text())
    racket = json.loads((HERE / "racket.json").read_text())
    identity = json.loads((HERE / "identity.json").read_text())
    results = racket["results"]
    assert len(results) == len(cases), (len(results), len(cases))
    rows = []
    for case, wanted, rival, result in zip(cases, expected, rivals, results):
        rows.append({
            "name": case["name"], "origin": case["origin"],
            "reference_error": result.get("error"),
            "independent_xor_matches_racket": wanted == result.get("output"),
            "rival_matches": {name: grid == result.get("output") for name, grid in rival.items()},
            "rival_mismatched_cells": {
                name: sum(x != y for rr, ss in zip(grid, result.get("output") or [])
                          for x, y in zip(rr, ss)) for name, grid in rival.items()},
        })
    rivals_summary = {}
    for name in rivals[0]:
        rivals_summary[name] = {}
        for origin in ("canonical", "generated_default", "generated_joint_axes"):
            group = [r for r in rows if r["origin"] == origin]
            rivals_summary[name][origin] = {
                "matched": sum(r["rival_matches"][name] for r in group), "total": len(group)}
    summary = {
        "classification": "No issue found in this focused audit",
        "input_count": len(cases),
        "canonical_count": sum(c["origin"] == "canonical" for c in cases),
        "generated_count": sum(c["origin"] != "canonical" for c in cases),
        "reference_errors": sum(r["reference_error"] is not None for r in rows),
        "independent_xor_mismatches": sum(not r["independent_xor_matches_racket"] for r in rows),
        "all_inputs_pass_self_check": all(not c["self_check_errors"] for c in validation["cases"]),
        "negative_fixtures_rejected": sum(bool(m["self_check_errors"])
                                          for m in validation["negative_fixtures"]),
        "rivals": rivals_summary,
        "executed_rule_hash": racket.get("executed_rule_hash"),
        "rule_hash_matches_catalog": racket.get("rule_hash_matches_catalog"),
        "generator_unchanged": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest()
                                 == identity["generator_sha256"],
        "coverage": {
            "canonical": "All four train inputs and one test input in the one current canonical row",
            "default": "difficulty easy/medium/hard; seed 0..7 inclusive; sample_index 3*seed+1",
            "joint_axes": "difficulty easy/medium/hard x panel_cell_count 4..7 inclusive x overlap_profile balanced/shared_core; seed=177, sample_index=23, grid_h=4, grid_w=14",
        },
    }
    write("comparison.json", {"summary": summary, "cases": rows})
    print(json.dumps(summary, indent=2))
    assert summary["reference_errors"] == 0
    assert summary["independent_xor_mismatches"] == 0
    assert summary["all_inputs_pass_self_check"]
    assert summary["generator_unchanged"]
    assert summary["executed_rule_hash"] == identity["canonical_rule_hash"]
    assert summary["rule_hash_matches_catalog"] is True


if __name__ == "__main__":
    {"prepare": prepare, "compare": compare}[sys.argv[1]]()
