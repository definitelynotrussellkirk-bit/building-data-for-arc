#!/usr/bin/env python3
"""Focused findings-only audit; obtain every label through public Racket apply.

Run from the outer packet root:
  WORK/.venv/bin/python review.py run ../.venv/bin/python ../checks/audit/8a2e39528187/probe.py

This writes only beside this file. It never edits the selected generator/rule.
Use --out NAME for a new output subdirectory when replaying (default: evidence).
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


TASK = "8a2e39528187"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "repo"
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs, canonical_path, load_selected_generator


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def components(grid):
    """Independent monochromatic 4-neighbor decomposition for the new rival."""
    seen, result = set(), []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0 or (r, c) in seen:
                continue
            seen.add((r, c))
            pending, cells = deque([(r, c)]), []
            while pending:
                rr, cc = pending.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    q = (rr + dr, cc + dc)
                    if (0 <= q[0] < len(grid) and 0 <= q[1] < len(row)
                            and q not in seen and grid[q[0]][q[1]] == color):
                        seen.add(q)
                        pending.append(q)
            result.append(sorted(cells))
    return result


def bbox(cells):
    return (min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells))


def always_change_rank_color(grid):
    """Intentional teaching negative: never keep an object's old color.

    Assign ascending area/bbox rank colors 2/4/6/8; if the assigned color equals
    the object's input color, use the next cyclic palette color instead.
    This diagnostic rival is NOT presented as an observed model failure or as
    a shortcut that fits every canonical pair.
    """
    palette = (2, 4, 6, 8)
    output = [[0 for _ in row] for row in grid]
    ordered = sorted(components(grid), key=lambda cells: (len(cells), bbox(cells)))
    for rank, cells in enumerate(ordered[:4]):
        color = palette[rank]
        r, c = cells[0]
        if grid[r][c] == color:
            color = palette[(rank + 1) % 4]
        for r, c in cells:
            output[r][c] = color
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="evidence")
    args = parser.parse_args()
    out = HERE / args.out
    if out.exists():
        raise FileExistsError(f"Use a new --out directory: {out}")
    if out.parent.resolve() != HERE:
        raise ValueError("--out must name one direct child directory")
    out.mkdir()

    module, source, source_hash = load_selected_generator(TASK, root=ROOT)
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    ledger_rows = []
    for line in canonical_path(ROOT).read_text().splitlines():
        item = json.loads(line)
        if item.get("task_id") == TASK:
            ledger_rows.append(item)
    assert len(ledger_rows) == 1
    program = ledger_rows[0]["program_solution"]
    rule_hash = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
    binding = {
        "task_id": TASK, "generator_path": str(source.relative_to(ROOT)),
        "generator_sha256": source_hash, "rule_hash": rule_hash,
        "canonical_program_text_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    records = []
    for pair in canonical:
        records.append({"kind": "canonical", **pair})
    position = {}
    for band in ("easy", "medium", "hard"):
        for sample_index in range(8):
            grid = module.generate(0, sample_index, difficulty=band)
            position[band, sample_index] = len(records)
            records.append({
                "kind": "generated", "seed": 0, "sample_index": sample_index,
                "difficulty": band, "overrides": {}, "input": grid,
                "observed": module.observe_overrides(grid),
            })

    overrides = {"grid_h": 9, "grid_w": 10, "lesson_profile": "canonical_strict"}
    base = module.generate(0, 0, difficulty="easy", **overrides)
    modified = [row[:] for row in base]
    largest = max(components(base), key=lambda cells: (len(cells), bbox(cells)))
    original_color = base[largest[0][0]][largest[0][1]]
    for r, c in largest:
        modified[r][c] = 8
    records.append({
        "kind": "hand_modified_generated_input", "input": modified,
        "seed": 0, "sample_index": 0, "difficulty": "easy", "overrides": overrides,
        "base_input": base,
        "mutation": {"description": "Recolor only the largest five-cell object to its correct rank color 8",
                     "previous_color": original_color, "new_color": 8, "cells": largest},
    })
    for record in records:
        record["self_check_errors"] = module.self_check(record["input"])
        record["strict_canonical_like_errors"] = module.strict_canonical_like(record["input"])
    write(out / "inputs.json", {"inputs": [r["input"] for r in records]})

    command = [sys.executable, "-m", "arcpuzzles", "apply", TASK,
               "--input", os.path.relpath(out / "inputs.json", ROOT),
               "--out", os.path.relpath(out / "racket.json", ROOT),
               "--check-generator-domain", "--timeout", "120"]
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=150)
    write(out / "command.json", {
        **binding, "command": command, "cwd": str(ROOT), "exit_code": run.returncode,
        "stdout": run.stdout, "stderr": run.stderr,
        "outer_replay_command": "WORK/.venv/bin/python review.py run ../.venv/bin/python ../checks/audit/8a2e39528187/probe.py --out REPLAY_DIRECTORY",
        "outer_replay_cwd": str(ROOT.parents[1]),
    })
    if run.returncode:
        print(run.stderr, file=sys.stderr)
        return run.returncode
    authority = json.loads((out / "racket.json").read_text())
    assert authority["generator_sha256"] == source_hash
    assert authority["executed_rule_hash"] == rule_hash
    assert authority["rule_hash_matches_catalog"]
    assert len(authority["results"]) == len(records)
    binding["executed_rule_text_sha256"] = authority["rule_text_sha256"]
    command_receipt = json.loads((out / "command.json").read_text())
    command_receipt["executed_rule_text_sha256"] = authority["rule_text_sha256"]
    write(out / "command.json", command_receipt)
    for record, result in zip(records, authority["results"]):
        assert not result["error"], result
        assert result["input"] == record["input"]
        record["racket_output"] = result["output"]
        record["racket_input_sha256"] = result["input_sha256"]
        record["racket_output_sha256"] = result["output_sha256"]
        record["mirror_matches_racket"] = module.rule_mirror(record["input"]) == result["output"]
        record["unchanged_nonzero_cells"] = sum(
            value != 0 and value == result["output"][r][c]
            for r, row in enumerate(record["input"]) for c, value in enumerate(row))
        input_palette = {value for row in record["input"] for value in row if value}
        record["mixed_rank_and_nonrank_input_palette"] = bool(
            input_palette & {2, 4, 6, 8} and input_palette - {2, 4, 6, 8})
        record["diagnostic_always_change_output"] = always_change_rank_color(record["input"])
        record["diagnostic_always_change_matches_racket"] = (
            record["diagnostic_always_change_output"] == result["output"])
    write(out / "records.json", {**binding, "records": records})

    competitors = dict(module.LESSON_COMPETITORS)
    shortcuts = dict(module.CANONICAL_SHORTCUTS)
    lessons = []
    minimal = None
    for band in ("easy", "medium", "hard"):
        for start in range(4):
            pool = [records[position[band, i]] for i in range(start, start + 5)]
            rotations = []
            for query_offset in range(5):
                train = [r for i, r in enumerate(pool) if i != query_offset]
                query = pool[query_offset]
                pairify = lambda r: {"input": r["input"], "output": r["racket_output"]}
                survivors = [name for name, rival in competitors.items()
                             if all(rival(r["input"]) == r["racket_output"] for r in train)]
                unresolved = [name for name in survivors
                              if competitors[name](query["input"]) != query["racket_output"]]
                rotations.append({
                    "query_sample_index": start + query_offset,
                    "demo_sample_indices": [r["sample_index"] for r in train],
                    "production_order": query_offset == 4,
                    "surviving_declared_rivals": survivors,
                    "surviving_rivals_disagreeing_on_query": unresolved,
                    "lesson_hook_errors": module.lesson_identifiable(
                        [pairify(r) for r in train], pairify(query)),
                })
                if minimal is None and unresolved:
                    name = unresolved[0]
                    rival = competitors[name]
                    minimal = {
                        **binding, "finding_id": "A8A2-R1", "type": "reproduced_query_rotation_teaching_ambiguity",
                        "seed": 0, "difficulty": band, "overrides": {}, "pool_start_sample_index": start,
                        "demonstrations": [{**r, "rival_output": rival(r["input"])} for r in train],
                        "query": {**query, "rival_output": rival(query["input"])},
                        "rival_name": name, "all_four_demo_outputs_match_rival": True,
                        "query_rival_differs_from_racket": True,
                        "command_evidence": "command.json", "racket_evidence": "racket.json",
                        "scope": "Smallest complete witness found in this stated seed/window census; no claim of globally minimal episode",
                    }
            lessons.append({"seed": 0, "difficulty": band, "pool_start_sample_index": start,
                            "pool_sample_indices": list(range(start, start + 5)), "rotations": rotations})
    flat = [r for lesson in lessons for r in lesson["rotations"]]
    production = [r for r in flat if r["production_order"]]
    canonical_records = [r for r in records if r["kind"] == "canonical"]
    generated_records = [r for r in records if r["kind"] == "generated"]
    summary = {
        **binding, "schema": "8a2e39528187-focused-audit-v1",
        "verification": {
            "racket_command_exit_code": run.returncode, "racket_inputs": len(records),
            "racket_errors": sum(bool(r["error"]) for r in authority["results"]),
            "all_input_self_check_failures": sum(bool(r["self_check_errors"]) for r in records),
            "all_input_strict_canonical_like_failures": sum(bool(r["strict_canonical_like_errors"]) for r in records),
            "generator_mirror_mismatches": sum(not r["mirror_matches_racket"] for r in records),
            "canonical_label_count": len(canonical_records),
            "canonical_label_mismatches": sum(r["output"] != r["racket_output"] for r in canonical_records),
        },
        "sampling": {"seed": 0, "bands": ["easy", "medium", "hard"], "sample_indices": list(range(8)),
                     "generated_rows": len(generated_records),
                     "unique_generated_inputs": len({digest(r["input"]) for r in generated_records}),
                     "consecutive_window_starts": [0, 1, 2, 3],
                     "overlap": "Four overlapping five-row pools per band; 12 pools total. All five query positions in each pool, always four demos.",
                     "profiles": dict(Counter(r["observed"]["lesson_profile"] for r in generated_records))},
        "declared_competitors": list(competitors),
        "canonical_fit": {name: {"matches": sum(rival(r["input"]) == r["racket_output"] for r in canonical_records),
                                  "denominator": len(canonical_records)} for name, rival in competitors.items()},
        "declared_canonical_shortcuts": list(shortcuts),
        "canonical_shortcut_fit": {name: {"matches": sum(rival(r["input"]) == r["racket_output"] for r in canonical_records),
                                           "denominator": len(canonical_records)} for name, rival in shortcuts.items()},
        "ordered_production": {"verdict": "pass" if not any(r["lesson_hook_errors"] for r in production) else "fail",
                               "lessons": len(production),
                               "lessons_with_surviving_rival": sum(bool(r["surviving_declared_rivals"]) for r in production),
                               "lessons_with_query_ambiguity": sum(bool(r["surviving_rivals_disagreeing_on_query"]) for r in production)},
        "query_rotation": {"verdict": "fail" if any(r["surviving_rivals_disagreeing_on_query"] for r in flat) else "pass",
                           "lesson_rotations": len(flat),
                           "rotations_with_surviving_rival": sum(bool(r["surviving_declared_rivals"]) for r in flat),
                           "rotations_with_query_ambiguity": sum(bool(r["surviving_rivals_disagreeing_on_query"]) for r in flat),
                           "ambiguous_rotations_by_rival": dict(Counter(name for r in flat for name in r["surviving_rivals_disagreeing_on_query"]))},
        "palette_coverage": {
            "canonical_pairs_with_unchanged_nonzero_cells": sum(bool(r["unchanged_nonzero_cells"]) for r in canonical_records),
            "canonical_denominator": len(canonical_records),
            "generated_pairs_with_unchanged_nonzero_cells": sum(bool(r["unchanged_nonzero_cells"]) for r in generated_records),
            "generated_denominator": len(generated_records),
            "canonical_mixed_palettes": sum(r["mixed_rank_and_nonrank_input_palette"] for r in canonical_records),
            "generated_mixed_palettes": sum(r["mixed_rank_and_nonrank_input_palette"] for r in generated_records),
            "diagnostic_rival": "always_change_rank_color (intentional teaching negative)",
            "diagnostic_rival_canonical_matches": sum(r["diagnostic_always_change_matches_racket"] for r in canonical_records),
            "diagnostic_rival_generated_matches": sum(r["diagnostic_always_change_matches_racket"] for r in generated_records),
            "source_palette_branches": {
                "non_rank_colors": list(module._NON_RANK_COLORS),
                "rank_derangements": list(module._RANK_DERANGEMENTS),
                "all_declared_derangements_have_zero_fixed_points": all(
                    all(a != b for a, b in zip(colors, (2, 4, 6, 8))) for colors in module._RANK_DERANGEMENTS)},
        },
        "lessons": lessons,
        "limitations": [
            "One deterministic seed across all three difficulty streams, not a broad safety review.",
            "Rotations reuse the same 24 unique generated inputs; 60 rotated lessons are not 300 independent examples.",
            "No source repair was attempted; ordered four-demo production passes the declared finite rival checks.",
            "The palette diagnostic is an intentionally constructed negative and does not fit every canonical pair.",
        ],
    }
    write(out / "summary.json", summary)
    if minimal:
        write(out / "counterexample_rotation.json", minimal)
    fixed = records[-1]
    write(out / "counterexample_palette.json", {
        **binding, "finding_id": "A8A2-C1", "type": "canonical_palette_coverage_gap", **fixed,
        "rival_name": "always_change_rank_color", "rival_intent": "intentional teaching negative",
        "validator_accepted": not fixed["self_check_errors"],
        "documented_domain": "9x10 minimum advertised canvas; 4 distinct monochromatic objects of areas 2/3/4/5; 0 background",
        "smallest_claim": "Minimum documented grid dimensions and minimum strict area profile; only five cells are recolored from the generated base",
        "canonical_unchanged_color_witnesses": [{"variant": r["variant"], "split": r["split"],
                                                "pair_index": r["pair_index"], "unchanged_nonzero_cells": r["unchanged_nonzero_cells"]}
                                               for r in canonical_records if r["unchanged_nonzero_cells"]],
        "command_evidence": "command.json", "racket_evidence": "racket.json",
    })
    print(json.dumps({k: summary[k] for k in ("task_id", "generator_sha256", "rule_hash", "verification", "sampling", "ordered_production", "query_rotation", "palette_coverage")}, indent=2))
    return int(any((summary["verification"]["canonical_label_mismatches"],
                    summary["verification"]["racket_errors"],
                    summary["verification"]["all_input_self_check_failures"],
                    summary["verification"]["generator_mirror_mismatches"])))


if __name__ == "__main__":
    raise SystemExit(main())
