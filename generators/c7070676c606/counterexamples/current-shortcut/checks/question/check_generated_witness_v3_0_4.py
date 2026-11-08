"""Source-bound shortcut evidence; one selected-rule Racket bridge, no snapshot.

From WORK:
  TMPDIR=/dev/shm/arc-review-604d32c6dec0-tmp RACKET_PATH=/dev/shm/arc-review-604d32c6dec0/WORK/.review/racket-runtime/racket/bin/racket PYTHONPATH=/dev/shm/arc-review-604d32c6dec0/WORK/repo/src:/dev/shm/arc-review-604d32c6dec0/WORK/repo/shared/runtime /dev/shm/arc-review-604d32c6dec0/WORK/.venv/bin/python -B checks/question/check_generated_witness_v3_0_4.py
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arc_repl.builtins import _unwrap
from arc_repl.executor import ArcExecutor
from reviewer_support import canonical_pairs, canonical_path


TASK = "c7070676c606"
EXPECTED_GENERATOR = "e9121bbc33924c5613c73f5c5194251c5a3999be33ee6f23791faccb8366efea"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def components(grid):
    """Independent union-find, restricted to green orthogonal neighbors."""
    parents = {(r, c): (r, c) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value == 3}

    def rep(cell):
        while parents[cell] != cell:
            cell = parents[cell]
        return cell

    for r, c in parents:
        for neighbor in ((r + 1, c), (r, c + 1)):
            if neighbor in parents:
                parents[rep(neighbor)] = rep((r, c))
    groups = {}
    for cell in parents:
        groups.setdefault(rep(cell), set()).add(cell)
    return sorted((cells for cells in groups.values() if all(r > 0 for r, c in cells)), key=min)


def top_to_bottom(grid):
    rank = grid[0].count(1)
    objs = components(grid)
    output = [row[:] for row in grid]
    if 1 <= rank <= len(objs):
        for r, c in objs[rank - 1]:
            output[r][c] = 2
    return output


def main():
    source = ROOT / "generators" / TASK / "generator.py"
    source_hash = digest(source)
    if source_hash != EXPECTED_GENERATOR:
        raise ValueError("This reproduction is pinned to the final reviewed generator bytes")
    spec = importlib.util.spec_from_file_location("question_generator", source)
    gen = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gen
    spec.loader.exec_module(gen)
    observed_probe = HERE.parent / "blue-components/rescore.py"
    independent_blue = {}
    nodes = [node for node in ast.parse(observed_probe.read_text()).body
             if isinstance(node, ast.FunctionDef) and node.name in {"components", "global_blue_components"}]
    assert len(nodes) == 2
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(observed_probe), "exec"), independent_blue)
    ascending_probe = HERE.parent / "ascending-ranks/rescore.py"
    independent_ascending = {}
    ascending_nodes = [node for node in ast.parse(ascending_probe.read_text()).body
                       if isinstance(node, ast.FunctionDef) and node.name in {"eligible_components", "constant_smallest_rank"}]
    assert len(ascending_nodes) == 2
    exec(compile(ast.Module(body=ascending_nodes, type_ignores=[]), str(ascending_probe), "exec"), independent_ascending)
    fixtures = json.loads((source.parent / "counterexamples/semantic_boundaries.json").read_text())
    compact = next(case["input"] for case in fixtures["cases"] if case["id"] == "compact_eight_rival_witness")
    generated = gen.generate(0, 0, difficulty="easy")
    cases = {"compact_boundary_fixture": compact, "generated_seed0_index0_easy": generated}
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    with canonical_path(ROOT).open() as handle:
        rows = (json.loads(line) for line in handle if line.strip())
        records = [row for row in rows if row.get("task_id") == TASK]
    if len(records) != 1:
        raise ValueError("Expected one selected canonical record")
    program = records[0]["program_solution"]
    rule_hash = hashlib.sha256(program.encode()).hexdigest()
    if rule_hash != fixtures["reference"]["rule_text_sha256"]:
        raise ValueError("Reference changed from retained fixtures")
    report = {"schema": "c7070676c606-shortcut-question-evidence-v1", "task_id": TASK,
              "generator_version": gen.VERSION, "generator_sha256": source_hash, "rule_text_sha256": rule_hash,
              "script_sha256": digest(Path(__file__)),
              "independent_blue_component_script_sha256": digest(observed_probe),
              "independent_ascending_rank_script_sha256": digest(ascending_probe),
              "question_sha256": digest(ROOT / "REVIEW/questions/generator-shortcuts.json"),
              "replay": "TMPDIR=/dev/shm/arc-review-604d32c6dec0-tmp RACKET_PATH=/dev/shm/arc-review-604d32c6dec0/WORK/.review/racket-runtime/racket/bin/racket PYTHONPATH=/dev/shm/arc-review-604d32c6dec0/WORK/repo/src:/dev/shm/arc-review-604d32c6dec0/WORK/repo/shared/runtime /dev/shm/arc-review-604d32c6dec0/WORK/.venv/bin/python -B checks/question/check_generated_witness_v3_0_4.py",
              "execution": {"argv": sys.orig_argv, "cwd": str(Path.cwd())},
              "generation_call": {"seed": 0, "sample_index": 0, "difficulty": "easy", "overrides": {}},
              "canonical_checks": [], "canonical_rival_fit": {}, "cases": {}}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        report["canonical_rival_fit"][name] = [rival(pair["input"]) == pair["output"] for pair in canonical]
    report["independent_top_to_bottom_canonical_fit"] = [top_to_bottom(pair["input"]) == pair["output"] for pair in canonical]
    report["lesson_competitor_canonical_fit"] = {name: [rival(pair["input"]) == pair["output"] for pair in canonical] for name, rival in gen.LESSON_COMPETITORS.items()}
    report["lesson_only_competitors"] = sorted(set(gen.LESSON_COMPETITORS) - set(gen.CANONICAL_SHORTCUTS))
    task = {"train": [{"input": pair["input"], "output": pair["output"]} for pair in canonical],
            "test": [{"input": grid} for grid in cases.values()]}
    with ArcExecutor(task, use_racket=True) as executor:
        observation = executor.step(program)
        if observation.startswith("ERROR"):
            raise RuntimeError(observation)
        for index, pair in enumerate(canonical):
            observation = executor.step(f"(test! {index})")
            report["canonical_checks"].append({"variant": pair["variant"], "split": pair["split"],
                                                "pair_index": pair["pair_index"], "observation": observation,
                                                "passed": "PASS" in observation and "FAIL" not in observation})
        for index, (name, grid) in enumerate(cases.items()):
            observation = executor.step(f"(apply! {index})")
            output = None
            for token in observation.split():
                if token.startswith("_") and token[1:].isdigit() and token in executor._results:
                    output = _unwrap(executor._results[token])
                    break
            if output is None:
                raise RuntimeError(observation)
            rival_output = top_to_bottom(grid)
            report["cases"][name] = {
                "input": grid, "output": output, "top_to_bottom_output": rival_output,
                "input_sha256": grid_digest(grid), "output_sha256": grid_digest(output),
                "top_to_bottom_output_sha256": grid_digest(rival_output),
                "self_check": gen.self_check(grid), "observation": observation,
                "independent_rival_matches_declared": rival_output == gen.CANONICAL_SHORTCUTS["top_to_bottom"](grid),
                "refuted_rivals": [rival_name for rival_name, rival in gen.CANONICAL_SHORTCUTS.items() if rival(grid) != output],
                "lesson_competitor_matches_reference": {rival_name: rival(grid) == output for rival_name, rival in gen.LESSON_COMPETITORS.items()},
                "top_row_blue_cells": grid[0].count(1),
                "global_blue_cells": sum(row.count(1) for row in grid),
                "global_blue_components": len(independent_blue["components"](grid, 1)),
                "independent_global_blue_components_output": independent_blue["global_blue_components"](grid),
                "independent_global_blue_components_matches_declared": independent_blue["global_blue_components"](grid) == gen.LESSON_COMPETITORS["global_blue_components"](grid),
                "independent_ascending_rank_matches_declared": {str(rank): independent_ascending["constant_smallest_rank"](grid, rank) == gen.LESSON_COMPETITORS[f"constant_smallest_rank_{rank}"](grid) for rank in range(1, 6)},
                "components_in_discovery_order": [{"size": len(cells), "first_occupied": min(cells), "cells": sorted(cells)} for cells in components(grid)],
                "recolored_cells": [[r, c] for r, row in enumerate(grid) for c, value in enumerate(row) if value != output[r][c]],
                "rival_recolored_cells": [[r, c] for r, row in enumerate(grid) for c, value in enumerate(row) if value != rival_output[r][c]],
            }
        report["runtime"] = executor._bridge.runtime_identity
    report["generator_source_stable"] = source_hash == digest(source)
    report["passed"] = (report["generator_source_stable"]
                        and len(gen.LESSON_COMPETITORS) == 26
                        and report["cases"]["generated_seed0_index0_easy"]["lesson_competitor_matches_reference"]["constant_smallest_rank_2"] is False
                        and all(all(row["independent_ascending_rank_matches_declared"].values()) for row in report["cases"].values())
                        and all(report["lesson_competitor_canonical_fit"]["global_blue_components"])
                        and report["cases"]["generated_seed0_index0_easy"]["lesson_competitor_matches_reference"]["global_blue_components"] is False
                        and all(row["independent_global_blue_components_matches_declared"] for row in report["cases"].values())
                        and all(row["passed"] for row in report["canonical_checks"])
                        and all(all(fits) for fits in report["canonical_rival_fit"].values())
                        and all(report["independent_top_to_bottom_canonical_fit"])
                        and all(not row["self_check"] and row["independent_rival_matches_declared"]
                                and len(row["refuted_rivals"]) == 8 for row in report["cases"].values()))
    out = HERE / "v3.0.4-generated-witness.json"
    with out.open("x") as handle:
        handle.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(out), "passed": report["passed"],
                      "generator_version": gen.VERSION, "generator_sha256": source_hash, "rule_text_sha256": rule_hash,
                      "script_sha256": report["script_sha256"],
                      "cases": {name: {"shape": [len(row["input"]), len(row["input"][0])],
                                       "input_rows": ["".join(map(str, line)) for line in row["input"]],
                                       "output_rows": ["".join(map(str, line)) for line in row["output"]],
                                       "rival_rows": ["".join(map(str, line)) for line in row["top_to_bottom_output"]],
                                       "recolored_cells": row["recolored_cells"],
                                       "rival_recolored_cells": row["rival_recolored_cells"],
                                       "refuted_rivals": row["refuted_rivals"]} for name, row in report["cases"].items()}}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
