"""CPU preparation / receipt assessment for a bounded findings-only peer audit."""
from collections import Counter
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "fa3550d200a0"
ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def components(grid, diagonal=True):
    seen = set()
    result = []
    deltas = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
              if (dr or dc) and (diagonal or abs(dr) + abs(dc) == 1)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 or (r, c) in seen:
                continue
            seen.add((r, c)); stack = [(r, c)]; cells = []
            while stack:
                point = stack.pop(); cells.append(point)
                for dr, dc in deltas:
                    rr, cc = point[0] + dr, point[1] + dc
                    if 0 <= rr < len(grid) and 0 <= cc < len(row) and grid[rr][cc] and (rr, cc) not in seen:
                        seen.add((rr, cc)); stack.append((rr, cc))
            result.append(cells)
    return result


def stamp(grid, *, diagonal=True, crop_only=False):
    counts = Counter(v for row in grid for v in row if v)
    canvas = counts.most_common(1)[0][0]
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == canvas]
    top, bottom = min(r for r, c in cells), max(r for r, c in cells)
    left, right = min(c for r, c in cells), max(c for r, c in cells)
    out = [row[left:right + 1] for row in grid[top:bottom + 1]]
    if crop_only:
        return out
    for obj in components(grid, diagonal):
        if not any(r < top or r > bottom or c < left or c > right for r, c in obj):
            continue
        specials = [(r, c) for r, c in obj if grid[r][c] not in (0, 2, canvas)]
        if not specials:
            continue
        sr, sc = specials[0]
        marker = grid[sr][sc]
        matches = [(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)
                   if grid[r][c] == marker]
        if not matches:
            continue
        ar, ac = matches[0]
        for r, c in obj:
            rr, cc = ar - top + r - sr, ac - left + c - sc
            if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                out[rr][cc] = grid[r][c]
    return out


def handmade():
    grid = [[0] * 24 for _ in range(20)]
    for r in range(6, 12):
        for c in range(1, 7):
            grid[r][c] = 1
    grid[7][2] = 3; grid[10][5] = 4
    # Two diagonal-only matched pieces and an unmatched distractor.
    for r, c, marker in [(2, 12, 3), (8, 12, 4), (14, 12, 5)]:
        grid[r][c] = marker; grid[r + 1][c + 1] = 2
    return grid


def prepare():
    gen, source, generator_hash = load_selected_generator(TASK, root=ROOT)
    rules = []
    for line in canonical_path(ROOT).open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rules.append(row["program_solution"])
    assert len(set(rules)) == 1
    cases = []
    for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        cases.append({"kind": "canonical", "canonical_identity": {k: pair[k] for k in ("variant", "split", "pair_index")},
                      "input": pair["input"], "canonical_output": pair["output"], "generated": None})
    for index in range(4):
        spec = {"seed": 91, "sample_index": index, "difficulty": "medium", "overrides": {}}
        cases.append({"kind": "generated-default-schedule", "input": gen.generate(91, index, difficulty="medium"), "generated": spec})
    for seed in (0, 17):
        for side in ("left", "right"):
            for palette in gen.PALETTE_KINDS:
                overrides = dict(grid_h=20, grid_w=24, piece_count=5, decoy_count=1, rect_h=6, rect_w=6,
                                 canvas_side=side, palette_kind=palette)
                spec = {"seed": seed, "sample_index": 3, "difficulty": "hard", "overrides": overrides}
                cases.append({"kind": "generated-boundary", "input": gen.generate(seed, 3, difficulty="hard", **overrides), "generated": spec})
    valid = handmade()
    cases.append({"kind": "handmade-diagonal-matches-and-decoy", "input": valid, "generated": None,
                  "domain_expectation": "Accepted documented 8-connected domain; outside the three-to-five-cell sampler templates."})
    clipped = deepcopy(valid); clipped[10][5] = 1; clipped[11][6] = 4
    cases.append({"kind": "handmade-clipped-stamp-negative-control", "input": clipped, "generated": None,
                  "domain_expectation": "Rejected: matched marker 4 has payload beyond the bottom/right canvas boundary."})
    for index, case in enumerate(cases):
        grid = case["input"]
        case.update({"index": index, "self_check": gen.self_check(grid), "diagnostic_stamp": stamp(grid),
                     "rival_four_connected": stamp(grid, diagonal=False), "rival_crop_only": stamp(grid, crop_only=True),
                     "input_sha256": sha(json.dumps(grid, sort_keys=True, separators=(",", ":")).encode())})
        if not case["self_check"]:
            case["observed_axes"] = gen.observe_overrides(grid)
    assert all(not case["self_check"] for case in cases[:-1])
    assert any("clipped" in error for error in cases[-1]["self_check"])
    (OUT / "input.json").write_text(json.dumps({"inputs": [case["input"] for case in cases]}, indent=2) + "\n")
    record = {"task_id": TASK, "generator_sha256": generator_hash,
              "generator_source": str(source.relative_to(ROOT)), "rule_sha256": sha(rules[0].encode()),
              "canonical_rows": len(rules), "cases": cases,
              "declared_rivals": {name: sorted(getattr(gen, name, {})) for name in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")},
              "status": "CPU-prepared; actual Racket receipt required before semantic conclusion"}
    (OUT / "prepared.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"cases": len(cases), "accepted": len(cases)-1, "negative_controls": 1,
                      "generator_sha256": generator_hash, "rule_sha256": record["rule_sha256"]}, indent=2))


