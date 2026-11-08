#!/usr/bin/env python3
"""Reproduce the selected generator's too-large-stamp admission defect.

Run from WORK:
  .venv/bin/python3 run_with_racket.py "$PWD/.venv/bin/python3" \
    ../checks/audit/a8d6e6039a6f/probe.py

This findings-only audit never edits the selected generator, rule or status.
Its comparison preserves gray frame borders by clipping a transformed stamp
to the interior; it is explicitly a rival, not a replacement canonical rule.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from arcpuzzles import Catalog


TASK_ID = "a8d6e6039a6f"
EXPECTED_GENERATOR_SHA256 = "d6a36459af5a75c32e37820d5e631fb078369d69ba2ff384edbd539811890fdd"
EXPECTED_RULE_HASH = "9921e422d6f8"
EXPECTED_CANONICAL_RULE_SHA256 = "250788bac4cbc9a82e250c8766948ad99609c2c2afcc8e9062d0f7181c4886c0"
EXPECTED_RULE_TEXT_SHA256 = "8f7ad27f3ec05b381b8d1f929308c00166b54d99eb566dc902c502b73159d67c"
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def json_digest(value):
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, separators=(",", ":"), ensure_ascii=False) + "\n")


def transform(pattern, key):
    """Independent primitive implementation used only for the rival."""
    if key == 2:
        return [list(row) for row in zip(*pattern[::-1])]
    if key == 3:
        return [list(reversed(row)) for row in pattern]
    if key == 4:
        return [list(row) for row in reversed(pattern)]
    return [list(row) for row in pattern]


def gray_frames(grid):
    """Recover gray rectangular borders from input cells, without generator helpers."""
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5}
    frames = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        todo, component = [start], {start}
        while todo:
            r, c = todo.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    todo.append(neighbor)
        top = min(r for r, _ in component)
        bottom = max(r for r, _ in component)
        left = min(c for _, c in component)
        right = max(c for _, c in component)
        border = {(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)
                  if r in (top, bottom) or c in (left, right)}
        assert component == border, "audit input has a nonrectangular gray component"
        frames.append((top, bottom, left, right))
    return sorted(frames)


def key_at_frame(grid, frame):
    t, b, l, r = frame
    spots = ((t - 1, l), (t - 1, r), (b + 1, l), (b + 1, r),
             (t, l - 1), (t, r + 1), (b, l - 1), (b, r + 1))
    keys = [grid[rr][cc] for rr, cc in spots
            if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]) and 1 <= grid[rr][cc] <= 4]
    assert len(keys) == 1
    return keys[0]


def template_crop(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value >= 6]
    t, b = min(r for r, _ in cells), max(r for r, _ in cells)
    l, r = min(c for _, c in cells), max(c for _, c in cells)
    return [row[l:r + 1] for row in grid[t:b + 1]], (t, b, l, r)


def border_preserving_rival(grid):
    """Keep borders and clip only the overflowing stamp cells to each interior."""
    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    template, _ = template_crop(grid)
    fit_details = []
    for frame in gray_frames(grid):
        t, b, l, r = frame
        key = key_at_frame(grid, frame)
        pattern = transform(template, key)
        h, w = b - t - 1, r - l - 1
        ph, pw = len(pattern), len(pattern[0])
        paste_t = t + 1 + max(0, (h - ph) // 2)
        paste_l = l + 1 + max(0, (w - pw) // 2)
        omitted = []
        for rr, row in enumerate(pattern):
            for cc, value in enumerate(row):
                if value:
                    target = (paste_t + rr, paste_l + cc)
                    if t < target[0] < b and l < target[1] < r:
                        out[target[0]][target[1]] = value
                    else:
                        omitted.append({"cell": target, "value": value})
        fit_details.append({"frame": frame, "key": key, "interior_shape": [h, w],
                            "transformed_shape": [ph, pw], "fits": ph <= h and pw <= w,
                            "overflowing_colored_cells": omitted})
    return out, fit_details


def changes(before, after, predicate=lambda value: True):
    return [{"cell": [r, c], "before": value, "after": after[r][c]}
            for r, row in enumerate(before) for c, value in enumerate(row)
            if predicate(value) and value != after[r][c]]


def layout_pattern_census(gen):
    """Enumerate table dimensions and key orders; do not claim a full runtime sweep."""
    total, infeasible, profile_count = 0, 0, 0
    per_layout = []
    for li, (_, _, frames, _) in enumerate(gen.LAYOUTS):
        local_bad, local_total = 0, 0
        multiplicity = len(gen.LAYOUT_SPOTS[li]) * gen.PALETTE_COUNT * gen.PLACEMENT_COUNT
        for pattern in gen.PATTERNS[:gen.LAYOUT_PATTERN_COUNTS[li]]:
            ph, pw = len(pattern), len(pattern[0])
            for keys in gen.KEY_ORDERS[len(frames)]:
                profile_count += 1
                fits = True
                for (t, b, l, r), key in zip(frames, keys):
                    h, w = (pw, ph) if key == 2 else (ph, pw)
                    if h > b - t - 1 or w > r - l - 1:
                        fits = False
                local_total += multiplicity
                if not fits:
                    local_bad += multiplicity
        total += local_total
        infeasible += local_bad
        per_layout.append({"layout_index": li,
                           "frame_interiors": [[b - t - 1, r - l - 1] for t, b, l, r in frames],
                           "declared_scene_codes": local_total,
                           "dimensionally_infeasible_scene_codes": local_bad})
    assert total == gen.SCENE_COUNT
    return {"method": "Exhaustive declared layout/pattern/key-order dimensions, weighted by key spots, palettes and placements. No per-scene generation or Racket execution in this census.",
            "layout_pattern_key_profiles_checked": profile_count,
            "declared_scene_codes": total,
            "dimensionally_infeasible_scene_codes": infeasible,
            "infeasible_fraction_of_declared_codes": infeasible / total,
            "layouts_allowing_oversize_templates": sum(row["dimensionally_infeasible_scene_codes"] > 0 for row in per_layout),
            "template_shape_counts": {f"{h}x{w}": count for (h, w), count in sorted(Counter((len(p), len(p[0])) for p in gen.PATTERNS).items())},
            "per_layout": per_layout}


def main():
    started = time.monotonic()
    source_path = REPO / "generators" / TASK_ID / "generator.py"
    source_hash = digest_bytes(source_path.read_bytes())
    assert source_hash == EXPECTED_GENERATOR_SHA256, "selected generator bytes changed; this witness is source-bound"
    spec = importlib.util.spec_from_file_location("audited_a8d6e6039a6f", source_path)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    canonical_file = REPO / "shared/data/canonical/puzzles.jsonl"
    with canonical_file.open() as handle:
        records = [json.loads(line) for line in handle if f'"{TASK_ID}"' in line]
    records = [row for row in records if row.get("task_id") == TASK_ID]
    assert len(records) == 1
    canonical = records[0]
    rule = canonical["program_solution"]
    rule_hash = digest_bytes(" ".join(rule.split()).encode())[:12]
    assert rule_hash == EXPECTED_RULE_HASH
    # The public receipt hashes the executable wrapper, which differs from
    # the canonical rule! source text. Bind both representations separately.
    assert digest_bytes(rule.encode()) == EXPECTED_CANONICAL_RULE_SHA256

    grid = gen.generate(14, 0, difficulty=None)
    analysis = gen._analysis(grid)
    assert analysis["scene_code"] == 172945
    forced = gen.generate(0, 0, difficulty=None, scene_code=172945)
    assert forced == grid
    errors = gen.self_check(grid)
    assert errors == []
    assert gen.observe_overrides(grid) == {"scene_code": 172945}
    preserved_input = deepcopy(grid)
    rival, fit_details = border_preserving_rival(grid)
    assert all(not frame["fits"] for frame in fit_details)
    assert len(rival) == len(grid) and len(rival[0]) == len(grid[0])

    # A larger declared layout gives the same template enough room.
    control_code = gen._encode_scene(13, 0, 0, 19, 0, 0)
    control_grid = gen.generate(0, 0, scene_code=control_code)
    control_rival, control_fit = border_preserving_rival(control_grid)
    assert all(frame["fits"] for frame in control_fit)
    assert gen.self_check(control_grid) == []
    canonical_pairs = canonical["train"] + canonical["test"]
    inputs = [grid, control_grid] + [pair["input"] for pair in canonical_pairs]
    receipt = Catalog(REPO).apply(TASK_ID, inputs, reference="canonical", allow_unapproved=True,
                                  check_generator_domain=True, timeout=90)
    assert receipt["generator_sha256"] == source_hash
    assert receipt["executed_rule_hash"] == rule_hash
    assert receipt["rule_text_sha256"] == EXPECTED_RULE_TEXT_SHA256
    assert receipt["rule_hash_matches_catalog"] is True
    for result in receipt["results"]:
        assert result["error"] is None and result["valid_output"] is True
        assert result["generator_domain"] == {"status": "valid", "errors": []}
    output = receipt["results"][0]["output"]
    border_changes = changes(grid, output, lambda value: value == 5)
    assert border_changes == [
        {"cell": [2, 12], "before": 5, "after": 6},
        {"cell": [4, 18], "before": 5, "after": 6},
        {"cell": [10, 12], "before": 5, "after": 6},
        {"cell": [11, 12], "before": 5, "after": 6},
    ]
    assert output == gen.rule_mirror(grid), "this finding does not rely on a mirror/Racket disagreement"
    assert output != rival
    assert not changes(grid, rival, lambda value: value == 5)
    assert grid == preserved_input
    control_output = receipt["results"][1]["output"]
    assert control_output == control_rival
    assert not changes(control_grid, control_output, lambda value: value == 5)
    for pair, result in zip(canonical_pairs, receipt["results"][2:]):
        assert result["output"] == pair["output"]
        assert not changes(pair["input"], result["output"], lambda value: value == 5)

    census = layout_pattern_census(gen)
    witness = {
        "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "rule_hash": rule_hash,
        "canonical_rule_text_sha256": EXPECTED_CANONICAL_RULE_SHA256,
        "rule_text_sha256": EXPECTED_RULE_TEXT_SHA256,
        "generation": {"seed": 14, "sample_index": 0, "difficulty": None, "overrides": {}},
        "exact_override_replay": {"seed": 0, "sample_index": 0, "difficulty": None,
                                  "overrides": {"scene_code": 172945}, "same_input": True},
        "observed_overrides": gen.observe_overrides(grid),
        "self_check_errors": errors,
        "public_generator_domain": receipt["results"][0]["generator_domain"],
        "input": grid,
        "racket_output": output,
        "rival_output": rival,
        "rival_definition": "Apply the same key transform and placement, clipping colored cells to each frame interior so every gray border survives. This diagnostic rival is not asserted to be a valid canonical answer for an impossible full-fit input.",
        "input_sha256": receipt["results"][0]["input_sha256"],
        "racket_output_sha256": receipt["results"][0]["output_sha256"],
        "rival_output_canonical_json_sha256": json_digest(rival),
        "facts": analysis["facts"],
        "template_crop": template_crop(grid)[0],
        "frame_fit": fit_details,
        "gray_border_changes": border_changes,
        "racket_vs_rival_differences": changes(rival, output),
        "python_mirror_matches_racket": True,
    }
    write_json("witness.json", witness)
    write_json("racket_apply.json", receipt)
    write_json("table_census.json", census)
    evidence = {
        "schema": "arcpuzzles-focused-audit-v1",
        "task_id": TASK_ID,
        "finding_id": "oversized_template_accepted_and_overwrites_gray_border",
        "result": "issue_reproduced",
        "finding_kind": "generator_semantic_domain_and_validator_false_negative",
        "severity": "high",
        "generator_path": f"generators/{TASK_ID}/generator.py",
        "generator_sha256": source_hash,
        "generator_version": gen.VERSION,
        "rule_hash": rule_hash,
        "canonical_rule_text_sha256": EXPECTED_CANONICAL_RULE_SHA256,
        "rule_text_sha256": EXPECTED_RULE_TEXT_SHA256,
        "canonical_record_sha256": json_digest(canonical),
        "canonical_file_sha256": digest_bytes(canonical_file.read_bytes()),
        "selected_catalog_approved_at_run": receipt["catalog_approved"],
        "review_index_present": (source_path.parent / "evidence/review_index.json").is_file(),
        "witness_seed": 14, "witness_sample_index": 0, "witness_difficulty": None,
        "witness_overrides": {}, "witness_scene_code": 172945,
        "self_check_passes": True,
        "public_domain_check_passes": True,
        "actual_gray_border_cells_overwritten": len(border_changes),
        "actual_racket_inputs_checked": len(inputs),
        "canonical_pairs_checked": len(canonical_pairs),
        "canonical_outputs_match": True,
        "larger_frame_control": {"generation": {"seed": 0, "sample_index": 0,
                                                  "difficulty": None, "overrides": {"scene_code": control_code}},
                                 "layout_index": 13, "pattern_index": 19,
                                 "all_stamps_fit": True, "rival_matches_racket": True,
                                 "gray_borders_preserved": True},
        "census": {key: value for key, value in census.items() if key != "per_layout"},
        "scope_limits": [
            "Six actual Racket inputs were checked: one natural defect witness, one fitting generalized control, and all four canonical pairs.",
            "The table census checks exact dimension/key compatibility; it does not execute all declared scenes or establish their full validity.",
            "No selected source, rule, catalog, shared code, approval or audit-status record was edited.",
            "No full battery or exhaustive natural-seed sweep was run.",
        ],
        "assets": ["probe.py", "witness.json", "racket_apply.json", "table_census.json", "audit_notes.md", "commands.json"],
    }
    assert len(inputs) == 6
    write_json("evidence.json", evidence)
    commands = {
        "schema": "arcpuzzles-audit-commands-v1",
        "prior_probe_attempts": [{
            "probe_sha256": "75acc1523ff663da00bd5da44990979e80d93840b026c4fa07421f14b22c9849",
            "same_command_as_successful_run": True,
            "exit_code": 1,
            "error": "Audit probe initially compared raw canonical rule text to the public receipt's executable-wrapper hash. The guard failed before Racket execution; the final probe binds the two representations separately.",
        }],
        "commands": [{
            "purpose": "Reproduce the exact-source natural witness, Racket outputs, fitting and canonical controls, and declared-table census.",
            "cwd": str(WORK),
            "argv": [str(WORK / ".venv/bin/python3"), "run_with_racket.py", str(WORK / ".venv/bin/python3"), f"../checks/audit/{TASK_ID}/probe.py"],
            "portable_shell_command": f'.venv/bin/python3 run_with_racket.py "$PWD/.venv/bin/python3" ../checks/audit/{TASK_ID}/probe.py',
            "payload_cwd": str(REPO),
            "exit_code": 0,
            "result": "issue_reproduced",
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "python_version": sys.version.split()[0],
            "outputs": [f"checks/audit/{TASK_ID}/{name}" for name in ("witness.json", "racket_apply.json", "table_census.json", "evidence.json", "commands.json")],
        }],
    }
    write_json("commands.json", commands)
    print(json.dumps({"task_id": TASK_ID, "result": "issue_reproduced",
                      "self_check_passes": True, "public_domain_check_passes": True,
                      "gray_border_cells_overwritten": len(border_changes),
                      "actual_racket_inputs_checked": len(inputs),
                      "declared_scene_codes": census["declared_scene_codes"],
                      "dimensionally_infeasible_scene_codes": census["dimensionally_infeasible_scene_codes"],
                      "generator_sha256": source_hash, "rule_hash": rule_hash}))


if __name__ == "__main__":
    main()
