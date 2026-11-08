#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

ROOT = find_root(__file__)
OUT_ROOT = ROOT.parent / "checks" / "audit"


def install_packet_scripts_namespace() -> None:
    qualified = "scripts.comment_solutions"
    if qualified in sys.modules:
        return
    source = ROOT / "shared" / "tools" / "comment_solutions.py"
    package = sys.modules.get("scripts")
    if package is None:
        package = types.ModuleType("scripts")
        package.__path__ = [str(source.parent)]
        sys.modules["scripts"] = package
    spec = importlib.util.spec_from_file_location(qualified, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = module
    spec.loader.exec_module(module)


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def canonical_program(task_id: str) -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row["program_solution"]
    raise RuntimeError(f"missing canonical program for {task_id}")


def parity_slope_rival(gen: Any, grid: list[list[int]]) -> list[list[int]]:
    info, errors = gen._analyse(grid)
    if errors:
        raise ValueError(errors)
    n = info["n_cells"]
    last = info["ordered_red"][-1]
    if n == 1:
        step_r = -1 if last[0] > info["grid_size"] / 2 else 1
        step_c = step_r
    else:
        step_r = -1
        step_c = -1 if n % 2 == 1 else 1
    new_bottom = (last[0] + n * step_r, last[1] + n * step_c)
    out = [[7] * info["grid_size"] for _ in range(info["grid_size"])]
    for index in range(n + 1):
        row = new_bottom[0] + index * step_r
        col = new_bottom[1] + index * step_c
        if 0 <= row < info["grid_size"] and 0 <= col < info["grid_size"]:
            out[row][col] = 2
    return out


def audit_6e() -> dict[str, Any]:
    task_id = "6e18fab2c2e5"
    gen, source_path, source_sha = load_selected_generator(task_id, root=ROOT)
    seed = 1234
    rows = []
    for sample_index in range(6):
        grid = gen.generate(seed, sample_index, difficulty="medium")
        intended = gen.rule_mirror(grid)
        rival = parity_slope_rival(gen, grid)
        rows.append(
            {
                "sample_index": sample_index,
                "observed": gen.observe_overrides(grid),
                "validator_errors": gen.self_check(grid),
                "input": grid,
                "intended_output": intended,
                "rival_output": rival,
                "rival_matches": rival == intended,
            }
        )
    demos = [
        {"input": row["input"], "output": row["intended_output"]}
        for row in rows[:5]
    ]
    query = {"input": rows[5]["input"], "output": rows[5]["intended_output"]}

    install_packet_scripts_namespace()
    bridge = RacketBridge(timeout=30, max_calls_before_restart=16)
    try:
        bridge.eval_text(f"(define __audit_rule {wrap_rule(canonical_program(task_id))})")
        bridge.define_grid("__audit_input", rows[5]["input"])
        racket_output = bridge.eval_text("(__audit_rule __audit_input)")
        runtime = bridge.runtime_identity
    finally:
        bridge.shutdown()

    result = {
        "schema": "audit-6e18fab2c2e5-v1",
        "task_id": task_id,
        "generator_path": str(source_path.relative_to(ROOT)),
        "generator_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "rival": (
            "derive output diagonal slope from n_cells parity "
            "(odd=main, even=anti), ignoring input slope"
        ),
        "seed": seed,
        "difficulty": "medium",
        "demo_indices": [0, 1, 2, 3, 4],
        "query_index": 5,
        "demo_observations": [row["observed"] for row in rows[:5]],
        "demos_all_fit_rival": all(row["rival_matches"] for row in rows[:5]),
        "query_disagrees": not rows[5]["rival_matches"],
        "lesson_identifiable_result": gen.lesson_identifiable(demos, query),
        "query": rows[5],
        "racket_output": racket_output,
        "racket_matches_python_intended": racket_output == rows[5]["intended_output"],
        "racket_runtime": runtime,
    }
    dump(OUT_ROOT / task_id / "counterexample.json", result)
    dump(OUT_ROOT / task_id / "input.json", rows[5]["input"])
    return result


