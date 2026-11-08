#!/usr/bin/env python3
"""Source-bound ambiguity probe for cf0dd146ab42 generated lessons.

The declared canonical map uses codes 1..6.  This probe evaluates a plausible
finite rival that agrees with the public canonical examples (which use only
codes 2, 3, and 4) but treats the newly introduced 5/6 codes as identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_sha(grid: list[list[int]]) -> str:
    return sha_bytes(json.dumps(grid, separators=(",", ":")).encode())


def code_of(grid: list[list[int]]) -> int:
    return next(value for value in grid[0] if value != 0)


def crop_object(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (r, c)
        for r in range(1, len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] != 0
    ]
    if not cells:
        return [[0]]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return grid[::-1]


def canonical(grid: list[list[int]]) -> list[list[int]]:
    obj = crop_object(grid)
    code = code_of(grid)
    return {
        1: obj,
        2: rotate_cw(obj),
        3: rotate_180(obj),
        4: rotate_ccw(obj),
        5: flip_lr(obj),
        6: flip_ud(obj),
    }.get(code, obj)


def rival_identity_for_5_and_6(grid: list[list[int]]) -> list[list[int]]:
    code = code_of(grid)
    return crop_object(grid) if code in (5, 6) else canonical(grid)


def pair_record(pair: dict[str, Any]) -> dict[str, Any]:
    inp, expected = pair["input"], pair["output"]
    can = canonical(inp)
    rival = rival_identity_for_5_and_6(inp)
    return {
        "code": code_of(inp),
        "input_sha256": grid_sha(inp),
        "expected_sha256": grid_sha(expected),
        "canonical_matches_expected": can == expected,
        "rival_matches_expected": rival == expected,
        "canonical_output": can,
        "rival_output": rival,
    }


def load_canonical_pairs(path: Path, task_id: str) -> list[dict[str, Any]]:
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return [*row.get("train", []), *row.get("test", [])]
    raise KeyError(task_id)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--canonical-data", type=Path, required=True)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--input-out", type=Path, required=True)
    parser.add_argument("--racket", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.episodes.read_text().splitlines() if line.strip()]
    stats = Counter()
    candidates: list[tuple[dict[str, Any], dict[str, Any]]] = []
    unique_demo_counts = Counter()
    for episode in rows:
        demos = episode["train"]
        query = episode["test"][0]
        demo_codes = [code_of(pair["input"]) for pair in demos]
        query_code = code_of(query["input"])
        unique_demo_counts[len(set(demo_codes))] += 1
        stats["episodes"] += 1
        if query_code not in demo_codes:
            stats["query_code_unseen_in_demos"] += 1
        rival_fits_demos = all(
            rival_identity_for_5_and_6(pair["input"]) == pair["output"]
            for pair in demos
        )
        rival_differs_query = (
            rival_identity_for_5_and_6(query["input"]) != query["output"]
        )
        if query_code in (5, 6):
            stats["query_code_5_or_6"] += 1
        if all(code in (1, 2, 3, 4) for code in demo_codes):
            stats["all_demo_codes_1_to_4"] += 1
        if query_code in (5, 6) and rival_fits_demos and rival_differs_query:
            stats["identity_5_6_rival_ambiguous_lessons"] += 1
            clean_unseen = all(code in (1, 2, 3, 4) for code in demo_codes)
            if clean_unseen:
                stats["identity_5_6_rival_ambiguous_with_no_5_6_demo"] += 1
            candidates.append((clean_unseen, episode, query))

    if not candidates:
        raise SystemExit("no identity-5/6 ambiguity candidate found")
    # Prefer the simplest witness: no demonstration uses either newly added code.
    _clean_unseen, episode, query = sorted(
        candidates, key=lambda item: (not item[0], item[1]["episode_index"])
    )[0]
    args.input_out.write_text(json.dumps(query["input"], indent=2) + "\n")

    canonical_pairs = load_canonical_pairs(args.canonical_data, "cf0dd146ab42")
    canonical_records = [pair_record(pair) for pair in canonical_pairs]
    demo_records = [pair_record(pair) for pair in episode["train"]]
    query_record = pair_record(query)

    racket_record = None
    racket_output = None
    if args.racket:
        racket_record = json.loads(args.racket.read_text())
        racket_output = racket_record["results"][0]["output"]

    result: dict[str, Any] = {
        "schema": "cf0dd146ab42-lesson-ambiguity-v1",
        "generator": {
            "path": str(args.generator),
            "sha256": sha_bytes(args.generator.read_bytes()),
        },
        "episode_source": {
            "path": str(args.episodes),
            "sha256": sha_bytes(args.episodes.read_bytes()),
            "episodes": len(rows),
        },
        "aggregate": {
            **dict(stats),
            "unique_demo_code_count_histogram": dict(sorted(unique_demo_counts.items())),
        },
        "rival": {
            "name": "identity_for_codes_5_and_6",
            "definition": (
                "Apply the canonical mappings for 1..4, but interpret newly introduced "
                "codes 5 and 6 as identity."
            ),
            "fits_all_five_canonical_pairs": all(
                record["rival_matches_expected"] for record in canonical_records
            ),
            "canonical_pair_codes": [record["code"] for record in canonical_records],
        },
        "counterexample": {
            "seed": episode["seed"],
            "episode_index": episode["episode_index"],
            "sample_indices": episode["sample_indices"],
            "executed_rule_hash": episode["executed_rule_hash"],
            "generator_sha256_from_episode": episode["provenance"]["generator_sha256"],
            "demo_codes": [record["code"] for record in demo_records],
            "query_code": query_record["code"],
            "rival_fits_every_demo": all(record["rival_matches_expected"] for record in demo_records),
            "canonical_matches_every_demo": all(record["canonical_matches_expected"] for record in demo_records),
            "canonical_matches_query_label": query_record["canonical_matches_expected"],
            "rival_differs_on_query": not query_record["rival_matches_expected"],
            "input_sha256": query_record["input_sha256"],
            "query_input": query["input"],
            "canonical_output": query_record["canonical_output"],
            "rival_output": query_record["rival_output"],
            "canonical_output_sha256": grid_sha(query_record["canonical_output"]),
            "rival_output_sha256": grid_sha(query_record["rival_output"]),
        },
        "canonical_pairs": canonical_records,
        "episode_demos": demo_records,
    }
    if racket_record is not None:
        result["counterexample"].update({
            "racket_output": racket_output,
            "racket_matches_canonical": racket_output == query_record["canonical_output"],
            "racket_differs_from_rival": racket_output != query_record["rival_output"],
            "racket_output_sha256": grid_sha(racket_output),
            "racket_generator_domain": racket_record["results"][0].get("generator_domain"),
        })
        result["racket_receipt"] = {
            "path": str(args.racket),
            "sha256": sha_bytes(args.racket.read_bytes()),
            "command": racket_record.get("command"),
        }

    ok = bool(
        result["rival"]["fits_all_five_canonical_pairs"]
        and result["counterexample"]["rival_fits_every_demo"]
        and result["counterexample"]["canonical_matches_query_label"]
        and result["counterexample"]["rival_differs_on_query"]
        and (racket_record is None or result["counterexample"]["racket_matches_canonical"])
    )
    result["finding_reproduced"] = ok
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "finding_reproduced": ok,
        "aggregate": result["aggregate"],
        "counterexample": {
            key: result["counterexample"][key]
            for key in (
                "seed", "demo_codes", "query_code", "rival_fits_every_demo",
                "rival_differs_on_query", "canonical_output", "rival_output"
            )
        },
    }, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
