from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter, deque
from pathlib import Path

import argparse
import sys

RUNTIME = next((p / "shared" / "runtime" for p in Path(__file__).resolve().parents
                if (p / "shared" / "runtime" / "reviewer_support.py").is_file()), None)
if RUNTIME is None:
    raise FileNotFoundError("Run from a relocated ARCpuzzles library containing shared/runtime")
sys.path.insert(0, str(RUNTIME))
from reviewer_support import find_root
ROOT = find_root(__file__)
TASK = "0f6ba01fa18c"
GEN_PATH = ROOT / "generators" / TASK / "generator.py"
EXPECTED_GENERATOR_SHA256 = "405d2408290ceb3e8d9f9d792733d609ce1493622da30ac4a81030d396ca521a"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GEN_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def components(grid, color):
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
    out = []
    while cells:
        start = min(cells)
        cells.remove(start)
        q = deque([start])
        comp = [start]
        while q:
            r, c = q.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                p = (r + dr, c + dc)
                if p in cells:
                    cells.remove(p)
                    q.append(p)
                    comp.append(p)
        out.append(sorted(comp))
    return out


def normalize(cells):
    if not cells:
        return set()
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return {(r - mr, c - mc) for r, c in cells}


def render(cells):
    if not cells:
        return [[0]]
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    out = [[0] * w for _ in range(h)]
    for r, c in cells:
        out[r][c] = 8
    return out


def all_cells_rival(grid):
    a = normalize([(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1])
    b = normalize([(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2])
    key = next(v for row in grid for v in row if v in (3, 4, 6))
    if key == 3:
        cells = a | b
    elif key == 4:
        cells = a & b
    else:
        cells = a ^ b
    return render(normalize(cells))


def main():
    parser = argparse.ArgumentParser(description="Replay this source-bound audit; retained evidence is never overwritten.")
    parser.add_argument("--out", required=True, type=Path, help="New output directory for the replay")
    args = parser.parse_args()
    OUT = args.out.resolve()
    if OUT.exists():
        raise FileExistsError("Choose a new output directory; existing evidence is immutable")
    if hashlib.sha256(GEN_PATH.read_bytes()).hexdigest() != EXPECTED_GENERATOR_SHA256:
        raise ValueError("Generator changed since the audit; use the audited source to reproduce it")
    OUT.mkdir(parents=True)
    gen = load_generator()
    grid = [[0] * 10 for _ in range(8)]
    for r, c in ((1, 1), (2, 1), (2, 2), (5, 1)):
        grid[r][c] = 1
    for r, c in ((1, 6), (1, 7)):
        grid[r][c] = 2
    grid[7][9] = 3

    key_counts = {}
    unique_counts = {}
    for difficulty in ("easy", "medium", "hard"):
        keys = []
        sigs = set()
        for seed in range(200):
            g = gen.generate(seed, 0, difficulty=difficulty)
            keys.append(next(v for row in g for v in row if v in (3, 4, 6)))
            sigs.add(json.dumps(g, separators=(",", ":")))
        key_counts[difficulty] = dict(sorted(Counter(keys).items()))
        unique_counts[difficulty] = len(sigs)

    report = {
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "generator_version": gen.VERSION,
        "input_kind": "validator adversary outside ordinary generator domain",
        "input_shape": [len(grid), len(grid[0])],
        "self_check": gen.self_check(grid),
        "color_1_component_sizes": [len(x) for x in components(grid, 1)],
        "color_2_component_sizes": [len(x) for x in components(grid, 2)],
        "all_color_cells_rival_output": all_cells_rival(grid),
        "band_key_counts_200_seeds": key_counts,
        "band_unique_inputs_200_seeds": unique_counts,
        "conclusions": [
            "self_check accepts two disconnected color-1 components despite the documented one-template invariant",
            "the authority selects the first color-1 object, while a natural all-color normalization consumes both",
            "easy generation fixes the key to color 3, so an always-union band shortcut fits all 200 sampled easy inputs",
        ],
    }
    (OUT / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    (OUT / "rival-output.json").write_text(json.dumps(report["all_color_cells_rival_output"], indent=2) + "\n")
    (OUT / "probe-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
