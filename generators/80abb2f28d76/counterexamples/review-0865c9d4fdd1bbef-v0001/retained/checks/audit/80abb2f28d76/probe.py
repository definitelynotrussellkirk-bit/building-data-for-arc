"""Bounded findings-only audit. Run via the packet's review.py run wrapper."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

from arcpuzzles.catalog import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "80abb2f28d76"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def slide(grid, per_side=False):
    """Literal documented rival: closest independently on every occupied side."""
    blue = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    r0, r1 = min(r for r, _ in blue), max(r for r, _ in blue)
    c0, c1 = min(c for _, c in blue), max(c for _, c in blue)
    dots = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 9:
                continue
            if r0 <= r <= r1 and c < c0:
                dots.append((r, c, c0-c, 0))
            elif r0 <= r <= r1 and c > c1:
                dots.append((r, c, c-c1, 1))
            elif c0 <= c <= c1 and r < r0:
                dots.append((r, c, r0-r, 2))
            elif c0 <= c <= c1 and r > r1:
                dots.append((r, c, r-r1, 3))
            else:
                raise ValueError("probe supports side-aligned dots only")
    out = [[2 if v == 1 else 7 if v == 9 else v for v in row] for row in grid]
    for r, c, distance, side in dots:
        closest = min(d for _, _, d, s in dots if not per_side or s == side)
        win = distance == closest
        nr, nc = ((r, c0 if win else c0-1) if side == 0 else
                  (r, c1 if win else c1+1) if side == 1 else
                  (r0 if win else r0-1, c) if side == 2 else
                  (r1 if win else r1+1, c))
        out[nr][nc] = 9
    return out


def main():
    gen, source, sha = load_selected_generator(TASK, root=ROOT)
    records = []
    for seed in (0, 1):
        for side in gen.DOT_SIDES:
            overrides = {"dot_side": side, "n_dots": 3}
            grid = gen.generate(seed, 0, difficulty="medium", **overrides)
            records.append({"kind": "generated_ordinary", "seed": seed, "sample_index": 0,
                            "difficulty": "medium", "overrides": overrides, "input": grid})
    clamp = {"dot_side": "left", "rect_h": 3, "n_dots": 4}
    records.append({"kind": "generated_clamped_dot_count", "seed": 0, "sample_index": 0,
                    "difficulty": "hard", "overrides": clamp,
                    "input": gen.generate(0, 0, difficulty="hard", **clamp)})
    for name in gen.DEGENERATE_TEXTURES:
        records.append({"kind": "generated_degenerate", "seed": 0, "sample_index": 0,
                        "overrides": {"texture": name},
                        "input": gen.generate(0, 0, texture=name)})
    for index, pair in enumerate(canonical_pairs(TASK, root=ROOT, labeled_only=True)):
        records.append({"kind": "canonical", "canonical_pair_index": index,
                        "input": pair["input"], "expected": pair["output"]})
    witness = [[7]*12 for _ in range(12)]
    for r in range(4, 7):
        for c in range(4, 8):
            witness[r][c] = 1
    witness[4][2] = 9
    witness[1][5] = 9
    records.append({"kind": "handmade_multiside", "input": witness,
                    "sampler_domain": "outside documented single-side generation; self_check accepts"})
    for record in records:
        record["self_check"] = gen.self_check(record["input"])
        record["observed_n_dots"] = sum(v == 9 for row in record["input"] for v in row)
    application = Catalog(ROOT).apply(TASK, [r["input"] for r in records],
                                      check_generator_domain=True, timeout=120)
    (HERE / "racket.json").write_text(json.dumps(application, indent=2)+"\n")
    for record, actual in zip(records, application["results"], strict=True):
        record["racket_result_index"] = actual["index"]
        record["racket_output"] = actual["output"]
        record["racket_valid_output"] = actual["valid_output"]
        record["racket_error"] = actual["error"]
        if record["kind"] in {"generated_ordinary", "generated_clamped_dot_count", "canonical", "handmade_multiside"}:
            record["global_closest_mirror"] = slide(record["input"])
            record["per_side_closest_rival"] = slide(record["input"], per_side=True)
            record["global_matches_racket"] = record["global_closest_mirror"] == actual["output"]
            record["per_side_matches_racket"] = record["per_side_closest_rival"] == actual["output"]
            if record["kind"] == "canonical":
                record["canonical_label_matches_racket"] = record["expected"] == actual["output"]
    overrides = {"grid_h": 9, "grid_w": 9, "rect_h": 3, "rect_w": 7, "dot_side": "left"}
    try:
        grid = gen.generate(0, 0, difficulty="medium", **overrides)
        geometry = {"status": "generated", "input": grid}
    except Exception as exc:
        geometry = {"status": "raised", "exception": f"{type(exc).__name__}: {exc}"}
    geometry.update(seed=0, sample_index=0, difficulty="medium", overrides=overrides)
    report = {"task_id": TASK, "generator_sha256": sha,
              "rule_text_sha256": application["rule_text_sha256"],
              "executed_rule_hash": application["executed_rule_hash"],
              "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
              "declared_rivals": {name: list(getattr(gen, name, {})) for name in
                                  ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS")},
              "cases": records, "infeasible_declared_axes": geometry,
              "all_checked_global_mirrors_match": all(r.get("global_matches_racket", True) for r in records),
              "canonical_examples_match": all(r["canonical_label_matches_racket"] for r in records if r["kind"] == "canonical")}
    assert report["all_checked_global_mirrors_match"]
    assert report["canonical_examples_match"]
    (HERE / "probe-result.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"cases": len(records), "canonical_examples_match": report["canonical_examples_match"],
                      "invalid_degenerates": sum(not r["racket_valid_output"] for r in records if r["kind"] == "generated_degenerate"),
                      "generator_sha256": sha}, sort_keys=True))


if __name__ == "__main__":
    main()
