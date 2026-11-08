"""Independent oracle and distribution probe for f812a7b32f47.

This authoring helper derives outputs directly from the documented bbox rule.
It is supplementary test evidence; the canonical Racket program remains the
label authority.  It intentionally does not import production helper functions.
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

TASK = "f812a7b32f47"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=find_root(__file__))


def bbox(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value != 0]
    if not cells:
        raise ValueError("bbox is undefined for an all-zero grid")
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def intended_output(grid):
    """Independent Python statement of the selected Racket rule."""
    r0, c0, r1, c1 = bbox(grid)
    rows = [r for r in range(r0 + 1, r1) if grid[r][c0] == 2]
    cols = [c for c in range(c0 + 1, c1) if grid[r0][c] == 3]
    out = deepcopy(grid)
    for r in rows:
        for c in cols:
            out[r][c] = 7
    return out


def anywhere_marker_rival(grid):
    """Plausible wrong rule: use every non-corner 2-row and 3-column.

    The canonical demonstrations contain one color-2 bbox corner, so a literal
    scan-everywhere rule is already falsified there.  This stronger rival
    treats corners as frame anomalies but otherwise ignores which edge carries
    a marker.
    """
    r0, c0, r1, c1 = bbox(grid)
    corners = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
    rows = sorted({
        r for r, row in enumerate(grid)
        if any(value == 2 and (r, c) not in corners
               for c, value in enumerate(row))
    })
    cols = sorted({
        c for r, row in enumerate(grid) for c, value in enumerate(row)
        if value == 3 and (r, c) not in corners
    })
    out = deepcopy(grid)
    for r in rows:
        for c in cols:
            out[r][c] = 7
    return out


def observed(grid):
    """Recover the proposed exact axes from pixels, independently of production."""
    r0, c0, r1, c1 = bbox(grid)
    border = (
        list(grid[r0][c0:c1 + 1]) + list(grid[r1][c0:c1 + 1])
        + [grid[r][c0] for r in range(r0 + 1, r1)]
        + [grid[r][c1] for r in range(r0 + 1, r1)]
    )
    frame_candidates = [v for v in border if v not in (0, 2, 3)]
    if not frame_candidates:
        raise ValueError("no frame color")
    frame_color = Counter(frame_candidates).most_common(1)[0][0]
    n_top = sum(grid[r0][c] == 3 for c in range(c0 + 1, c1))
    n_left = sum(grid[r][c0] == 2 for r in range(r0 + 1, r1))
    off_axis = 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 2 and not (c == c0 and r0 < r < r1):
                off_axis += 1
            elif value == 3 and not (r == r0 and c0 < c < c1):
                off_axis += 1
    return {
        "frame_h": r1 - r0 + 1,
        "frame_w": c1 - c0 + 1,
        "frame_color": frame_color,
        "n_top": n_top,
        "n_left": n_left,
        "n_distractors": off_axis,
    }


def canonical_profiles():
    return {(len(pair["input"]), len(pair["input"][0]),
             len({v for row in pair["input"] for v in row}))
            for pair in canonical_pairs()}


def pinned_profile_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def explicit_witness():
    """Small legal input where the canonical rule and the anywhere rival disagree."""
    return [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 5, 3, 5, 3, 5, 5, 0],
        [0, 2, 0, 0, 0, 0, 3, 0],
        [0, 5, 0, 0, 0, 0, 5, 0],
        [0, 2, 0, 0, 0, 0, 5, 0],
        [0, 5, 2, 5, 5, 5, 5, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]


def audit(module, count):
    profiles = canonical_profiles()
    report = {
        "schema": "f812a7b32f47-independent-audit-v1",
        "version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "canonical_pairs": len(canonical_pairs()),
        "canonical_oracle_matches": sum(
            intended_output(p["input"]) == p["output"] for p in canonical_pairs()
        ),
        "canonical_self_check_failures": [
            {"split": p["split"], "pair_index": p["pair_index"],
             "errors": module.self_check(p["input"])}
            for p in canonical_pairs() if module.self_check(p["input"])
        ],
        "bands": {},
    }
    for band in ("easy", "medium", "hard"):
        grids = [module.generate(9000 + i, 17 * i + 3, difficulty=band)
                 for i in range(count)]
        stats = [observed(g) for g in grids]
        report["bands"][band] = {
            "samples": count,
            "self_check_failures": sum(bool(module.self_check(g)) for g in grids),
            "distinct_inputs": len({json.dumps(g, separators=(",", ":")) for g in grids}),
            "frame_heights": sorted({s["frame_h"] for s in stats}),
            "frame_widths": sorted({s["frame_w"] for s in stats}),
            "frame_colors": sorted({s["frame_color"] for s in stats}),
            "distractor_counts": sorted({s["n_distractors"] for s in stats}),
            "rival_disagreements": sum(
                intended_output(g) != anywhere_marker_rival(g) for g in grids
            ),
            "canonical_profile_hits": sum(
                (len(g), len(g[0]), len({v for row in g for v in row})) in profiles
                for g in grids
            ),
        }
    witness = explicit_witness()
    report["witness"] = {
        "input": witness,
        "intended": intended_output(witness),
        "anywhere_marker_rival": anywhere_marker_rival(witness),
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.count)
    source = args.generator or ROOT / f"generators/{TASK}/generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"bands": report["bands"],
                      "canonical_self_check_failures": report["canonical_self_check_failures"]},
                     indent=2))
    return int(bool(report["canonical_self_check_failures"])
               or any(v["self_check_failures"] for v in report["bands"].values()))


if __name__ == "__main__":
    raise SystemExit(main())
