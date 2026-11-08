"""Bounded ordinary-lesson audit for the one-step halo generator; no edits/approval."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2] / "repo"
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import load_selected_generator
from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator, _grid

TASK = "517a230ecc8c"
DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def sha(value):
    if isinstance(value, str):
        value = value.encode()
    elif not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


def expand(grid, *, diagonal=False, exactly_one=False, suppress_border=False):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    deltas = DELTAS + (((-1, -1), (-1, 1), (1, -1), (1, 1)) if diagonal else ())
    for r in range(h):
        for c in range(w):
            if grid[r][c] or suppress_border and (r in (0, h - 1) or c in (0, w - 1)):
                continue
            neighbors = [grid[r + dr][c + dc] for dr, dc in deltas
                         if 0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc]]
            if neighbors and len(set(neighbors)) == 1 and (not exactly_one or len(neighbors) == 1):
                out[r][c] = neighbors[0]
    return out


def bbox_first(grid):
    out = [row[:] for row in grid]
    for color in sorted({v for row in grid for v in row} - {0}):
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        for r in range(min(r for r, _ in cells), max(r for r, _ in cells) + 1):
            for c in range(min(c for _, c in cells), max(c for _, c in cells) + 1):
                out[r][c] = color
    return expand(out)


def local_program(*, diagonal=False, exactly_one=False, suppress_border=False, bbox=False):
    condition = "(= (length ns) 1)" if exactly_one else "(= (length (remove-duplicates ns)) 1)"
    border = "(or (= r 0) (= c 0) (= r (- h 1)) (= c (- w 1)))" if suppress_border else "#f"
    base = "g"
    if bbox:
        base = """(for/fold ([out g]) ([o (in-list (objects g 0))])
          (paint-cells out (positions-in-rect (obj-r1 o) (obj-c1 o) (obj-r2 o) (obj-c2 o)) (obj-color o)))"""
    return f"""(rule! (lambda (g)
      (let* ([state {base}] [h (rows state)] [w (cols state)])
        (cellmap state (r c v)
          (if (or (not (= v 0)) {border}) v
              (let ([ns (filter (lambda (x) (not (= x 0)))
                         (map (lambda (d) (safe-at state (+ r (first d)) (+ c (second d)) 0))
                              {'all-8-deltas' if diagonal else 'cardinal-deltas'}))])
                (if (and (not (null? ns)) {condition}) (car ns) 0)))))))"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=64)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("Use a new output path")
    module, source_path, source_hash = load_selected_generator(TASK, root=ROOT)
    catalog = Catalog(ROOT)
    description = catalog.describe(TASK)
    canonical = {v["program_solution"] for v in catalog.get(TASK)["variants"] if isinstance(v.get("program_solution"), str)}
    if len(canonical) != 1:
        raise ValueError("Canonical program is not unique")
    program = canonical.pop()
    allow_unapproved = not description["approved"]
    episodes = catalog.generate(TASK, count=args.count, seed=args.seed, allow_unapproved=allow_unapproved, timeout=180)
    rivals = {
        "exactly_one_occupied_neighbor": (lambda g: expand(g, exactly_one=True), local_program(exactly_one=True)),
        "bbox_then_cardinal_halo": (bbox_first, local_program(bbox=True)),
        "eight_neighbor_halo": (lambda g: expand(g, diagonal=True), local_program(diagonal=True)),
        "never_paint_outer_border": (lambda g: expand(g, suppress_border=True), local_program(suppress_border=True)),
    }
    report = {
        "schema": "arcpuzzles-peer-finite-lesson-probe-v1", "task_id": TASK,
        "source_path": str(source_path.relative_to(ROOT)), "source_sha256": source_hash,
        "probe_sha256": sha(Path(__file__).read_bytes()), "version": module.VERSION,
        "canonical_program": program, "canonical_program_sha256": sha(program),
        "rule_hash": description.get("rule_hash"), "allow_unapproved": allow_unapproved,
        "request": {"count": args.count, "seed": args.seed, "difficulty": None, "n_train": "ordinary default", "n_test": "ordinary default"},
        "rivals": {name: {"program": p, "program_sha256": sha(p)} for name, (_, p) in rivals.items()},
        "episodes": [], "findings": [],
    }
    candidates = []
    for index, episode in enumerate(episodes):
        actual_program = episode.get("program_solution", episode.get("program", program))
        row = {"index": index, "seed": episode.get("seed"), "sample_index": episode.get("sample_index"),
               "sampling": episode.get("sampling"), "demos": len(episode["train"]), "queries": len(episode["test"]),
               "program_sha256": sha(actual_program), "checks": []}
        for name, (predict, rival_program) in rivals.items():
            demo_diffs = [i for i, pair in enumerate(episode["train"]) if predict(pair["input"]) != pair["output"]]
            query_diffs = [i for i, pair in enumerate(episode["test"]) if predict(pair["input"]) != pair["output"]]
            row["checks"].append({"rival": name, "demo_disagreements": demo_diffs, "query_disagreements": query_diffs})
            if not demo_diffs and query_diffs:
                candidates.append((index, name, query_diffs[0]))
        report["episodes"].append(row)
    if candidates:
        index, name, query_index = candidates[0]
        episode = episodes[index]
        predict, rival_program = rivals[name]
        finding = {"classification": "ordinary_lesson_underidentified_against_plausible_rival", "episode_index": index,
                   "seed": episode.get("seed"), "sampling": episode.get("sampling"), "rival": name,
                   "train": [], "query_index": query_index, "program": program, "rival_program": rival_program}
        with _local_imports(ROOT / "shared/runtime", Path(__file__).parent):
            apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
            try:
                for split, pairs in (("train", episode["train"]), ("query", [episode["test"][query_index]])):
                    for pair in pairs:
                        intended = _grid(apply(program, pair["input"]))
                        altered = _grid(apply(rival_program, pair["input"]))
                        assert intended == pair["output"]
                        assert altered == predict(pair["input"])
                        result = {"input": pair["input"], "output": intended, "rival_output": altered, "agree": intended == altered}
                        if split == "train": finding["train"].append(result)
                        else: finding["query"] = result
                finding["racket"] = identity
                finding["protected_executions"] = 2 * (len(episode["train"]) + 1)
            finally:
                bridge.close()
        assert all(row["agree"] for row in finding["train"]) and not finding["query"]["agree"]
        finding["repair_proposal"] = "Select a short ordinary lesson containing a concavity/irregular shape or boundary witness that refutes the surviving halo rival; retain the original ambiguous lesson as separate optional interpretation research."
        report["findings"].append(finding)
    if sha(source_path.read_bytes()) != source_hash:
        raise ValueError("Selected generator source changed during the bounded probe")
    report["candidate_count"] = len(candidates)
    report["status"] = "protected_finding" if report["findings"] else "no_hole_among_declared_rivals_in_sample"
    report["limits"] = "Four finite rivals and a bounded ordinary-default lesson sample; not universal uniqueness, exhaustive validation, approval, or a production repair."
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "episodes": len(episodes), "demo_counts": sorted({len(e['train']) for e in episodes}),
                      "query_counts": sorted({len(e['test']) for e in episodes}), "candidate_count": len(candidates),
                      "source_sha256": source_hash, "rule_hash": report["rule_hash"], "report": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()
