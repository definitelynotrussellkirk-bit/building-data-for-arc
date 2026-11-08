"""Independent oracle and source-bound probes for generator 691d467ddb4d.

This file is review tooling, not label authority.  The production labels remain
the canonical Racket program.  It deliberately reimplements component ranking
instead of importing generator helpers so tests can catch sampler/validator
coupling mistakes.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "691d467ddb4d"


def _bootstrap_runtime(start: Path) -> Path:
    """Locate reviewer_support without assuming this helper's nesting depth."""
    start = start.resolve()
    for candidate in (start, *start.parents):
        if (candidate / "shared/runtime/reviewer_support.py").is_file():
            return candidate
    raise FileNotFoundError(f"No shared/runtime/reviewer_support.py above {start}")


_BOOTSTRAP_ROOT = _bootstrap_runtime(Path(__file__).parent)
sys.path.insert(0, str(_BOOTSTRAP_ROOT / "shared/runtime"))
from reviewer_support import (  # noqa: E402
    canonical_pairs as read_canonical_pairs,
    canonical_path,
    find_root,
)

ROOT = find_root(__file__)
CANONICAL_FILE = canonical_path(ROOT)


def load_generator(path: str | Path | None = None):
    source = Path(path or ROOT / f"generators/{TASK_ID}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_691d467ddb4d", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    """Read labels from the nearest portable runtime/repository ledger."""
    # Resolve the path eagerly above so copied-runtime failures are explicit.
    if not CANONICAL_FILE.is_file():
        raise FileNotFoundError(CANONICAL_FILE)
    return read_canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def components(grid: list[list[int]], color: int = 4) -> list[list[tuple[int, int]]]:
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    point = rr + dr, cc + dc
                    if (0 <= point[0] < h and 0 <= point[1] < w
                            and point not in seen and grid[point[0]][point[1]] == color):
                        seen.add(point)
                        stack.append(point)
            found.append(sorted(comp))
    return found


def _rank(comp: list[tuple[int, int]]) -> tuple[int, int]:
    return min(c for _, c in comp), min(r for r, _ in comp)


def _paint_selected(grid: list[list[int]], selected: list[tuple[int, int]] | None) -> list[list[int]]:
    out = deepcopy(grid)
    if selected is not None:
        for r, c in selected:
            out[r][c] = 3
    return out


def canonical_output(grid: list[list[int]]) -> list[list[int]]:
    comps = components(grid)
    selected = min(comps, key=_rank) if comps else None
    return _paint_selected(grid, selected)


def border_touch_output(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: recolor a yellow object only if its min column is 0 or 1."""
    candidates = [comp for comp in components(grid) if _rank(comp)[0] <= 1]
    return _paint_selected(grid, min(candidates, key=_rank) if candidates else None)


def topmost_output(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: recolor the topmost yellow object, breaking ties leftward."""
    comps = components(grid)
    selected = min(comps, key=lambda comp: (min(r for r, _ in comp), min(c for _, c in comp))) if comps else None
    return _paint_selected(grid, selected)


def observed(grid: list[list[int]]) -> dict[str, int | bool]:
    comps = components(grid)
    left = min(comps, key=_rank)
    top = min(comps, key=lambda comp: (min(r for r, _ in comp), min(c for _, c in comp)))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_right": len(comps) - 1,
        "target_min_col": _rank(left)[0],
        "target_min_row": _rank(left)[1],
        "target_is_topmost": left == top,
    }


def census(module, *, draws_per_band: int = 200) -> dict:
    result = {
        "schema": "691d467ddb4d-review-census-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "draws_per_band": draws_per_band,
        "bands": {},
    }
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = Counter()
        hashes: set[str] = set()
        first_interior = None
        for index in range(draws_per_band):
            grid = module.generate(100_000 + band_index * 10_000 + index, index, difficulty=band)
            issues = module.self_check(grid)
            stats = observed(grid)
            counts["draws"] += 1
            counts["self_check_failures"] += bool(issues)
            counts[f"target_col_{stats['target_min_col']}"] += 1
            counts[f"n_right_{stats['n_right']}"] += 1
            counts["interior_targets"] += stats["target_min_col"] >= 2
            counts["leftmost_not_topmost"] += not stats["target_is_topmost"]
            digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            hashes.add(digest)
            if first_interior is None and stats["target_min_col"] >= 2:
                first_interior = {
                    "seed": 100_000 + band_index * 10_000 + index,
                    "sample_index": index,
                    "input_sha256": digest,
                    "stats": stats,
                    "grid": grid,
                }
        result["bands"][band] = {
            "counts": dict(sorted(counts.items())),
            "unique_inputs": len(hashes),
            "first_interior_witness": first_interior,
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws-per-band", type=int, default=200)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = census(load_generator(), draws_per_band=args.draws_per_band)
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
