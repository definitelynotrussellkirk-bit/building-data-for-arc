"""Independent oracle and distribution probe for prototype dictionary stamping.

This module is task-local test tooling.  It does not replace the canonical Racket
label authority.  The oracle is intentionally written without importing helpers
from the selected generator so it can detect generator-side semantic mistakes.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK = "5d3738a6b89c"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    """Load every canonical pair through the portable reviewer helper when present."""
    try:
        from reviewer_support import canonical_pairs as portable_pairs, find_root
    except ImportError:
        portable_pairs = None
    if portable_pairs is not None:
        return portable_pairs(TASK, root=find_root(__file__))
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                test = row["test"] if isinstance(row["test"], list) else [row["test"]]
                return list(row["train"]) + list(test)
    raise ValueError(f"canonical task {TASK} not found")


def parse(grid: list[list[int]]) -> dict:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected nonempty grid")
    width = len(grid[0])
    if not width or any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected rectangular grid")
    sep_rows = [r for r, row in enumerate(grid) if all(value == 9 for value in row)]
    if not sep_rows:
        raise ValueError("missing full color-9 separator row")
    sep = sep_rows[0]
    sep_cols = [c for c in range(width) if all(grid[r][c] == 9 for r in range(sep))]
    starts = [0] + [c + 1 for c in sep_cols]
    ends = sep_cols + [width]
    boxes = [(left, right) for left, right in zip(starts, ends) if right > left]
    prototypes = []
    for left, right in boxes:
        if right - left != 3 or sep < 3:
            raise ValueError("prototype boxes must be 3x3")
        key = grid[1][left + 1]
        offsets = []
        for r in range(3):
            for c in range(left, right):
                if grid[r][c] != 0:
                    offsets.append((r - 1, c - (left + 1)))
        prototypes.append({"left": left, "right": right, "key": key, "offsets": tuple(offsets)})
    key_set = {prototype["key"] for prototype in prototypes}
    anchors = {
        key: [(r, c) for r in range(sep + 1, len(grid)) for c in range(width) if grid[r][c] == key]
        for key in key_set
    }
    return {
        "height": len(grid), "width": width, "sep": sep, "sep_cols": sep_cols,
        "boxes": boxes, "prototypes": prototypes, "anchors": anchors,
    }


def reference_output(grid: list[list[int]], *, first_anchor_only: bool = False) -> list[list[int]]:
    """Independent Python transcription of the canonical stamping semantics."""
    info = parse(grid)
    lookup = {prototype["key"]: prototype["offsets"] for prototype in info["prototypes"]}
    remaining = set(lookup) if first_anchor_only else None
    out = deepcopy(grid)
    for r in range(info["sep"] + 1, info["height"]):
        for c in range(info["width"]):
            value = grid[r][c]
            if value not in lookup:
                continue
            if remaining is not None:
                if value not in remaining:
                    continue
                remaining.remove(value)
            for dr, dc in lookup[value]:
                rr, cc = r + dr, c + dc
                if rr >= info["sep"] + 1 and 0 <= rr < info["height"] and 0 <= cc < info["width"]:
                    out[rr][cc] = value
    return out


def observed(grid: list[list[int]]) -> dict:
    info = parse(grid)
    mask_sizes = {len(prototype["offsets"]) for prototype in info["prototypes"]}
    if len(mask_sizes) != 1:
        raise ValueError(f"prototype mask sizes differ: {sorted(mask_sizes)}")
    edge = any(
        r in (info["sep"] + 1, info["height"] - 1) or c in (0, info["width"] - 1)
        for anchors in info["anchors"].values() for r, c in anchors
    )
    return {
        "grid_h": info["height"],
        "n_boxes": len(info["boxes"]),
        "mask_size": next(iter(mask_sizes)),
        "edge_mode": "mixed" if edge else "interior",
    }



def clipping_surfaces(grid: list[list[int]]) -> set[str]:
    """Return semantic clipping surfaces exercised by actual anchor/mask pairs."""
    info = parse(grid)
    lookup = {prototype["key"]: prototype["offsets"] for prototype in info["prototypes"]}
    surfaces: set[str] = set()
    for key, anchors in info["anchors"].items():
        for row, column in anchors:
            for dr, dc in lookup[key]:
                rr, cc = row + dr, column + dc
                if rr < info["sep"] + 1:
                    surfaces.add("separator")
                if rr >= info["height"]:
                    surfaces.add("bottom")
                if cc < 0:
                    surfaces.add("left")
                if cc >= info["width"]:
                    surfaces.add("right")
    return surfaces


def outer_border_ignored_output(grid: list[list[int]]) -> list[list[int]]:
    """Rival that skips anchors on the outer left/right/bottom grid border."""
    info = parse(grid)
    lookup = {prototype["key"]: prototype["offsets"] for prototype in info["prototypes"]}
    out = deepcopy(grid)
    for row in range(info["sep"] + 1, info["height"]):
        for column in range(info["width"]):
            key = grid[row][column]
            if key not in lookup:
                continue
            if row == info["height"] - 1 or column in (0, info["width"] - 1):
                continue
            for dr, dc in lookup[key]:
                rr, cc = row + dr, column + dc
                if rr >= info["sep"] + 1 and 0 <= rr < info["height"] and 0 <= cc < info["width"]:
                    out[rr][cc] = key
    return out

def painted_footprints(grid: list[list[int]]) -> list[tuple[int, tuple[int, int], frozenset[tuple[int, int]]]]:
    info = parse(grid)
    lookup = {prototype["key"]: prototype["offsets"] for prototype in info["prototypes"]}
    result = []
    for key, anchors in info["anchors"].items():
        for anchor in anchors:
            cells = frozenset(
                (anchor[0] + dr, anchor[1] + dc)
                for dr, dc in lookup[key]
                if anchor[0] + dr >= info["sep"] + 1
                and 0 <= anchor[0] + dr < info["height"]
                and 0 <= anchor[1] + dc < info["width"]
            )
            result.append((key, anchor, cells))
    return result



def schedule_rotation_audit(module) -> dict:
    """Exhaust one declared period and hold out every labelled pair once."""
    report = {
        "period": module.LESSON_SCHEDULE_PERIOD,
        "examples_needed": module.EXAMPLES_NEEDED,
        "bands": {},
    }
    for band in (None, "easy", "medium", "hard"):
        checked = unwitnessed = hook_failures = 0
        for start in range(module.LESSON_SCHEDULE_PERIOD):
            episode = [
                module.generate(19_000, start + offset, difficulty=band)
                for offset in range(module.EXAMPLES_NEEDED + 1)
            ]
            for query_index, query_grid in enumerate(episode):
                demo_grids = [grid for index, grid in enumerate(episode) if index != query_index]
                demos = [{"input": grid, "output": reference_output(grid)} for grid in demo_grids]
                query = {"input": query_grid, "output": reference_output(query_grid)}
                checked += 1
                unwitnessed += not any(
                    outer_border_ignored_output(grid) != reference_output(grid)
                    for grid in demo_grids
                )
                hook_failures += bool(module.lesson_identifiable(demos, query))
        report["bands"]["default" if band is None else band] = {
            "rotations_checked": checked,
            "unwitnessed_rotations": unwitnessed,
            "lesson_hook_failures": hook_failures,
        }
    return report

def audit(module, count: int) -> dict:
    report: dict = {
        "schema": "5d3738a6b89c-independent-audit-v3",
        "version": module.VERSION,
        "canonical": [],
        "bands": {},
        "schedule_rotations": schedule_rotation_audit(module),
    }
    for index, pair in enumerate(canonical_pairs()):
        report["canonical"].append({
            "index": index,
            "self_check": module.self_check(pair["input"]),
            "oracle_matches": reference_output(pair["input"]) == pair["output"],
            "first_anchor_matches": reference_output(pair["input"], first_anchor_only=True) == pair["output"],
            "outer_border_rival_matches": outer_border_ignored_output(pair["input"]) == pair["output"],
        })
    for band in ("easy", "medium", "hard"):
        counts = Counter()
        shapes, masks, modes, boxes, hashes = set(), set(), set(), set(), set()
        for index in range(count):
            grid = module.generate(5000 + index, index * 13 + 1, difficulty=band)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(5000 + index, index * 13 + 1, difficulty=band)
            stats = observed(grid)
            shapes.add((len(grid), len(grid[0])))
            masks.add(stats["mask_size"]); modes.add(stats["edge_mode"]); boxes.add(stats["n_boxes"])
            counts["observed_mixed"] += stats["edge_mode"] == "mixed"
            hashes.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            intended = reference_output(grid)
            rival = reference_output(grid, first_anchor_only=True)
            counts["changed"] += intended != grid
            counts["first_anchor_rival_disagreements"] += intended != rival
            surfaces = clipping_surfaces(grid)
            counts["separator_clipping"] += "separator" in surfaces
            counts["outer_clipping"] += bool(surfaces & {"left", "right", "bottom"})
            counts["outer_border_rival_disagreements"] += intended != outer_border_ignored_output(grid)
            footprints = painted_footprints(grid)
            counts["overlap_cases"] += any(
                left[2] & right[2]
                for i, left in enumerate(footprints) for right in footprints[i + 1:]
            )
        report["bands"][band] = dict(
            counts,
            expected_mixed=counts["observed_mixed"],
            distinct_inputs=len(hashes),
            shapes=sorted(shapes),
            mask_sizes=sorted(masks),
            edge_modes=sorted(modes),
            n_boxes=sorted(boxes),
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=250)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.count)
    source = Path(args.generator or ROOT / f"generators/{TASK}/generator.py")
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    bad = any(
        item["self_check"]
        or not item["oracle_matches"]
        or not item["first_anchor_matches"]
        or not item["outer_border_rival_matches"]
        for item in report["canonical"]
    )
    bad |= any(
        data["self_check_errors"]
        or data["nondeterministic"]
        or data["overlap_cases"]
        or data["separator_clipping"] != data["expected_mixed"]
        or data["outer_clipping"] != data["expected_mixed"]
        or data["outer_border_rival_disagreements"] != data["expected_mixed"]
        for data in report["bands"].values()
    )
    bad |= any(
        data["unwitnessed_rotations"] or data["lesson_hook_failures"]
        for data in report["schedule_rotations"]["bands"].values()
    )
    return int(bad)


if __name__ == "__main__":
    raise SystemExit(main())