def exact_match_output(gen: Any, grid: list[list[int]]) -> list[list[int]]:
    _template, _outside, matches = gen._semantic_parts(grid)
    if len(matches) != 1:
        raise ValueError(f"expected one exact target, got {len(matches)}")
    out = [row[:] for row in grid]
    for row, col in matches[0]["cells"]:
        out[row][col] = 5
    return out


def audit_bdd() -> dict[str, Any]:
    task_id = "bdd177308a5b"
    gen, source_path, source_sha = load_selected_generator(task_id, root=ROOT)
    canonical = canonical_pairs(task_id, root=ROOT)
    counts = {
        "zones": Counter(),
        "template_sizes": Counter(),
        "distractor_counts": Counter(),
        "dimensions": Counter(),
    }
    failures = []
    unique = set()
    draws = 0
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(100):
            sample_index = seed % 32
            try:
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                errors = gen.self_check(grid)
                observed = gen.observe_overrides(grid)
                intended = exact_match_output(gen, grid)
                rival = gen.SEMANTIC_RIVALS["dihedral_invariant_all"](grid)
                witness = gen.SEMANTIC_WITNESSES["orientation_near_miss"](grid)
                if errors or not witness or rival == intended:
                    failures.append(
                        {
                            "difficulty": difficulty,
                            "seed": seed,
                            "sample_index": sample_index,
                            "errors": errors,
                            "orientation_witness": witness,
                            "rival_disagrees": rival != intended,
                        }
                    )
                counts["zones"][observed["target_zone"]] += 1
                counts["template_sizes"][str(observed["template_size"])] += 1
                counts["distractor_counts"][str(observed["distractor_count"])] += 1
                counts["dimensions"][f"{observed['grid_h']}x{observed['grid_w']}"] += 1
                unique.add(json.dumps(grid, separators=(",", ":")))
                draws += 1
            except Exception as exc:  # retained as evidence, not suppressed
                failures.append(
                    {
                        "difficulty": difficulty,
                        "seed": seed,
                        "sample_index": sample_index,
                        "exception": f"{type(exc).__name__}: {exc}",
                    }
                )
    canonical_errors = [gen.self_check(pair["input"]) for pair in canonical]
    result = {
        "schema": "audit-bdd177308a5b-v1",
        "task_id": task_id,
        "generator_path": str(source_path.relative_to(ROOT)),
        "generator_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "canonical_pairs": len(canonical),
        "canonical_self_check_errors": canonical_errors,
        "sampling": {
            "draws": draws,
            "unique_inputs": len(unique),
            "bands": ["easy", "medium", "hard"],
            "seeds_per_band": 100,
            "counts": {name: dict(counter) for name, counter in counts.items()},
            "failures": failures,
        },
        "checks": [
            "all sampled inputs pass self_check and observable axes",
            "every sample contains an orientation near miss",
            "the declared dihedral-invariant rival disagrees with exact-match output",
            "all canonical inputs pass current grammar",
        ],
        "finding": "No issue found" if not failures and not any(canonical_errors) else "Actionable sample failure",
    }
    dump(OUT_ROOT / task_id / "sampling.json", result)
    return result


def main() -> int:
    result_6e = audit_6e()
    result_bdd = audit_bdd()
    summary = {
        "6e18fab2c2e5": {
            "generator_sha256": result_6e["generator_sha256"],
            "demos_all_fit_rival": result_6e["demos_all_fit_rival"],
            "query_disagrees": result_6e["query_disagrees"],
            "lesson_identifiable_result": result_6e["lesson_identifiable_result"],
            "racket_matches_python_intended": result_6e["racket_matches_python_intended"],
        },
        "bdd177308a5b": {
            "generator_sha256": result_bdd["generator_sha256"],
            "draws": result_bdd["sampling"]["draws"],
            "unique_inputs": result_bdd["sampling"]["unique_inputs"],
            "failure_count": len(result_bdd["sampling"]["failures"]),
            "finding": result_bdd["finding"],
        },
    }
    dump(OUT_ROOT / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if (
        result_6e["demos_all_fit_rival"]
        and result_6e["query_disagrees"]
        and result_6e["racket_matches_python_intended"]
        and result_6e["lesson_identifiable_result"] == []
        and result_bdd["finding"] == "No issue found"
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
