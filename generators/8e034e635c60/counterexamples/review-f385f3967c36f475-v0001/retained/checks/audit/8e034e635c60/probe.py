"""Findings-only audit; no generator or rule writes.

Run from WORK with:
  python3 run_with_racket.py python3 ../checks/audit/8e034e635c60/probe.py prepare
  python3 run_with_racket.py python3 -m arcpuzzles apply 8e034e635c60 --input ../checks/audit/8e034e635c60/input.json --out ../checks/audit/8e034e635c60/racket.json
  python3 run_with_racket.py python3 ../checks/audit/8e034e635c60/probe.py analyze
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "8e034e635c60"
OUT = Path(__file__).resolve().parent
ROOT = find_root(Path.cwd() / "generators" / TASK / "generator.py")
SOURCE = ROOT / "generators" / TASK / "generator.py"
AUTHORITY = ROOT / "shared/data/base/solutions/banks/e00836ab832d/E130__8e034e635c60.json"
SPEC = importlib.util.spec_from_file_location("audited_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            cells = {(r, c)}
            pending = [(r, c)]
            seen.add((r, c))
            while pending:
                rr, cc = pending.pop()
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        pending.append((nr, nc))
            result.append((color, cells))
    return result


def all_color_l_rival(grid):
    """Intentional audit rival: complete every monochrome L, ignoring color 2."""
    out = [row[:] for row in grid]
    for _, cells in components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        if len(cells) == 3 and r1 - r0 == 1 and c1 - c0 == 1:
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if (r, c) not in cells:
                        out[r][c] = 3
    return out


def grid_meta(grid):
    return {"input_sha256_json_compact": digest(grid),
            "height": len(grid), "width": len(grid[0]),
            "colors": sorted({c for row in grid for c in row}),
            "self_check": GEN.self_check(grid),
            "red_component_sizes": [len(cells) for color, cells in components(grid) if color == 2]}


def prepare():
    authority = json.loads(AUTHORITY.read_text())
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    report = {"task_id": TASK, "phase": "audit_unchanged_source",
              "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "authority_file_sha256": hashlib.sha256(AUTHORITY.read_bytes()).hexdigest(),
              "rule_sha256_unmodified_target_code_utf8": hashlib.sha256(
                  authority["racket_target"]["target_code"].encode()).hexdigest(),
              "generator_version": GEN.VERSION,
              "generator_path": str(SOURCE.relative_to(ROOT)),
              "canonical_path": str(canonical_path(ROOT).relative_to(ROOT)),
              "declared_competitors": {name: list(getattr(GEN, name, ()))
                                       for name in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")},
              "axis_declarations": GEN.AXES,
              "palette_texture_checks": [], "rejected_declared_valid_controls": [],
              "racket_case_index": []}
    cases = []

    def add_case(grid, name, **metadata):
        index = len(cases)
        cases.append(grid)
        report["racket_case_index"].append({"index": index, "name": name,
                                            **metadata, **grid_meta(grid)})

    for seed in range(3):
        baseline = GEN.generate(seed, 0)
        for axis, values in (("palette_kind", GEN.PALETTE_KINDS), ("texture", GEN.HELPFUL_TEXTURES)):
            for value in values:
                grid = GEN.generate(seed, 0, **{axis: value})
                report["palette_texture_checks"].append(
                    {"seed": seed, "sample_index": 0, "difficulty": None,
                     "overrides": {axis: value}, "equals_unoverridden": grid == baseline,
                     "input_sha256_json_compact": digest(grid), "self_check": GEN.self_check(grid)})
        add_case(baseline, f"ordinary_seed_{seed}", seed=seed, sample_index=0,
                 difficulty=None, overrides={}, documented_generator_domain=True)

    for axis, values in (("grid_h", (4, 18)), ("grid_w", (4, 18)), ("n_l_shapes", (1, 10))):
        for value in values:
            try:
                GEN.generate(0, 0, **{axis: value})
                outcome = {"raised": False}
            except Exception as exc:
                outcome = {"raised": True, "exception_type": type(exc).__name__, "message": str(exc)}
            report["rejected_declared_valid_controls"].append(
                {"seed": 0, "sample_index": 0, "difficulty": None,
                 "overrides": {axis: value}, "declared_valid": True, **outcome})

    count_overrides = {"grid_h": 7, "grid_w": 7, "n_l_shapes": 5}
    count_grid = GEN.generate(0, 0, **count_overrides)
    add_case(count_grid, "requested_five_Ls_in_7x7", seed=0, sample_index=0,
             difficulty=None, overrides=count_overrides, documented_generator_domain=True,
             requested_L_count=5, observed_L_count=sum(color == 2 for color, _ in components(count_grid)))

    for texture in GEN.DEGENERATE_TEXTURES:
        grid = GEN.generate(0, 0, texture=texture)
        add_case(grid, f"declared_degenerate_{texture}", seed=0, sample_index=0,
                 difficulty=None, overrides={"texture": texture}, documented_generator_domain=True,
                 self_check_with_texture_meta=GEN.self_check(grid, meta={"texture": texture}))

    for pair in canonical:
        add_case(pair["input"], f"canonical_v{pair['variant']}_{pair['split']}_{pair['pair_index']}",
                 canonical_identity={key: pair[key] for key in ("variant", "split", "pair_index")},
                 canonical_output=pair["output"],
                 rival_matches_canonical=all_color_l_rival(pair["input"]) == pair["output"],
                 documented_generator_domain=False,
                 domain_note="Canonical pairs contain distractors excluded by this generator's all-red output support.")

    witness = [[0] * 7 for _ in range(7)]
    for color, r, c in ((2, 0, 0), (1, 4, 4)):
        for dr, dc in ((0, 0), (1, 0), (1, 1)):
            witness[r + dr][c + dc] = color
    add_case(witness, "nonred_L_selectivity_counterfactual", seed=None, sample_index=None,
             difficulty=None, overrides=None, manually_constructed=True,
             documented_generator_domain=False,
             domain_note="Legal rectangular ARC grid with isolated exact red and blue Ls; passes self_check, but the extra blue L is outside the documented all-red generator domain. This is a coverage/domain witness, not a generated-label mismatch.")
    report["palette_texture_check_count"] = len(report["palette_texture_checks"])
    report["palette_texture_unique_input_count"] = len({x["input_sha256_json_compact"] for x in report["palette_texture_checks"]})
    report["canonical_usable_pair_count"] = len(canonical)
    report["racket_input_count"] = len(cases)
    write("input.json", cases)
    write("prepared.json", report)
    print(json.dumps({key: report[key] for key in ("generator_sha256", "rule_sha256_unmodified_target_code_utf8", "palette_texture_check_count", "palette_texture_unique_input_count", "canonical_usable_pair_count", "racket_input_count")}))


def analyze():
    report = json.loads((OUT / "prepared.json").read_text())
    racket = json.loads((OUT / "racket.json").read_text())
    # This script deliberately requires the documented public apply receipt.
    assert racket["generator_sha256"] == report["generator_sha256"]
    assert racket["rule_hash_matches_catalog"] is True
    assert all(row["valid_output"] and row["error"] is None for row in racket["results"])
    outputs = [row["output"] for row in racket["results"]]
    if len(outputs) != report["racket_input_count"]:
        raise AssertionError("Racket apply output count differs from prepared cases")
    cases = json.loads((OUT / "input.json").read_text())
    evidence = []
    for spec, inp, actual in zip(report["racket_case_index"], cases, outputs):
        rival = all_color_l_rival(inp)
        item = {**spec, "input_grid": inp, "actual_racket_output": actual,
                "rival_output": rival, "rival_matches_racket": rival == actual,
                "racket_added_green_count": sum(old != new and new == 3
                                               for oldrow, newrow in zip(inp, actual)
                                               for old, new in zip(oldrow, newrow))}
        if "canonical_output" in spec:
            item["racket_matches_canonical"] = actual == spec["canonical_output"]
        evidence.append(item)
    report["racket_case_results"] = evidence
    report["selected_canonical_rule_sha256"] = racket["rule_text_sha256"]
    report["racket_receipt_source_identity"] = {k: v for k, v in racket.items()
                                                 if k != "results"}
    write("evidence.json", report)
    count = next(x for x in evidence if x["name"] == "requested_five_Ls_in_7x7")
    witness = next(x for x in evidence if x["name"] == "nonred_L_selectivity_counterfactual")
    assert count["observed_L_count"] < count["requested_L_count"]
    assert all(x["equals_unoverridden"] for x in report["palette_texture_checks"])
    assert all(x["raised"] for x in report["rejected_declared_valid_controls"])
    assert all(x["rival_matches_racket"] for x in evidence if x is not witness)
    assert not witness["rival_matches_racket"]
    assert all(x["racket_matches_canonical"] for x in evidence if "canonical_output" in x)
    print(json.dumps({"assertions": "passed", "requested_L_count": 5,
                      "observed_L_count": count["observed_L_count"],
                      "racket_added_green_count": count["racket_added_green_count"],
                      "rival_canonical_fit": sum(x["rival_matches_racket"] for x in evidence if "canonical_output" in x),
                      "canonical_usable_pairs": report["canonical_usable_pair_count"],
                      "counterfactual_diverges": True}))


if __name__ == "__main__":
    {"prepare": prepare, "analyze": analyze}[sys.argv[1]]()
