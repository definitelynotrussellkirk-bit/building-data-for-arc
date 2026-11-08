"""Exhaustive diagnostic path census; never consults any solve directory.

Counts occupied-support paths once modulo reversal, but not modulo board
symmetry or translation. Seed 2 is always at the raster-later endpoint, so the
raster_seed_order rival necessarily disagrees. No random seeds are used.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, deque
import hashlib
import heapq
import json
import math
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import probe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-length", type=int, default=20)
    parser.add_argument("--verify-probe", action="store_true", help="Check every fast all-five classification against existing probe.py rivals.")
    parser.add_argument("--out", type=Path, default=Path("checks/semantic-review/even-length/census.json"))
    args = parser.parse_args()
    height, width = 5, 6
    count = height * width
    points = [(r, c) for r in range(height) for c in range(width)]
    bits = [1 << i for i in range(count)]
    nbr = [[j for j, p in enumerate(points) if abs(p[0]-q[0]) + abs(p[1]-q[1]) == 1] for q in points]
    nbr_masks = [sum(bits[j] for j in row) for row in nbr]
    nbr8 = [[(j, math.sqrt(2) if abs(p[0]-q[0]) == abs(p[1]-q[1]) == 1 else 1.)
             for j, p in enumerate(points) if j != i and max(abs(p[0]-q[0]), abs(p[1]-q[1])) == 1]
            for i, q in enumerate(points)]
    names = ("bfs8", "diagonal_euclidean", "raster_seed_order", "turn_penalty_half", "turn_discount_half")
    counts = {n: Counter() for n in range(7, args.max_length + 1)}
    witnesses = {n: [] for n in counts}
    path = []
    turns = []
    started = time.monotonic()

    def diagonal_refutes(mask, n, weighted):
        all_dist = []
        for start in (path[0], path[-1]):
            dist = [math.inf] * count
            dist[start] = 0.
            queue = [(0., start)]
            while queue:
                d, u = heapq.heappop(queue)
                if d != dist[u]:
                    continue
                for v, cost in nbr8[u]:
                    if mask & bits[v]:
                        alt = d + (cost if weighted else 1.)
                        if alt < dist[v]:
                            dist[v] = alt
                            heapq.heappush(queue, (alt, v))
            all_dist.append(dist)
        a, b = all_dist
        for i in range(1, n - 1):
            expected = 2*i - n + 1
            actual = a[path[i]] - b[path[i]]
            actual_sign = -1 if actual < -1e-8 else 1 if actual > 1e-8 else 0
            expected_sign = -1 if expected < 0 else 1 if expected > 0 else 0
            if actual_sign != expected_sign:
                return True
        return False

    def record(mask):
        n = len(path)
        ctr = counts[n]
        ctr["supports"] += 1
        middle = n // 2
        if n % 2:
            imbalance = bisect_left(turns, middle) - (len(turns) - bisect_right(turns, middle))
            both_turns = imbalance != 0
        else:
            left = bisect_left(turns, middle-1) - (len(turns) - bisect_right(turns, middle-1))
            right = bisect_left(turns, middle) - (len(turns) - bisect_right(turns, middle))
            both_turns = left >= 2 or right <= -2
        if both_turns:
            ctr["both_half_turn_rivals"] += 1
        plus_bfs8 = both_turns and diagonal_refutes(mask, n, False)
        if plus_bfs8:
            ctr["both_turns_and_bfs8"] += 1
        all_five = plus_bfs8 and diagonal_refutes(mask, n, True)
        if args.verify_probe:
            check_grid = probe.make_path([points[i] for i in path], (height, width))
            check_expected = probe.bfs4(check_grid)
            native_result = all(probe.RIVALS[name](check_grid) != check_expected for name in names)
            assert all_five == native_result, (list(path), all_five, native_result)
            ctr["existing_probe_crosschecks"] += 1
        if not all_five:
            return
        ctr["all_five_canonical_fitting_rivals"] += 1
        grid = probe.make_path([points[i] for i in path], (height, width))
        expected = probe.bfs4(grid)
        remaining = ("manhattan", "euclidean_squared", "chebyshev", "turn_penalty_one")
        all_nine = all(probe.RIVALS[name](grid) != expected for name in remaining)
        if all_nine:
            ctr["all_nine_rivals"] += 1
        keep = len(witnesses[n]) < 2 or (all_nine and not any(w["all_nine"] for w in witnesses[n]))
        if keep:
            diffs = {name: probe.mismatch(fn(grid), expected) for name, fn in probe.RIVALS.items()}
            assert all(diffs[name] for name in names)
            assert all_nine == all(diffs.values())
            witnesses[n].append({"all_nine": all_nine, "path": [points[i] for i in path],
                                 "input": grid, "python_bfs4_diagnostic_output": expected,
                                 "rival_differences": diffs})

    def walk(at, mask, direction):
        length = len(path)
        if length >= 7 and path[0] > at:
            record(mask)
        if length == args.max_length:
            return
        for nxt in nbr[at]:
            if not mask & bits[nxt] and nbr_masks[nxt] & mask == bits[at]:
                next_direction = (points[nxt][0]-points[at][0], points[nxt][1]-points[at][1])
                turning = direction is not None and direction != next_direction
                if turning:
                    turns.append(length-1)
                path.append(nxt)
                walk(nxt, mask | bits[nxt], next_direction)
                path.pop()
                if turning:
                    turns.pop()

    for start in range(count):
        path.append(start)
        walk(start, bits[start], None)
        path.pop()
        print(json.dumps({"start_completed": start, "elapsed_seconds": round(time.monotonic()-started, 3),
                          "counts": counts}), flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    result = {"grid_shape": [height, width], "max_length": args.max_length,
              "exhaustive": True, "seed_range": None, "every_classification_checked_against_probe": args.verify_probe,
              "count_convention": "Every induced support exactly once; fixed board coordinates; seed2 at raster-later endpoint.",
              "probe_sha256": hashlib.sha256(Path(probe.__file__).read_bytes()).hexdigest(),
              "census_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "elapsed_seconds": time.monotonic()-started, "counts": counts, "witnesses": witnesses}
    args.out.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"out": str(args.out), "elapsed_seconds": result["elapsed_seconds"], "counts": counts}), flush=True)


if __name__ == "__main__":
    main()
