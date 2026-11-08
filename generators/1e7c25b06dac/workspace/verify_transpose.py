"""Replay canonical labels and finite-rival four-query lessons with Racket.

Run from repo through the packet runner. This is an authoring check, not an
approval or a claim of unique rule identification against all programs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "1e7c25b06dac"
RIVALS = ("identity", "transpose_only", "lower_to_upper", "upper_to_lower",
          "anti_diagonal", "fixed_coordinates")


def rival(name, grid):
    n = len(grid)
    out = [row[:] for row in grid]
    if name == "identity":
        return out
    if name == "transpose_only":
        return [list(row) for row in zip(*grid)]
    if name == "fixed_coordinates":
        for r, c in ((3, 1), (4, 2), (n - 1, 1)):
            if 0 <= r < n and 0 <= c < n and not out[c][r]:
                out[c][r] = grid[r][c]
        return out
    for r in range(n):
        for c in range(n):
            if grid[r][c]:
                continue
            if name == "lower_to_upper" and not r < c:
                continue
            if name == "upper_to_lower" and not r > c:
                continue
            sr, sc = (n - 1 - c, n - 1 - r) if name == "anti_diagonal" else (c, r)
            out[r][c] = grid[sr][sc]
    return out


def literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def certify_lesson(pairs, n_train):
    demos, queries = pairs[:n_train], pairs[n_train:]
    rejected = {name: [i for i, p in enumerate(demos) if rival(name, p["input"]) != p["output"]]
                for name in RIVALS}
    checks = []
    for index, pair in enumerate(queries):
        differing = [name for name in RIVALS if rival(name, pair["input"]) != pair["output"]]
        unresolved = [name for name in differing if not rejected[name]]
        if unresolved:
            raise AssertionError(f"query {index} lacks demo evidence against {unresolved}")
        checks.append({"query_index": index, "query_disagreeing_rivals": differing,
                       "unresolved_rivals": unresolved})
    return {"rival_names": list(RIVALS), "demo_rejections": rejected,
            "query_checks": checks, "scope": "finite declared rivals; demos only"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--sizes", type=int, nargs="+", default=[3, 6, 20, 30])
    args = parser.parse_args()
    if not (1 <= args.demos <= 12 and 1 <= args.queries <= 12):
        parser.error("demo/query counts must each be in 1..12")
    if any(not 3 <= size <= 30 for size in args.sizes) or len(set(args.sizes)) != len(args.sizes):
        parser.error("sizes must be distinct integers in 3..30")
    if args.out.exists():
        parser.error("output must be new")
    root = find_root(__file__)
    generator, source, sha = load_selected_generator(TASK_ID, root=root)
    ledger = canonical_path(root)
    row = next(json.loads(line) for line in ledger.open() if json.loads(line).get("task_id") == TASK_ID)
    program = row["program_solution"]
    wrapped = wrap_rule(program)
    report = {"schema": "transpose-fill-focused-evidence-v1", "task_id": TASK_ID,
              "source_sha256": sha, "canonical_file_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
              "rule_program": program, "rule_sha256": hashlib.sha256(program.encode()).hexdigest(),
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "seed": args.seed, "canonical_checks": [], "lessons": [],
              "approval": "not granted; source-bound authoring evidence"}
    with RacketBridge() as bridge:
        report["runtime"] = {key: value for key, value in bridge.runtime_identity.items()
                             if key.endswith("sha256") or key in ("schema", "backend", "protected")}
        assert report["runtime"]["protected"] is True
        def apply(grid):
            return bridge.eval_text(f"({wrapped} {literal(grid)})")
        for pair in canonical_pairs(TASK_ID, root=root):
            assert not generator.self_check(pair["input"])
            assert apply(pair["input"]) == pair["output"]
            report["canonical_checks"].append({"split": pair["split"], "pair_index": pair["pair_index"], "exact": True})
        for size in args.sizes:
            pairs, indices, seen = [], [], set()
            for index in range(100 * (args.demos + args.queries)):
                grid = generator.generate(args.seed, index, grid_size=size)
                key = json.dumps(grid, separators=(",", ":"))
                if key in seen:
                    continue
                assert not generator.self_check(grid)
                seen.add(key)
                pairs.append({"input": grid, "output": apply(grid)})
                indices.append(index)
                if len(pairs) == args.demos + args.queries:
                    break
            if len(pairs) != args.demos + args.queries:
                raise RuntimeError("bounded distinct-input sampler exhausted")
            certificate = certify_lesson(pairs, args.demos)
            report["lessons"].append({"size": size, "accepted_sample_indices": indices,
                "n_train": args.demos, "n_test": args.queries,
                "train": pairs[:args.demos], "test": pairs[args.demos:], "certificate": certificate})
        # Occupied conflicting partners exercise the exact reference's preserve
        # branch. This is outside the ordinary sampler; do not call it coverage.
        boundary = [[0, 1, 0], [2, 0, 3], [0, 0, 4]]
        expected = [[0, 1, 0], [2, 0, 3], [0, 3, 4]]
        actual = apply(boundary)
        assert actual == expected and not generator.self_check(boundary)
        report["occupied_partner_boundary"] = {"input": boundary, "output": actual,
            "scope": "validator/reference only; not ordinary sampled support"}
    report["racket_labels_executed"] = len(report["canonical_checks"]) + sum(
        len(lesson["train"]) + len(lesson["test"]) for lesson in report["lessons"]) + 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"status": "pass", "canonical_pairs": len(report["canonical_checks"]),
        "sizes": args.sizes, "queries_per_lesson": args.queries,
        "racket_labels_executed": report["racket_labels_executed"], "out": str(args.out)}, sort_keys=True))


if __name__ == "__main__":
    main()
