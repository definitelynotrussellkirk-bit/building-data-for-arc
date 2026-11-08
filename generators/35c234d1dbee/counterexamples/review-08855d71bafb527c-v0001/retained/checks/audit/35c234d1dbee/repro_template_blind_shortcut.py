#!/usr/bin/env python3
"""Reproduce the template-blind shortcut in generator 35c234d1dbee."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3] / "repo"
GEN_PATH = REPO / "generators" / "35c234d1dbee" / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_g35", GEN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def split_generated(grid):
    h, w = len(grid), len(grid[0])
    divs = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    assert len(divs) == 1, divs
    sep = divs[0]
    return [row[:sep] for row in grid], [row[sep + 1 :] for row in grid]


def crop_nonzero(panel):
    cells = [(r, c) for r, row in enumerate(panel) for c, v in enumerate(row) if v not in (0, 9)]
    assert cells
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in panel[r0 : r1 + 1]]


def canonical_oracle(grid):
    left, board = split_generated(grid)
    template = crop_nonzero(left)
    h, w = len(board), len(board[0])
    th, tw = len(template), len(template[0])
    matches = []
    for r0 in range(h - th + 1):
        for c0 in range(w - tw + 1):
            if not all(
                template[dr][dc] == 0 or board[r0 + dr][c0 + dc] == template[dr][dc]
                for dr in range(th)
                for dc in range(tw)
            ):
                continue
            clear = True
            for r in range(r0 - 1, r0 + th + 1):
                for c in range(c0 - 1, c0 + tw + 1):
                    if not (0 <= r < h and 0 <= c < w):
                        continue
                    inside = r0 <= r < r0 + th and c0 <= c < c0 + tw
                    if not inside and board[r][c] != 0:
                        clear = False
            if clear:
                matches.append((r0, c0))
    out = [[0] * w for _ in range(h)]
    for r0, c0 in matches:
        out[r0 + th // 2][c0 + tw // 2] = 8
    return out


def template_blind_rival(grid):
    _, board = split_generated(grid)
    h, w = len(board), len(board[0])
    seen = set()
    out = [[0] * w for _ in range(h)]
    for sr in range(h):
        for sc in range(w):
            if board[sr][sc] == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and board[nr][nc] != 0 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
            c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
            out[r0 + (r1 - r0 + 1) // 2][c0 + (c1 - c0 + 1) // 2] = 8
    return out


def recolor_template(grid):
    altered = [row[:] for row in grid]
    left, _ = split_generated(grid)
    old = next(v for row in left for v in row if v not in (0, 9))
    new = next(v for v in range(1, 8) if v != old)
    sep = len(left[0])
    for r in range(len(altered)):
        for c in range(sep):
            if altered[r][c] == old:
                altered[r][c] = new
    return altered


def main():
    gen = load_generator()
    total = 0
    agreements = 0
    first = None
    mismatches = []
    for difficulty in ("easy", None, "hard"):
        for seed in range(100):
            for sample_index in range(10):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                oracle = canonical_oracle(grid)
                rival = template_blind_rival(grid)
                total += 1
                same = oracle == rival
                agreements += same
                if not same and len(mismatches) < 10:
                    mismatches.append({
                        "difficulty": difficulty,
                        "seed": seed,
                        "sample_index": sample_index,
                        "self_check": gen.self_check(grid, difficulty=difficulty),
                        "canonical_marks": [[r, c] for r, row in enumerate(oracle) for c, value in enumerate(row) if value],
                        "template_blind_marks": [[r, c] for r, row in enumerate(rival) for c, value in enumerate(row) if value],
                        "grid": grid,
                    })
                if first is None:
                    first = grid
    assert first is not None
    altered = recolor_template(first)
    counterexample = {
        "input": altered,
        "canonical_output": canonical_oracle(altered),
        "template_blind_output": template_blind_rival(altered),
        "explanation": "Changing only the template color makes the board contain no matches, but the template-blind rival still marks every board component centre. The generator never emits this distinction because it copies the template color and shape into every board component and emits no decoys.",
    }
    result = {
        "samples_checked": total,
        "template_blind_agreements": agreements,
        "agreement_rate": agreements / total,
        "mismatch_count": total - agreements,
        "mismatches": mismatches,
        "altered_input_refutes_rival": counterexample["canonical_output"] != counterexample["template_blind_output"],
        "counterexample": counterexample,
    }
    out_path = Path(__file__).with_name("template_blind_evidence.json")
    out_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "counterexample"}, indent=2))
    print(f"evidence={out_path}")
    if agreements != total or not result["altered_input_refutes_rival"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
