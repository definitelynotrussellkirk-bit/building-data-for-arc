"""Reproduce findings against the immutable ab8640b4ed72 audit source.

From the packet root:
  python3 -B WORK/checks/audit/ab8640b4ed72/repro.py
  python3 review.py run python3 -m arcpuzzles apply ab8640b4ed72 \
    --input ../checks/audit/ab8640b4ed72/input.json \
    --out ../checks/audit/ab8640b4ed72/racket.json
  python3 -B WORK/checks/audit/ab8640b4ed72/repro.py --racket WORK/checks/audit/ab8640b4ed72/racket.json

The apply command requires a new output path. For a repeat run, pass --out NEW_DIR
to this script and use that directory's input.json plus a new Racket receipt.
Successful reproduction exits 0; the observed defects are recorded in evidence.json.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
TASK = "ab8640b4ed72"
EXPECTED_SOURCE_SHA256 = "7aba5e1649635bb92f6aa602294267a1695f0632ccfcb91ce65ec3ddc4b5f6f2"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def grid_sha(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def independent_midpoint_mirror(grid):
    """A prediction only; actual labels come from arcpuzzles apply / Racket."""
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for r in range(h):
        for c in range(w-2):
            color = grid[r][c]
            if color and grid[r][c+1] == 0 and grid[r][c+2] == color:
                out[r][c+1] = color
    for r in range(h-2):
        for c in range(w):
            color = grid[r][c]
            if color and grid[r+1][c] == 0 and grid[r+2][c] == color:
                out[r+1][c] = color
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE)
    parser.add_argument("--racket", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    source = REPO / f"generators/{TASK}/generator.py"
    source_sha = sha(source)
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"Audit source changed: expected {EXPECTED_SOURCE_SHA256}, got {source_sha}")
    sys.path.insert(0, str(REPO/"shared/runtime"))
    from puzzle_generators.base import set_ctx_observer
    from reviewer_support import canonical_pairs
    spec = importlib.util.spec_from_file_location("audited_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    rows = []
    with (REPO/"shared/data/canonical/puzzles.jsonl").open() as f:
        for line in f:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append((row, hashlib.sha256(line.encode()).hexdigest()))
    assert len(rows) == 1
    program = rows[0][0]["program_solution"]
    canonical = canonical_pairs(TASK, root=REPO)
    inputs = [p["input"] for p in canonical]
    canonical_report = []
    for i, pair in enumerate(canonical):
        reasons = gen.self_check(pair["input"])
        canonical_report.append({"input_index": i, "variant": pair["variant"],
            "split": pair["split"], "pair_index": pair["pair_index"],
            "self_check": reasons,
            "independent_mirror_matches_stored_output": independent_midpoint_mirror(pair["input"]) == pair["output"]})

    def run_case(name, overrides, difficulty="medium", seed=0, index=0):
        contexts = []
        set_ctx_observer(contexts.append)
        result = {"name": name, "seed": seed, "sample_index": index,
                  "difficulty": difficulty, "overrides": overrides}
        try:
            grid = gen.generate(seed, index, difficulty=difficulty, **overrides)
            colors = Counter(v for row in grid for v in row if v)
            result.update({"error": None, "shape": [len(grid), len(grid[0])],
                "foreground_counts": dict(sorted(colors.items())), "n_foreground_colors": len(colors),
                "self_check": gen.self_check(grid, difficulty=difficulty), "input_sha256": grid_sha(grid)})
            if grid not in inputs:
                inputs.append(grid)
            result["input_index"] = inputs.index(grid)
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            set_ctx_observer(None)
        if contexts:
            result["recorded_draws"] = contexts[0].recorded_draws()
            result["overrides_used"] = contexts[0].overrides_used()
        return result

    cases = [
        run_case("baseline", {}),
        run_case("palette_size_one", {"palette_size": 1}),
        run_case("n_distinct_colors_one", {"n_distinct_colors": 1}),
        run_case("warm", {"palette_kind": "warm"}),
        run_case("cool", {"palette_kind": "cool"}),
        run_case("declared_height_14_medium", {"grid_h": 14}),
        run_case("declared_height_14_hard", {"grid_h": 14}, "hard"),
        run_case("declared_width_5", {"grid_w": 5}),
        run_case("declared_bridge_count_8", {"grid_h": 13, "grid_w": 16, "bridge_count": 8}, "hard"),
    ]
    baseline = cases[0]
    assert baseline["n_foreground_colors"] == 4 and baseline["self_check"] == []
    for case in cases[1:5]:
        assert case["input_sha256"] == baseline["input_sha256"]
        assert case["overrides_used"] == {}
        assert case["self_check"] == []
    assert canonical_report[0]["self_check"] == ["color 6 appears 1 times; expected exactly two endpoints"]
    assert all(not p["self_check"] for p in canonical_report[1:])
    assert all(p["independent_mirror_matches_stored_output"] for p in canonical_report)
    assert all(c["error"] for c in cases[5:])
    report = {
        "task_id": TASK, "generator_sha256": source_sha,
        "generator_version": gen.VERSION, "canonical_variant_count": len(rows),
        "raw_canonical_row_sha256_including_newline": rows[0][1],
        "raw_canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "normalized_rule_hash": hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12],
        "reproducer_sha256": sha(__file__),
        "declared_axes": gen.AXES,
        "canonical_self_check": canonical_report,
        "generated_controls": cases,
        "claims": {
            "ignored_numeric_color_controls": ["palette_size", "n_distinct_colors"],
            "ignored_palette_kind_controls": ["warm", "cool"],
            "canonical_rejected_count": 1, "canonical_input_count": len(canonical),
            "raw_generated_rule_mismatch_found": False,
        },
        "authority": None,
        "limits": ["Independent mirror predictions are not authoritative labels.",
                   "Canonical exclusion is a domain/support defect; it is not a claim that sampled generator labels are wrong.",
                   "No full battery was run. The preliminary 10000-seed placement search found no requested-count shortfall."],
    }
    if args.racket:
        authority = json.loads(args.racket.read_text())
        assert authority["generator_sha256"] == source_sha
        assert authority["rule_hash_matches_catalog"]
        assert authority["executed_rule_hash"] == report["normalized_rule_hash"]
        assert len(authority["results"]) == len(inputs)
        results = []
        for i, result in enumerate(authority["results"]):
            assert result["input"] == inputs[i]
            assert result["valid_output"] and result["error"] is None
            mirror_matches = result["output"] == independent_midpoint_mirror(inputs[i])
            assert mirror_matches
            stored_matches = result["output"] == canonical[i]["output"] if i < len(canonical) else None
            if stored_matches is not None:
                assert stored_matches
            results.append({"input_index": i, "valid_output": True, "mirror_matches": mirror_matches,
                "stored_canonical_matches": stored_matches,
                "changed_cells": [[r,c,v] for r,row in enumerate(result["output"]) for c,v in enumerate(row) if inputs[i][r][c]!=v]})
        report["authority"] = {"receipt": args.racket.name, "receipt_sha256": sha(args.racket),
            "executed_rule_hash": authority["executed_rule_hash"],
            "wrapped_callable_sha256": authority["rule_text_sha256"], "results": results,
            "canonical_singleton_input_coordinate": [4,5],
            "canonical_singleton_color_before": inputs[0][4][5],
            "canonical_singleton_color_after": authority["results"][0]["output"][4][5]}
    (args.out/"input.json").write_text(json.dumps({"inputs":inputs})+"\n")
    (args.out/"evidence.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"task_id":TASK,"source_sha256":source_sha,"rule_hash":report["normalized_rule_hash"],
        "input_count":len(inputs),"canonical_rejections":1,"canonical_total":len(canonical),
        "baseline_foreground_colors":list(baseline["foreground_counts"]),
        "color_controls_identical_to_baseline":True,"actual_Racket_verified":args.racket is not None,
        "evidence":str(args.out/"evidence.json")},indent=2))


if __name__ == "__main__":
    main()