def assess():
    prepared = json.loads((OUT / "prepared.json").read_text())
    receipt = json.loads((OUT / "racket.json").read_text())
    assert receipt["generator_sha256"] == prepared["generator_sha256"]
    # apply's rule_text_sha256 identifies the wrapped callable, not raw
    # program_solution bytes. Bind both identities rather than conflate them.
    source_rules = [json.loads(line)["program_solution"] for line in canonical_path(ROOT).open()
                    if json.loads(line).get("task_id") == TASK]
    assert all(sha(source.encode()) == prepared["rule_sha256"] for source in source_rules)
    assert receipt["executed_rule_hash"] == sha(" ".join(source_rules[0].split()).encode())[:12]
    assert len(receipt["results"]) == len(prepared["cases"])
    rows = []
    for case, actual in zip(prepared["cases"], receipt["results"]):
        assert actual["output"] is not None, actual
        rows.append({"index": case["index"], "kind": case["kind"], "self_check": case["self_check"],
                     "diagnostic_matches_racket": case["diagnostic_stamp"] == actual["output"],
                     "canonical_matches_racket": case.get("canonical_output", actual["output"]) == actual["output"],
                     "four_connected_rival_matches": case["rival_four_connected"] == actual["output"],
                     "crop_only_rival_matches": case["rival_crop_only"] == actual["output"]})
    accepted = [row for row in rows if not row["self_check"]]
    canonical = [row for row in rows if row["kind"] == "canonical"]
    summary = {"task_id": TASK, "generator_sha256": prepared["generator_sha256"], "rule_source_sha256": prepared["rule_sha256"],
               "executed_rule_hash": receipt["executed_rule_hash"], "executed_callable_sha256": receipt["rule_text_sha256"],
               "actual_receipt": "checks/audit/fa3550d200a0/racket.json", "count": len(rows),
               "diagnostic_mismatches": [row["index"] for row in rows if not row["diagnostic_matches_racket"]],
               "canonical_mismatches": [row["index"] for row in rows if not row["canonical_matches_racket"]],
               "four_connected_rival_rejected": sum(not row["four_connected_rival_matches"] for row in rows),
               "crop_only_rival_rejected": sum(not row["crop_only_rival_matches"] for row in rows),
               "accepted_cases": len(accepted),
               "accepted_four_connected_rival_rejected": sum(not row["four_connected_rival_matches"] for row in accepted),
               "accepted_crop_only_rival_rejected": sum(not row["crop_only_rival_matches"] for row in accepted),
               "canonical_cases": len(canonical),
               "canonical_four_connected_rival_rejected": sum(not row["four_connected_rival_matches"] for row in canonical),
               "canonical_crop_only_rival_rejected": sum(not row["crop_only_rival_matches"] for row in canonical),
               "cases": rows}
    (OUT / "assessment.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({key: value for key, value in summary.items() if key != "cases"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "assess"))
    args = parser.parse_args()
    prepare() if args.mode == "prepare" else assess()
