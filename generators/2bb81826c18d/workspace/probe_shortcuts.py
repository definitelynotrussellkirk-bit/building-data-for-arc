"""Small baseline shortcut screen; confirm candidates with public Racket apply.

Run from the packet through review.py run. Only public canonical train pairs are
read. The scan's Python reference is a candidate screen, not label authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

TASK = "2bb81826c18d"
BASELINE_SHA = "f4b85948212752aa24e5c08ff174cb850645663a6140f952eba2019154abf28b"
RULE_HASH = "b0e1d6662c7a"


def rectangles(grid):
    """Color boxes suffice on this task's separated, unique-color rectangles."""
    for color in sorted({v for row in grid for v in row} - {0}):
        cells = [(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == color]
        top = min(r for r, _ in cells)
        bottom = max(r for r, _ in cells)
        left = min(c for _, c in cells)
        right = max(c for _, c in cells)
        yield dict(color=color, top=top, bottom=bottom, left=left, right=right,
                   height=bottom-top+1, width=right-left+1)


def predict(grid, rival):
    out = [row[:] for row in grid]
    for box in rectangles(grid):
        t, b, l, q = (box[k] for k in ("top", "bottom", "left", "right"))
        if rival == "identity" or (rival == "skip_thin_rectangles"
                                  and min(box["height"], box["width"]) < 5):
            continue
        for r in range(t+1, b):
            for c in range(l+1, q):
                phases = {
                    "local": (r-t)+(c-l),
                    "skip_thin_rectangles": (r-t)+(c-l),
                    "column_global_phase": (r-t)+c,
                    "row_global_phase": r+(c-l),
                    "global_even_phase": r+c,
                    "opposite_local_phase": (r-t)+(c-l)+1,
                    "top_right_anchor": (r-t)+(q-c),
                    "bottom_left_anchor": (b-r)+(c-l),
                    "bottom_right_anchor": (b-r)+(q-c),
                    "erase_all_interior": 0,
                    "row_stripes": r-t-1,
                    "column_stripes": c-l-1,
                }
                if phases[rival] % 2 == 0:
                    out[r][c] = 0
    return out


RIVALS = ("skip_thin_rectangles", "column_global_phase", "row_global_phase",
          "global_even_phase", "opposite_local_phase", "top_right_anchor",
          "bottom_left_anchor", "bottom_right_anchor", "erase_all_interior",
          "row_stripes", "column_stripes", "identity")


def sha(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def scan(repo, out):
    from arcpuzzles import Catalog
    sys.path.insert(0, str(repo / "shared/runtime"))
    from reviewer_support import load_selected_generator
    generator, path, source_sha = load_selected_generator(TASK, root=repo)
    if source_sha != BASELINE_SHA:
        raise ValueError("Baseline source changed; replay saved inputs or use baseline bytes")
    challenge = Catalog(repo).challenge(TASK, variant=0)
    canonical = challenge["train"]
    fit = {name: all(predict(p["input"], name) == p["output"] for p in canonical)
           for name in RIVALS}
    counts = Counter()
    candidates = {}
    structure = {"n_rects": Counter(), "min_side": Counter(), "left_parity": Counter(),
                 "top_parity": Counter(), "height_parity": Counter(), "width_parity": Counter()}
    for band in ("easy", "medium", "hard"):
        for seed in range(200):
            inputs = [generator.generate(seed, i, difficulty=band) for i in range(4)]
            outputs = [predict(grid, "local") for grid in inputs]
            for grid in inputs:
                boxes = list(rectangles(grid))
                structure["n_rects"][len(boxes)] += 1
                for box in boxes:
                    structure["min_side"][min(box["height"], box["width"])] += 1
                    for axis in ("left", "top", "height", "width"):
                        structure[axis+"_parity"][box[axis] % 2] += 1
            for rival in ("skip_thin_rectangles", "column_global_phase"):
                fits = [predict(grid, rival) == output for grid, output in zip(inputs, outputs)]
                if all(fits[:3]) and not fits[3]:
                    counts[band+":"+rival] += 1
                    if rival not in candidates:
                        candidates[rival] = dict(rival=rival, seed=seed, difficulty=band,
                                                 sample_indices=list(range(4)), overrides={},
                                                 inputs=inputs, rectangles=[list(rectangles(g)) for g in inputs],
                                                 query_prediction=predict(inputs[3], rival))
    out.mkdir(parents=True, exist_ok=True)
    public = {"train": canonical, "test": challenge["test"]}
    (out / "canonical_public.json").write_text(json.dumps(public, separators=(",", ":"))+"\n")
    rows = []
    inputs = []
    for pi, pair in enumerate(canonical):
        rows.append(dict(kind="canonical_train", pair_index=pi, input_index=len(inputs)))
        inputs.append(pair["input"])
    for rival, candidate in candidates.items():
        candidate["apply_input_indices"] = list(range(len(inputs), len(inputs)+4))
        inputs.extend(candidate["inputs"])
    receipt = dict(task_id=TASK, generator_sha256=source_sha, rule_hash=RULE_HASH,
                   probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   canonical_scope="variant 0 public train only; no hidden query labels read",
                   canonical_visible_fit=fit,
                   canonical_rectangles=[list(rectangles(p["input"])) for p in canonical],
                   scan_settings=dict(bands=["easy", "medium", "hard"], seeds="0..199",
                                      sample_indices=[0,1,2,3], overrides={}),
                   counts_are="Python-screened candidates, not Racket-confirmed population estimates",
                   ambiguous_candidates=dict(counts), structural_counts=structure,
                   canonical_apply_rows=rows, candidates=candidates)
    (out / "screen.json").write_text(json.dumps(receipt, indent=2)+"\n")
    (out / "apply_inputs.json").write_text(json.dumps({"inputs":inputs}, separators=(",", ":"))+"\n")
    print(json.dumps({"canonical_visible_fit":fit, "ambiguities":dict(counts),
                      "first_candidates":{k:{a:v[a] for a in ("seed","difficulty","sample_indices")}
                                          for k,v in candidates.items()}}, indent=2))


def verify(out, applied):
    screen = json.loads((out / "screen.json").read_text())
    report = json.loads(applied.read_text())
    if report["executed_rule_hash"] != RULE_HASH or report["generator_sha256"] != BASELINE_SHA:
        raise ValueError("Apply receipt is not bound to baseline source and rule")
    canonical = json.loads((out / "canonical_public.json").read_text())["train"]
    results = report["results"]
    for item in screen["canonical_apply_rows"]:
        assert results[item["input_index"]]["output"] == canonical[item["pair_index"]]["output"]
    verified = {}
    for rival, candidate in screen["candidates"].items():
        rows = [results[i] for i in candidate["apply_input_indices"]]
        assert [r["input"] for r in rows] == candidate["inputs"]
        fit = [predict(r["input"], rival) == r["output"] for r in rows]
        assert fit == [True, True, True, False], (rival, fit)
        ref = rows[3]["output"]
        pred = candidate["query_prediction"]
        differences = [[r,c,ref[r][c],pred[r][c]] for r in range(len(ref))
                       for c in range(len(ref[0])) if ref[r][c] != pred[r][c]]
        verified[rival] = dict(seed=candidate["seed"], difficulty=candidate["difficulty"],
                               sample_indices=candidate["sample_indices"], overrides=candidate["overrides"],
                               demonstration_fit=fit[:3], query_fit=fit[3],
                               query_input_sha256=sha(rows[3]["input"]), query_output_sha256=sha(ref),
                               query_differences=differences, query_prediction=pred,
                               apply_input_indices=candidate["apply_input_indices"])
    final = dict(task_id=TASK, generator_sha256=BASELINE_SHA, rule_hash=RULE_HASH,
                 apply_receipt_sha256=hashlib.sha256(applied.read_bytes()).hexdigest(),
                 canonical_visible_pairs_verified=len(canonical), verified_ambiguities=verified,
                 scope="Actual Racket applies to exact generated consecutive 3-demo+1-query draws")
    (out / "verified.json").write_text(json.dumps(final, indent=2)+"\n")
    print(json.dumps({"verified":{k:{a:v[a] for a in ("seed","difficulty","demonstration_fit","query_fit")}
                                  for k,v in verified.items()}}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("scan", "verify"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--apply", type=Path)
    args = parser.parse_args()
    if args.mode == "scan":
        scan(Path(__file__).resolve().parents[3], args.out)
    else:
        verify(args.out, args.apply)
