"""Independent oracle and repeatable audit for task e73c86cb45ad.

The Python oracle is review evidence, not label authority. ``--racket`` stages
and executes the selected canonical Racket program and never silently falls
back to the Python implementation.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

TASK = "e73c86cb45ad"
HOME = Path(__file__).resolve().parents[1]
from reviewer_support import canonical_pairs as load_canonical_pairs, canonical_path, find_root
ROOT = find_root(__file__)
# Standalone script execution puts only this workspace on sys.path. Add the
# repository root so puzzle_generators.rule_wrap can import repo-local scripts.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_generator(path=None):
    path = Path(path or HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError("canonical task is absent")


def canonical_pairs():
    return load_canonical_pairs(TASK, root=ROOT)


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, tuple(sorted(cells))))
    return result


def norm(cells):
    cells = tuple(cells)
    if not cells:
        raise ValueError("shape must contain at least one cell")
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def rotate(shape):
    shape = norm(shape)
    height = max(r for r, _ in shape) + 1
    return norm((c, height - 1 - r) for r, c in shape)


def rotations(shape):
    values = []
    current = norm(shape)
    for _ in range(4):
        values.append(current)
        current = rotate(current)
    return tuple(values)


def bbox(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def analyze(grid):
    h = len(grid)
    w = len(grid[0])
    target = grid[0][w - 1]
    objs = [
        (color, cells)
        for color, cells in components(grid)
        if not (len(cells) == 1 and cells[0] == (0, w - 1))
    ]
    refs = [(color, cells) for color, cells in objs if color == 1]
    if not refs:
        raise ValueError("no color-1 reference")
    ref = max(refs, key=lambda item: (len(item[1]), tuple(-v for v in bbox(item[1])[:2])))
    candidates = sorted(
        [(color, cells) for color, cells in objs if (color, cells) != ref],
        key=lambda item: bbox(item[1])[:2],
    )
    ref_rots = set(rotations(ref[1]))
    matches = [item for item in candidates if norm(item[1]) in ref_rots]
    return {
        "height": h,
        "width": w,
        "target": target,
        "reference": ref,
        "candidates": candidates,
        "matches": matches,
    }


def crop_recolor(cells, color):
    r1, c1, r2, c2 = bbox(cells)
    occupied = set(cells)
    return [
        [color if (r, c) in occupied else 0 for c in range(c1, c2 + 1)]
        for r in range(r1, r2 + 1)
    ]


def rule_output(grid):
    info = analyze(grid)
    if not info["matches"]:
        raise ValueError("no rotation-equivalent candidate")
    return crop_recolor(info["matches"][0][1], info["target"])


def first_candidate_output(grid):
    info = analyze(grid)
    if not info["candidates"]:
        raise ValueError("no candidate")
    return crop_recolor(info["candidates"][0][1], info["target"])


def observed(grid):
    info = analyze(grid)
    if len(info["matches"]) != 1:
        raise ValueError(f"expected one match, found {len(info['matches'])}")
    ref_shape = norm(info["reference"][1])
    match_shape = norm(info["matches"][0][1])
    turns = [index for index, shape in enumerate(rotations(ref_shape)) if shape == match_shape]
    if len(turns) != 1:
        raise ValueError(f"rotation is not uniquely recoverable: {turns}")
    match_index = info["candidates"].index(info["matches"][0])
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "shape_size": len(info["reference"][1]),
        "match_rotation": turns[0],
        "match_order": "first" if match_index == 0 else "later",
        "n_distractors": len(info["candidates"]) - 1,
    }


def _install_rule_wrap_compat():
    """Expose the packet's parser under the legacy scripts package name.

    The stripped review packet stores comment_solutions.py in shared/tools,
    while puzzle_generators.rule_wrap still imports scripts.comment_solutions.
    Installing this explicit alias keeps the probe standalone without changing
    shared runtime code or silently replacing the Racket authority.
    """
    if "scripts.comment_solutions" in sys.modules:
        return
    source = ROOT / "shared" / "tools" / "comment_solutions.py"
    if not source.is_file():
        raise FileNotFoundError(f"missing rule-wrap parser: {source}")
    package = sys.modules.get("scripts")
    if package is None:
        package = types.ModuleType("scripts")
        package.__path__ = [str(source.parent)]
        sys.modules["scripts"] = package
    spec = importlib.util.spec_from_file_location("scripts.comment_solutions", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["scripts.comment_solutions"] = module
    spec.loader.exec_module(module)


def racket_outputs(grids):
    """Execute the selected Racket authority; never fall back to Python."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    _install_rule_wrap_compat()
    from puzzle_generators import runner

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    bridge, name = runner._open_bridge_with_rule(
        runner.wrap_rule(canonical()["program_solution"])
    )
    try:
        return [runner._apply_rule(bridge, name, grid) for grid in grids]
    finally:
        bridge.close()


def audit(module, sample_count):
    canonical_rows = canonical_pairs()
    report = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "canonical_count": len(canonical_rows),
        "canonical_python_mismatches": [],
        "canonical_self_check_errors": [],
        "by_band": {},
    }
    for index, pair in enumerate(canonical_rows):
        if rule_output(pair["input"]) != pair["output"]:
            report["canonical_python_mismatches"].append(index)
        issues = module.self_check(deepcopy(pair["input"]))
        if issues:
            report["canonical_self_check_errors"].append({"index": index, "issues": issues})

    sampled = []
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        inputs = set()
        rotations_seen = set()
        sizes_seen = set()
        for index in range(sample_count):
            grid = module.generate(1000 + index, index * 7 + 3, difficulty=band)
            sampled.append(grid)
            issues = module.self_check(grid)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(issues)
            counts["nondeterministic"] += grid != module.generate(
                1000 + index, index * 7 + 3, difficulty=band
            )
            stats = observed(grid)
            rotations_seen.add(stats["match_rotation"])
            sizes_seen.add(stats["shape_size"])
            counts[f"order_{stats['match_order']}"] += 1
            counts["first_candidate_rival_disagreements"] += (
                rule_output(grid) != first_candidate_output(grid)
            )
            inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
        report["by_band"][str(band)] = {
            **dict(counts),
            "distinct_inputs": len(inputs),
            "rotations": sorted(rotations_seen),
            "shape_sizes": sorted(sizes_seen),
        }
    return report, [pair["input"] for pair in canonical_rows] + sampled[:64]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    path = args.generator or HOME / "generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["rule_hash"] = normalized_rule_hash(canonical()["program_solution"])
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        bool(report["canonical_python_mismatches"])
        or bool(report["canonical_self_check_errors"])
        or any(row.get("self_check_errors") or row.get("nondeterministic") for row in report["by_band"].values())
    )
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            mismatches = [
                index for index, (grid, output) in enumerate(zip(grids, outputs))
                if rule_output(grid) != output
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # explicit failure, never a fallback
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"version": report["version"], "by_band": report["by_band"], "racket": report["racket"]}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
