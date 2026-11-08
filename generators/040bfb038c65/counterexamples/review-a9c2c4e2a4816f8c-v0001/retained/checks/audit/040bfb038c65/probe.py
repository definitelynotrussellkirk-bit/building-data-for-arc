#!/usr/bin/env python3
"""Find/replay one production-order lesson ambiguous to a largest-blob rival.

Direct generator calls select the candidate only. Authoritative labels are
obtained separately using the public arcpuzzles apply and generate commands.
All writes stay beside this script; no private runner helper is imported.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared" / "runtime")]
from arcpuzzles import Catalog

TASK = "040bfb038c65"
SOURCE = REPO / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_target", SOURCE)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def blobs(grid):
    h, w = len(grid), len(grid[0])
    seen, result = set(), []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 4 or (r, c) in seen:
                continue
            seen.add((r, c))
            todo, cells = [(r, c)], []
            while todo:
                x, y = todo.pop()
                cells.append((x, y))
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < h and 0 <= ny < w and
                            grid[nx][ny] == 4 and (nx, ny) not in seen):
                        seen.add((nx, ny))
                        todo.append((nx, ny))
            result.append(sorted(cells))
    return result


def canonical(cells):
    variants = []
    for swap in (False, True):
        for sx in (-1, 1):
            for sy in (-1, 1):
                points = [(sx * (c if swap else r), sy * (r if swap else c))
                          for r, c in cells]
                mr = min(r for r, c in points)
                mc = min(c for r, c in points)
                variants.append(tuple(sorted((r - mr, c - mc) for r, c in points)))
    return min(variants)


def paint(grid, cells):
    result = [row[:] for row in grid]
    for r, c in cells:
        result[r][c] = 8
    return result


def rule_hypothesis(grid):
    objects = blobs(grid)
    keys = [canonical(cells) for cells in objects]
    counts = Counter(keys)
    target = next((cells for cells, key in zip(objects, keys) if counts[key] == 1), [])
    return paint(grid, target)


def largest_rival(grid):
    """Recolor the largest yellow 4-component; row-major first breaks ties."""
    objects = blobs(grid)
    return paint(grid, max(objects, key=len) if objects else [])


def write(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2) + "\n")


def find_witness():
    row = Catalog(REPO).get(TASK)
    canonical_results = []
    for vi, variant in enumerate(row["variants"]):
        for split in ("train", "test"):
            for pi, pair in enumerate(variant.get(split, [])):
                if "output" not in pair:
                    continue
                canonical_results.append({"variant": vi, "split": split,
                    "pair_index": pi, "matches": largest_rival(pair["input"]) == pair["output"]})
    assert all(item["matches"] for item in canonical_results), canonical_results
    records_examined = 0
    for seed in range(256):
        grids = [generator.generate(seed, i, difficulty=None) for i in range(4)]
        records_examined += 4
        checks = [generator.self_check(g, difficulty=None, meta=None) for g in grids]
        assert checks == [[], [], [], []], {"seed": seed, "checks": checks}
        matches = [largest_rival(g) == rule_hypothesis(g) for g in grids]
        if matches != [True, True, True, False]:
            continue
        records = []
        for i, grid in enumerate(grids):
            objects = blobs(grid)
            sizes = [len(o) for o in objects]
            target = rule_hypothesis(grid)
            records.append({"seed": seed, "sample_index": i, "difficulty": None,
                "overrides": {}, "split": "train" if i < 3 else "test",
                "pair_index": i if i < 3 else 0, "input": grid,
                "self_check": checks[i], "belongs_to_documented_generator_domain": True,
                "component_sizes_row_major": sizes,
                "component_cells_row_major": objects,
                "python_rule_hypothesis_output": target,
                "rival_output": largest_rival(grid),
                "rival_matches_python_hypothesis": matches[i]})
        witness = {"task_id": TASK,
            "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "rule_hash": row["rule_hash"], "witness_kind": "generated",
            "rival": "largest_yellow_blob_row_major_tie_break",
            "rival_definition": "Recolor to 8 the largest 4-connected yellow(4) component; break size ties by its first cell in row-major order.",
            "canonical_rival_fits": canonical_results,
            "declared_canonical_shortcuts": getattr(generator, "CANONICAL_SHORTCUTS", None),
            "declared_lesson_competitors": getattr(generator, "LESSON_COMPETITORS", None),
            "declared_examples_needed": generator.EXAMPLES_NEEDED,
            "lesson_policy": {"n_train": 3, "n_test": 1, "sample_indices": [0, 1, 2, 3],
                "query_sample_index": 3, "ordering": "production sequential accepted samples"},
            "search": {"seed_start": 0, "seed_end_inclusive": seed,
                "sample_indices_per_seed": [0, 1, 2, 3], "grids_examined": records_examined,
                "selection_basis": "Python rule hypothesis, then authoritative Racket validation required"},
            "records": records}
        write("input.json", grids)
        write("witness.json", witness)
        print(json.dumps({"seed": seed, "generator_sha256": witness["generator_sha256"],
            "rule_hash": row["rule_hash"], "search": witness["search"],
            "component_sizes": [r["component_sizes_row_major"] for r in records],
            "rival_matches_python_hypothesis": matches, "self_check": checks,
            "canonical_rival_fits": canonical_results}, indent=2))
        return
    raise SystemExit("No candidate found in the fixed search range")


def verify_witness():
    witness = json.loads((HERE / "witness.json").read_text())
    applied = json.loads((HERE / "racket.json").read_text())
    episode = json.loads((HERE / "production.jsonl").read_text())
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert source_hash == witness["generator_sha256"] == applied["generator_sha256"]
    assert source_hash == episode["provenance"]["generator_sha256"]
    assert witness["rule_hash"] == applied["executed_rule_hash"] == episode["executed_rule_hash"]
    assert applied["rule_hash_matches_catalog"] is True
    records = witness["records"]
    pairs = episode["train"] + episode["test"]
    assert len(records) == len(applied["results"]) == len(pairs) == 4
    assert len(episode["train"]) == 3 and len(episode["test"]) == 1
    assert episode["sample_indices"] == [0, 1, 2, 3]
    assert episode["rejections"] == []
    self_checks = []
    rival_matches = []
    output_differences = []
    for record, result, pair in zip(records, applied["results"], pairs):
        grid = record["input"]
        assert grid == generator.generate(record["seed"], record["sample_index"],
            difficulty=record["difficulty"], **record["overrides"])
        assert grid == result["input"] == pair["input"]
        assert result["error"] is None and result["valid_output"] is True
        authoritative_output = result["output"]
        assert authoritative_output == pair["output"]
        assert authoritative_output == record["python_rule_hypothesis_output"]
        self_checks.append(generator.self_check(grid, difficulty=None, meta=None))
        rival = largest_rival(grid)
        assert rival == record["rival_output"]
        rival_matches.append(rival == authoritative_output)
        differences = [[r, c, authoritative_output[r][c], rival[r][c]]
            for r in range(len(grid)) for c in range(len(grid[0]))
            if authoritative_output[r][c] != rival[r][c]]
        output_differences.append(differences)
        record["actual_racket_output"] = authoritative_output
        record["input_sha256"] = result["input_sha256"]
        record["output_sha256"] = result["output_sha256"]
        record["rival_matches_racket"] = rival_matches[-1]
        record["rival_differences_rc_actual_rival"] = differences
    assert self_checks == [[], [], [], []]
    assert rival_matches == [True, True, True, False]
    rotations = []
    for qi in range(4):
        demos = [i for i in range(4) if i != qi]
        fits_demos = all(rival_matches[i] for i in demos)
        rotations.append({"query_position": qi, "demonstration_positions": demos,
            "rival_fits_all_demonstrations": fits_demos,
            "rival_differs_on_query": not rival_matches[qi],
            "ambiguous_against_this_rival": fits_demos and not rival_matches[qi]})
    query = records[3]
    summary = {"task_id": TASK, "generator_sha256": source_hash,
        "rule_hash": applied["executed_rule_hash"],
        "rule_text_sha256": applied["rule_text_sha256"],
        "witness_kind": "generated", "seed": 11, "sample_indices": [0, 1, 2, 3],
        "difficulty": None, "overrides": {}, "unique_inputs": 4,
        "canonical_rival_fits": witness["canonical_rival_fits"],
        "self_check": self_checks, "authoritative_outputs_valid": 4,
        "python_rule_hypothesis_matches_racket": 4,
        "production": {"lessons": 1, "demonstrations": 3, "queries": 1,
            "sample_indices": episode["sample_indices"], "rejections": episode["rejections"],
            "rival_matches": rival_matches, "ambiguous_lessons": 1,
            "lesson_check": episode["lesson_check"]},
        "rotations": {"source_lessons": 1, "unique_inputs": 4, "rotated_queries": 4,
            "ambiguous_against_this_rival": sum(r["ambiguous_against_this_rival"] for r in rotations),
            "refuted_by_demonstrations": sum(not r["rival_fits_all_demonstrations"] for r in rotations),
            "rows": rotations},
        "query": {"input_shape": [len(query["input"]), len(query["input"][0])],
            "component_sizes_row_major": query["component_sizes_row_major"],
            "differing_cells_count": len(output_differences[3]),
            "differences_rc_actual_rival": output_differences[3]},
        "scope": "One source-bound lesson; no estimate of failure prevalence and no full battery."}
    witness["rule_text_sha256"] = applied["rule_text_sha256"]
    witness["authoritative_apply_command"] = applied["command"]
    witness["authoritative_apply_cwd"] = applied["cwd"]
    write("witness.json", witness)
    write("verification.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["find", "verify"])
    args = parser.parse_args()
    if args.mode == "find":
        find_witness()
    else:
        verify_witness()
