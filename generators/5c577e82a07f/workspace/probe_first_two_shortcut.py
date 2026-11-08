#!/usr/bin/env python3
"""Source-bound probe for the canonical two-color scope shortcut.

The wrong rule completes only the two lowest-valued rectangle colors. It fits
all canonical pairs because they contain exactly two colors. This probe checks
whether any ordinary three-demo lesson lets that rule fit every demonstration
but disagree with the held-out query.

Run from the repository root, for example:

    python3 generators/5c577e82a07f/workspace/probe_first_two_shortcut.py \
        --seeds 100 --starts 24 --out ../checks/first-two-shortcut.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "5c577e82a07f"
HERE = Path(__file__).resolve()
GENERATOR_PATH = HERE.parents[1] / "generator.py"
REPO_ROOT = HERE.parents[3]
RUNTIME = REPO_ROOT / "shared" / "runtime"
for path in (str(RUNTIME), str(REPO_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"_probe_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def _sha(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _pair(gen, rival, seed: int, sample_index: int, difficulty: str) -> dict[str, Any]:
    source = gen.generate(seed, sample_index, difficulty=difficulty)
    truth = gen.rule_mirror(source)
    guess = rival(source)
    return {
        "sample_index": sample_index,
        "n_rects": gen.semantic_observables(source)["n_rects"],
        "input_sha256": _sha(source),
        "truth_sha256": _sha(truth),
        "rival_sha256": _sha(guess),
        "rival_matches": _normalize(guess) == _normalize(truth),
        "input": source,
        "truth": truth,
        "rival": guess,
    }


def run(seeds: int, starts: int, difficulty: str) -> dict[str, Any]:
    gen = _load_generator()
    try:
        rival = gen.CANONICAL_SHORTCUTS["first_two_colors_only"]
    except (AttributeError, KeyError) as exc:
        raise RuntimeError(
            "generator must declare CANONICAL_SHORTCUTS['first_two_colors_only']"
        ) from exc

    from reviewer_support import canonical_pairs, find_root

    canonicals = canonical_pairs(TASK_ID, root=find_root(__file__))
    canonical_rows = []
    for index, pair in enumerate(canonicals):
        predicted = rival(pair["input"])
        canonical_rows.append(
            {
                "index": index,
                "input_sha256": _sha(pair["input"]),
                "fits": _normalize(predicted) == _normalize(pair["output"]),
                "n_rects": gen.semantic_observables(pair["input"])["n_rects"],
            }
        )

    counts = {"refuted": 0, "survived_all": 0, "query_discriminates": 0}
    first_by_status: dict[str, Any] = {}
    n_rect_windows: dict[str, int] = {}
    for seed in range(seeds):
        for start in range(starts):
            pairs = [
                _pair(gen, rival, seed, start + offset, difficulty)
                for offset in range(4)
            ]
            demo_matches = [pair["rival_matches"] for pair in pairs[:3]]
            query_matches = pairs[3]["rival_matches"]
            if not all(demo_matches):
                status = "refuted"
            elif query_matches:
                status = "survived_all"
            else:
                status = "query_discriminates"
            counts[status] += 1
            signature = ",".join(str(pair["n_rects"]) for pair in pairs)
            n_rect_windows[signature] = n_rect_windows.get(signature, 0) + 1
            first_by_status.setdefault(
                status,
                {
                    "seed": seed,
                    "start": start,
                    "n_rects": [pair["n_rects"] for pair in pairs],
                    "pairs": pairs,
                },
            )

    total = seeds * starts
    generator_sha = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    return {
        "schema": "arc-task-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(REPO_ROOT)),
        "generator_sha256": generator_sha,
        "generator_version": gen.VERSION,
        "difficulty": difficulty,
        "lesson_policy": "three consecutive demos followed by one consecutive query",
        "seed_range": [0, seeds - 1] if seeds else [],
        "start_range": [0, starts - 1] if starts else [],
        "windows": total,
        "canonical": {
            "pairs": len(canonical_rows),
            "fits_all": all(row["fits"] for row in canonical_rows),
            "rows": canonical_rows,
        },
        "status_counts": counts,
        "query_discrimination_rate": counts["query_discriminates"] / total if total else None,
        "n_rect_window_counts": dict(sorted(n_rect_windows.items())),
        "first_by_status": first_by_status,
        "pass": bool(canonical_rows)
        and all(row["fits"] for row in canonical_rows)
        and counts["query_discriminates"] == 0,
        "limits": [
            "Finite deterministic census, not proof against undeclared rivals.",
            "Only ordinary unoverridden lessons in the selected difficulty are sampled.",
            "A survived_all result can be answer-equivalent on an all-two-color lesson.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--starts", type=int, default=24)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds < 1 or args.starts < 1:
        parser.error("--seeds and --starts must be positive")
    report = run(args.seeds, args.starts, args.difficulty)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    print(
        json.dumps(
            {
                "windows": report["windows"],
                "status_counts": report["status_counts"],
                "canonical_fits_all": report["canonical"]["fits_all"],
                "pass": report["pass"],
            },
            sort_keys=True,
        ),
        file=sys.stderr,
    )
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
