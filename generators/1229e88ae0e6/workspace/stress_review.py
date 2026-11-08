"""Finite-domain and seeded stress checks; outputs are diagnostic, not Racket labels.

  python3 repo/generators/1229e88ae0e6/workspace/stress_review.py --out checks/stress.json
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

from review_probe import facts, load_generator, specification


def run(library: Path) -> dict:
    source = library / "generators/1229e88ae0e6/generator.py"
    gen = load_generator(library, source)
    started = time.monotonic()
    report = {"schema": "centering-stress-v1", "label_source": "independent_python_spec_not_Racket",
              "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "checks": {}, "failures": []}
    checked = report["checks"]

    def require(ok, label, context):
        if not ok:
            report["failures"].append({"check": label, "context": context})

    supports = set()
    support_counts = {}
    for bh in (2, 3):
        for bw in (2, 3):
            rows = []
            for n in range(3, 9):
                rows.extend(gen._motifs(bh, bw, n))
            require(len(rows) == len(set(rows)), "duplicate_support", [bh, bw])
            supports.update(rows)
            support_counts[f"{bh}x{bw}"] = len(rows)
    checked["support_catalog"] = support_counts
    checked["total_distinct_supports"] = len(supports)

    # Every noncentered placement of every support on each canonical canvas,
    # with one monochrome and one deterministic 3-color assignment.
    placements = 0
    for support in sorted(supports):
        bh = max(r for r, _ in support)+1
        bw = max(c for _, c in support)+1
        for h, w in sorted(gen._CANONICAL_SHAPES):
            for r0 in range(h-bh+1):
                for c0 in range(w-bw+1):
                    if (r0, c0) == ((h-bh)//2, (w-bw)//2):
                        continue
                    for multi in (False, True):
                        grid = [[0]*w for _ in range(h)]
                        for k, (r, c) in enumerate(support):
                            grid[r0+r][c0+c] = (k%3+1) if multi else 7
                        expected = specification(grid)
                        context = [h, w, r0, c0, support, multi]
                        require(not gen.self_check(grid), "exhaustive_selfcheck", context)
                        require(not gen.strict_canonical_like(grid), "exhaustive_strict", context)
                        require(gen.rule_mirror(grid) == expected, "exhaustive_spec", context)
                        actual_counts = Counter(v for row in expected for v in row if v)
                        original_counts = Counter(v for row in grid for v in row if v)
                        require(actual_counts == original_counts, "pixel_preservation", context)
                        placements += 1
    checked["exhaustive_colored_placements"] = placements

    override_count = 0
    for band in ("easy", "medium", "hard"):
        for zone in gen._ZONES:
            for mode in gen._COLOR_MODES:
                requested = {"source_zone": zone, "color_mode": mode}
                for seed in (0, 1, 31, -1, 2**63-1):
                    for i in range(8):
                        g = gen.generate(seed, i, difficulty=band, **requested)
                        context = [band, seed, i, requested]
                        require(gen.observe_overrides(g) == requested, "exact_override", context)
                        require(not gen.self_check(g, meta=requested), "override_selfcheck", context)
                        require(not gen.strict_canonical_like(g), "override_strict", context)
                        require(gen.rule_mirror(g) == specification(g), "override_spec", context)
                        override_count += 1
    checked["override_cases"] = override_count

    sample_count = window_count = 0
    witnesses, rival_kills = Counter(), Counter()
    for band in ("easy", "medium", "hard"):
        for seed in list(range(64)) + [-1, 2**31-1, 2**63, 2**63+3, 20260927]:
            grids = [gen.generate(seed, i, difficulty=band) for i in range(24)]
            pairs = [{"input": grid, "output": specification(grid)} for grid in grids]
            for i, pair in enumerate(pairs):
                require(gen.rule_mirror(pair["input"]) == pair["output"],
                        "seeded_spec", [band, seed, i])
                for name, fn in gen.SEMANTIC_WITNESSES.items():
                    witnesses[name] += bool(fn(pair["input"]))
                for name, fn in gen.SEMANTIC_RIVALS.items():
                    rival_kills[name] += fn(pair["input"]) != pair["output"]
            sample_count += len(pairs)
            for start in range(20):
                demos, query = pairs[start:start+4], pairs[start+4]
                require(not gen.lesson_identifiable(demos, query),
                        "sliding_lesson", [band, seed, start])
                for name, fn in gen.SEMANTIC_RIVALS.items():
                    require(any(fn(p["input"]) != p["output"] for p in demos),
                            "quartet_rival_survives", [name, band, seed, start])
                require(len({json.dumps(p["input"]) for p in demos+[query]}) == 5,
                        "episode_duplicate", [band, seed, start])
                window_count += 1
    checked.update({"seeded_samples": sample_count, "sliding_episodes": window_count,
                    "witness_fires": dict(witnesses), "rival_kills": dict(rival_kills)})

    metamorphic = Counter()
    for band in ("easy", "medium", "hard"):
        for i in range(128):
            g = gen.generate(20260927, i, difficulty=band)
            out = specification(g)
            transpose = lambda x: [list(row) for row in zip(*x)]
            recolor = lambda x: [[(v%9)+1 if v else 0 for v in row] for row in x]
            flip = lambda x: [row[::-1] for row in x]
            for name, operation in (("transpose", transpose), ("palette_permutation", recolor)):
                require(gen.rule_mirror(operation(g)) == operation(out), name, [band, i])
                metamorphic[name] += 1
            flipped = flip(g)
            if gen.self_check(flipped):
                # A flip can turn an off-center odd-slack source into an
                # already centered one. That is outside the teaching domain,
                # not a failure of centering. The independent spec handles it.
                metamorphic["horizontal_flip_left_teaching_domain"] += 1
            if specification(flipped) != flip(out):
                metamorphic["horizontal_flip_non_covariance_witnesses"] += 1
    checked["metamorphic"] = dict(metamorphic)
    report["elapsed_seconds"] = round(time.monotonic()-started, 3)
    report["passed"] = not report["failures"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.library)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
