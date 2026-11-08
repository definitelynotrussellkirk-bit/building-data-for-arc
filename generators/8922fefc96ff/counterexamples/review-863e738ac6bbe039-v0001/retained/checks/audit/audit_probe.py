from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load(task: str):
    path = REPO / "generators" / task / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def span_truth(grid):
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        cols = [c for c, value in enumerate(row) if value == 7]
        if len(cols) == 2 and all(row[c] == 0 for c in range(cols[0] + 1, cols[1])):
            for c in range(cols[0], cols[1] + 1):
                out[r][c] = 7
    return out


def span_rival_ignore_blockers(grid):
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        cols = [c for c, value in enumerate(row) if value == 7]
        if len(cols) == 2:
            for c in range(cols[0], cols[1] + 1):
                out[r][c] = 7
    return out


def blocked_rows(grid):
    count = 0
    for row in grid:
        cols = [c for c, value in enumerate(row) if value == 7]
        if len(cols) == 2 and any(row[c] != 0 for c in range(cols[0] + 1, cols[1])):
            count += 1
    return count


def three_plus_rows(grid):
    return sum(sum(value == 7 for value in row) >= 3 for row in grid)


def norm(cells: Iterable[tuple[int, int]]):
    cells = list(cells)
    if not cells:
        return tuple()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def rot(cells):
    cells = norm(cells)
    if not cells:
        return cells
    h = 1 + max(r for r, _ in cells)
    return norm((c, h - 1 - r) for r, c in cells)


def refl(cells):
    cells = norm(cells)
    if not cells:
        return cells
    w = 1 + max(c for _, c in cells)
    return norm((r, w - 1 - c) for r, c in cells)


def variants(cells):
    cur = norm(cells)
    out = set()
    for _ in range(4):
        out.add(norm(cur))
        out.add(norm(refl(cur)))
        cur = rot(cur)
    return out


def split_panels(grid):
    h, w = len(grid), len(grid[0])
    divs = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    spans = []
    start = 0
    c = 0
    while c < w:
        if c in divs:
            if start < c:
                spans.append((start, c))
            while c < w and c in divs:
                c += 1
            start = c
        else:
            c += 1
    if start < w:
        spans.append((start, w))
    panels = []
    for lo, hi in spans:
        cells = [(r, c - lo) for r in range(h) for c in range(lo, hi) if grid[r][c] not in (0, 9)]
        panels.append(norm(cells))
    return panels


def dihedral_truth(grid):
    panels = split_panels(grid)
    return [
        [8 if panels[c] in variants(panels[r]) else 0 for c in range(len(panels))]
        for r in range(len(panels))
    ]


def diagonal_rival(grid):
    n = len(split_panels(grid))
    return [[8 if r == c else 0 for c in range(n)] for r in range(n)]


def audit_span(per_band=600, lessons=200):
    task = "8922fefc96ff"
    gen, path = load(task)
    report = {
        "schema": "audit-sampler-probe-v1",
        "task_id": task,
        "generator_sha256": sha(path),
        "sampler": {"seeds": "10000+i", "sample_index": "i", "per_band": per_band},
        "bands": {},
    }
    for band in ("easy", "medium", "hard"):
        stats = Counter()
        grids = []
        for i in range(per_band):
            grid = gen.generate(10000 + i, i, difficulty=band)
            grids.append(grid)
            stats["draws"] += 1
            stats["self_check_failures"] += int(bool(gen.self_check(grid)))
            stats["blocked_draws"] += int(blocked_rows(grid) > 0)
            stats["three_plus_draws"] += int(three_plus_rows(grid) > 0)
            stats["rival_fits"] += int(span_rival_ignore_blockers(grid) == span_truth(grid))
        ambiguous = 0
        for start in range(lessons):
            demos = [grids[(start * 7 + j) % per_band] for j in range(4)]
            if all(span_rival_ignore_blockers(g) == span_truth(g) for g in demos):
                ambiguous += 1
        stats["four_demo_windows"] = lessons
        stats["four_demo_rival_survivors"] = ambiguous
        report["bands"][band] = dict(stats)
    witness = gen.generate(0, 0, texture="span_already_filled")
    report["declared_counterexample"] = {
        "seed": 0,
        "sample_index": 0,
        "overrides": {"texture": "span_already_filled"},
        "self_check": gen.self_check(witness),
        "input_path": f"checks/audit/{task}/input.json",
        "truth_equals_rival": span_truth(witness) == span_rival_ignore_blockers(witness),
    }
    (PACKET / "checks" / "audit" / task / "input.json").write_text(
        json.dumps(witness, separators=(",", ":")) + "\n"
    )
    return report


def audit_panels(per_band=600, lessons=200):
    task = "35c7e1c0d116"
    gen, path = load(task)
    report = {
        "schema": "audit-sampler-probe-v1",
        "task_id": task,
        "generator_sha256": sha(path),
        "sampler": {"seeds": "20000+i", "sample_index": "i", "per_band": per_band},
        "bands": {},
    }
    representative = None
    for band in ("easy", "medium", "hard"):
        stats = Counter()
        grids = []
        for i in range(per_band):
            seed = 20000 + i
            grid = gen.generate(seed, i, difficulty=band)
            grids.append(grid)
            truth = dihedral_truth(grid)
            panels = split_panels(grid)
            offdiag = sum(truth[r][c] == 8 for r in range(len(truth)) for c in range(len(truth)) if r != c)
            stats["draws"] += 1
            stats["self_check_failures"] += int(bool(gen.self_check(grid)))
            stats["diagonal_only_outputs"] += int(offdiag == 0)
            stats["outputs_with_offdiagonal_match"] += int(offdiag > 0)
            stats["draws_with_empty_panel"] += int(any(not panel for panel in panels))
            if representative is None and band == "medium" and offdiag == 0 and not gen.self_check(grid):
                representative = (seed, i, grid, truth)
        ambiguous = 0
        for start in range(lessons):
            demos = [grids[(start * 7 + j) % per_band] for j in range(4)]
            if all(diagonal_rival(g) == dihedral_truth(g) for g in demos):
                ambiguous += 1
        stats["four_demo_windows"] = lessons
        stats["four_demo_diagonal_rival_survivors"] = ambiguous
        report["bands"][band] = dict(stats)
    if representative is None:
        raise RuntimeError("no diagonal-only representative found")
    seed, index, witness, truth = representative
    report["representative_shortcut_survivor"] = {
        "seed": seed,
        "sample_index": index,
        "difficulty": "medium",
        "self_check": gen.self_check(witness),
        "input_path": f"checks/audit/{task}/input.json",
        "independent_output": truth,
        "diagonal_rival_output": diagonal_rival(witness),
    }
    (PACKET / "checks" / "audit" / task / "input.json").write_text(
        json.dumps(witness, separators=(",", ":")) + "\n"
    )
    return report


if __name__ == "__main__":
    span = audit_span()
    panels = audit_panels()
    for report in (span, panels):
        task = report["task_id"]
        out = PACKET / "checks" / "audit" / task / "probe.json"
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(task, json.dumps(report["bands"], sort_keys=True))
