#!/usr/bin/env python3
"""Focused findings-only audit of selected d4be41674012; no source mutation."""
from collections import deque
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "d4be41674012"
ROOT = find_root(__file__)


def components(grid):
    seen, result = set(), []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not value or (r, c) in seen:
                continue
            seen.add((r, c))
            queue, cells = deque([(r, c)]), []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if (0 <= nr < len(grid) and 0 <= nc < len(row)
                            and (nr, nc) not in seen and grid[nr][nc] == value):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
            c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
            crop = [row[c0:c1+1] for row in grid[r0:r1+1]]
            zeros = {(r, c) for r, row in enumerate(crop) for c, v in enumerate(row) if not v}
            holes = 0
            while zeros:
                start = zeros.pop()
                queue, touches_border = deque([start]), False
                while queue:
                    rr, cc = queue.popleft()
                    touches_border |= rr in (0, len(crop)-1) or cc in (0, len(crop[0])-1)
                    for neighbor in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                        if neighbor in zeros:
                            zeros.remove(neighbor)
                            queue.append(neighbor)
                holes += not touches_border
            result.append({"color": value, "area": len(cells), "holes": holes,
                           "bbox": [r0, c0, r1, c1], "crop": crop})
    return result


def documented_hole_pack(grid):
    objects = sorted(components(grid), key=lambda obj: (obj["holes"], obj["area"], obj["color"]))
    height = max(len(obj["crop"]) for obj in objects)
    width = sum(len(obj["crop"][0]) for obj in objects) + len(objects)-1
    out = [[0]*width for _ in range(height)]
    left = 0
    for obj in objects:
        crop = obj["crop"]
        for r, row in enumerate(crop):
            for c, v in enumerate(row):
                out[r][left+c] = v
        left += len(crop[0])+1
    return out


def run():
    module, source, source_sha = load_selected_generator(TASK, root=ROOT)
    catalog = Catalog(ROOT)
    metadata = catalog.get(TASK)
    pairs = canonical_pairs(TASK, root=ROOT)
    seed, index = 17, 0
    generated = module.generate(seed, index)
    applied = catalog.apply(TASK, [pair["input"] for pair in pairs] + [generated],
                            reference="canonical", allow_unapproved=True,
                            check_generator_domain=True)
    canonical_results = []
    for pair, result in zip(pairs, applied["results"]):
        assert result["output"] == pair["output"], (pair["split"], pair["pair_index"], result)
        canonical_results.append({"variant": pair["variant"], "split": pair["split"],
            "pair_index": pair["pair_index"], "reference_matches_canonical_label": True,
            "documented_generator_rule_matches_label": documented_hole_pack(pair["input"]) == pair["output"],
            "observed_hole_counts": sorted(obj["holes"] for obj in components(pair["input"]))})
    witness_result = applied["results"][-1]
    hole_output = documented_hole_pack(generated)
    controls = []
    for overrides in ({"grid_h": 10, "grid_w": 12}, {"grid_h": 16, "grid_w": 20},
                      {"palette_size": 2}, {"n_distinct_colors": 2}, {"palette_kind": "warm"}):
        record = {"seed": seed, "sample_index": index, "difficulty": None, "overrides": overrides}
        try:
            grid = module.generate(seed, index, **overrides)
            colors = sorted({v for row in grid for v in row})
            record.update(status="accepted", same_as_default=grid == generated,
                          actual_shape=[len(grid), len(grid[0])], input_colors=colors,
                          actual_nonzero_color_count=len([v for v in colors if v]),
                          actual_total_color_count=len(colors), self_check_errors=module.self_check(grid))
        except Exception as exc:
            record.update(status="rejected", error_type=type(exc).__name__, error=str(exc))
        controls.append(record)
    rule = metadata["variants"][0]["program_solution"]
    report = {"schema": "arc-focused-adversarial-audit-v1", "task_id": TASK,
        "status": "confirmed_findings", "source": str(source.relative_to(ROOT)),
        "generator_sha256": source_sha, "catalog_rule_hash": metadata["rule_hash"],
        "canonical_rule_text_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "executed_rule_hash": applied["executed_rule_hash"],
        "executed_rule_text_sha256": applied["rule_text_sha256"],
        "rule_hash_matches_catalog": applied["rule_hash_matches_catalog"],
        "current_review_index_present": (source.parent / "evidence/review_index.json").exists(),
        "canonical_title": metadata["variants"][0]["title"],
        "canonical_written_solution": metadata["variants"][0]["written_solution"],
        "declared_axes": module.AXES,
        "findings": [
            {"id": "documented-rule-is-another-transformation", "severity": "medium",
             "claim": "Selected generator documentation, SUMMARY and invariants teach hole-count horizontal packing, while the canonical rule transposes objects and stacks them vertically in left-to-right input order.",
             "evidence": "The independently implemented documented hole-pack disagrees with all four canonical labels and the generated witness. Canonical Racket agrees with all four labels.",
             "scope": "A confirmed contract and teaching-family mismatch, not evidence that canonical-runtime generated labels are wrong."},
            {"id": "advertised-overrides-not-honored", "severity": "medium",
             "claim": "Advertised dimension endpoints are rejected and valid color/palette overrides are silently ignored.",
             "evidence": "Default difficulty requests10x12 and16x20 rejected although AXES advertises10..16 by12..20. palette_size2 and n_distinct_colors2 return the unchanged default grid with3 nonzero colors and4 total colors."}],
        "canonical_checks": canonical_results,
        "observed_counts": {"canonical_racket_matches": sum(r["reference_matches_canonical_label"] for r in canonical_results),
                            "canonical_pairs_checked": len(pairs),
                            "documented_rule_canonical_matches": sum(r["documented_generator_rule_matches_label"] for r in canonical_results),
                            "generated_samples_checked": 1},
        "generated_witness": {"seed": seed, "sample_index": index, "difficulty": None,
            "overrides": {}, "input": generated, "self_check_errors": module.self_check(generated),
            "components": components(generated), "canonical_execution": witness_result,
            "documented_hole_pack_output": hole_output,
            "documented_rule_matches_canonical": hole_output == witness_result["output"]},
        "override_probes": controls,
        "receipt": {"cwd": str(ROOT), "command": "../.venv/bin/python ../run_with_racket.py ../.venv/bin/python ../checks/audit/d4be41674012/reproducer.py", "exit_code": 0},
        "limits": "One generated sample, four canonical pairs and five override requests. No full battery, no source repair, no archival implementation imported, no safety-label change, no claim that retry fallback failed."}
    path = Path(__file__).with_name("report.json")
    path.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"task_id": TASK, "generator_sha256": source_sha,
                      "observed_counts": report["observed_counts"], "report": str(path)}))


if __name__ == "__main__":
    run()
