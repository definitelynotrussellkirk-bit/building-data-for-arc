"""Bounded K/control and real-Racket label probes; run via review.py run.

From packet outer directory:
WORK/.venv/bin/python review.py run ../.venv/bin/python \
    generators/6bbf6747b137/workspace/verify_repair.py ../checks/6bbf6747b137/probe.json
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_path, canonical_pairs, find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.runner import wrap_rule

TASK = "6bbf6747b137"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_HASH = load_selected_generator(TASK, root=ROOT)


def components(grid):
    remaining = {(r, c) for r in range(1, len(grid))
                 for c in range(len(grid[0])) if grid[r][c]}
    parts = []
    while remaining:
        start = remaining.pop()
        cells, todo = {start}, [start]
        while todo:
            r, c = todo.pop()
            for p in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                if p in remaining:
                    remaining.remove(p)
                    cells.add(p)
                    todo.append(p)
        parts.append(cells)
    return parts


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def main(out_path):
    row = next(json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
               if json.loads(line).get("task_id") == TASK)
    rule = row["program_solution"]
    cases, failures, witnesses = [], [], []
    draws = []
    # Minimum existing default shape: exercise each K and all difficulty bands.
    for band in ("easy", "medium", "hard"):
        for k in range(1, 7):
            for seed in (0, 1, 17, 42):
                grid = GEN.generate(seed, 0, difficulty=band, K=k)
                draws.append((f"{band}/K{k}/s{seed}", grid, True))
    for texture in GEN.DEGENERATE_TEXTURES:
        draws.append((texture, GEN.generate(17, 0, texture=texture), False))
    for pair in canonical_pairs(TASK, root=ROOT):
        draws.append((f"canonical/{pair['split']}/{pair['pair_index']}", pair["input"], False))
    canonical_outputs = {f"canonical/{pair['split']}/{pair['pair_index']}": pair["output"]
                         for pair in canonical_pairs(TASK, root=ROOT)}
    with RacketBridge() as bridge:
        runtime = bridge.runtime_identity
        for name, grid, normal in draws:
            k = grid[0].count(1)
            parts = components(grid)
            sizes = sorted(map(len, parts))
            if normal and (len(parts) != 3 or len(set(sizes)) != 3 or sizes.count(k) != 1):
                failures.append({"name": name, "kind": "sampler_domain", "sizes": sizes,
                                 "K": k, "input": grid})
            expected = [[0] * len(grid[0]) for _ in grid]
            for cells in parts:
                if len(cells) == k:
                    for r, c in cells:
                        expected[r][c] = grid[r][c]
            literal = "'(" + " ".join("(" + " ".join(map(str, r)) + ")" for r in grid) + ")"
            output = bridge.eval_text(f"({wrap_rule(rule)} {literal})")
            if name in canonical_outputs and output != canonical_outputs[name]:
                failures.append({"name": name, "kind": "canonical_label",
                                 "racket_output": output, "stored_output": canonical_outputs[name]})
            if output != expected:
                failures.append({"name": name, "kind": "racket_label", "input": grid,
                                 "expected_from_components": expected, "racket_output": output})
            errors = GEN.self_check(grid)
            if errors:
                failures.append({"name": name, "kind": "self_check", "errors": errors})
            cases.append({"name": name, "K": k, "areas": sizes,
                          "input_sha256": digest(grid), "racket_output_sha256": digest(output)})
            if name in ("easy/K1/s17", "easy/K5/s17"):
                witnesses.append({"name": name, "input": grid, "output": output,
                                  "label_authority": "actual Racket canonical rule"})
        # The exact same body receives different executed labels when its header changes.
        grid = GEN.generate(17, 0, K=3)
        outputs = []
        for cells in sorted(components(grid), key=len)[:2]:
            varied = deepcopy(grid)
            varied[0] = [int(c < len(cells)) for c in range(len(grid[0]))]
            literal = "'(" + " ".join("(" + " ".join(map(str, r)) + ")" for r in varied) + ")"
            outputs.append(bridge.eval_text(f"({wrap_rule(rule)} {literal})"))
        if outputs[0] == outputs[1]:
            failures.append({"kind": "header_dependence"})
    report = {"task_id": TASK, "source_sha256": SOURCE_HASH,
              "rule_sha256": hashlib.sha256(rule.encode()).hexdigest(),
              "surfaces": ["K override and sampler domain", "canonical Racket labels and header ablation"],
              "normal_draws": 72, "degenerate_draws": 3, "canonical_pairs": 3,
              "header_ablation_calls": 2, "runtime": runtime,
              "cases": cases, "witnesses": witnesses, "failures": failures}
    Path(out_path).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"cases": len(cases), "failures": len(failures), "out": out_path}))
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
