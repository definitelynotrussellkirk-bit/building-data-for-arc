#!/usr/bin/env python3
"""Regenerate bounded authoring evidence for the orientation-selector family.

This is intentionally task-local.  It exercises the retained finite rival set,
checks that settings share inputs for equal requests, and writes opaque one-query
public projections whose names are hashes of the exact visible bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

from reviewer_support import public_challenge_bytes


HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_3ffc7ef20035_orientation_audit_prototype", HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling orientation-selector prototype")
PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(PROTOTYPE)


def _exact_ints(name: str, values: Iterable[int], low: int, high: int) -> tuple[int, ...]:
    result = tuple(values)
    if not result or any(type(value) is not int or not low <= value <= high for value in result):
        raise ValueError(f"{name} must contain exact integers in {low}..{high}")
    if len(result) != len(set(result)):
        raise ValueError(f"{name} must not contain duplicates")
    return result


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def run_audit(
    output: str | Path,
    *,
    seeds: Iterable[int] = (0, 17, 991),
    demo_counts: Iterable[int] = (2, 3, 4, 5, 6),
    queries: int = 4,
) -> dict:
    """Run the finite authoring audit and write a reproducible evidence directory."""
    seeds = _exact_ints("seeds", seeds, 0, 2**63 - 1)
    demo_counts = _exact_ints("demo_counts", demo_counts, PROTOTYPE.MIN_DEMOS, PROTOTYPE.MAX_DEMOS)
    if type(queries) is not int or not PROTOTYPE.MIN_QUERIES <= queries <= PROTOTYPE.MAX_QUERIES:
        raise ValueError("queries is outside the supported range")

    output = Path(output)
    if output.exists():
        raise FileExistsError(f"refusing existing audit directory: {output}")
    public_dir = output / "public"
    public_dir.mkdir(parents=True)

    rows: list[dict] = []
    blocking: set[str] = set()
    survivor_failures: list[dict] = []
    matched_requests = 0
    label_claims = 0
    episode_cache: dict[tuple[int, int, str], dict] = {}

    for seed in seeds:
        for demos in demo_counts:
            by_scope: dict[str, dict] = {}
            for scope in PROTOTYPE.SCOPES:
                episode = PROTOTYPE.generate_episode(
                    seed,
                    scope=scope,
                    demos=demos,
                    queries=queries,
                )
                episode_cache[(seed, demos, scope)] = episode
                by_scope[scope] = episode
                audit = PROTOTYPE.audit_episode(episode)
                blocking.update(audit["blocking_rivals"])
                if audit["surviving_hypotheses"] != [scope]:
                    survivor_failures.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "scope": scope,
                            "survivors": audit["surviving_hypotheses"],
                        }
                    )
                label_claims += demos + queries
                rows.append(
                    {
                        "seed": seed,
                        "demos": demos,
                        "queries": queries,
                        "scope": scope,
                        "surviving_hypotheses": audit["surviving_hypotheses"],
                        "blocking_rivals": audit["blocking_rivals"],
                    }
                )
            baseline_inputs = _inputs(by_scope[PROTOTYPE.SCOPES[0]])
            if any(_inputs(by_scope[scope]) != baseline_inputs for scope in PROTOTYPE.SCOPES[1:]):
                survivor_failures.append(
                    {"seed": seed, "demos": demos, "error": "settings did not share inputs"}
                )
            matched_requests += 1

    showcase_seed = seeds[0]
    showcase_demos = 3 if 3 in demo_counts else demo_counts[0]
    public_files: list[dict] = []
    for scope in PROTOTYPE.SCOPES:
        episode = episode_cache[(showcase_seed, showcase_demos, scope)]
        for turn in PROTOTYPE.public_turns(episode):
            visible = public_challenge_bytes(turn)
            digest = hashlib.sha256(visible).hexdigest()
            path = public_dir / f"challenge-{digest}.json"
            if path.exists() and path.read_bytes() != visible:
                raise RuntimeError("public hash collision")
            path.write_bytes(visible)
            public_files.append({"path": f"public/{path.name}", "sha256": digest})

    report = {
        "schema": "3ffc7ef20035-parametric-bounded-audit-v1",
        "status": "passed" if not blocking and not survivor_failures else "failed",
        "task_id": PROTOTYPE.TASK_ID,
        "settings": list(PROTOTYPE.SCOPES),
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "queries": queries,
        "hypotheses_per_episode": len(PROTOTYPE.HYPOTHESES),
        "episodes_checked": len(rows),
        "label_claims_checked_by_python_mirror": label_claims,
        "matched_input_requests_checked": matched_requests,
        "blocking_rivals": sorted(blocking),
        "survivor_failures": survivor_failures,
        "public_files": public_files,
        "rows": rows,
        "limits": (
            "Finite declared-rival and projection audit only. Labels here use the task-local "
            "Python mirror; native qualification independently re-executes selected labels in protected Racket."
        ),
    }
    (output / "summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", action="append", type=int)
    parser.add_argument("--demos", action="append", type=int)
    parser.add_argument("--queries", type=int, default=4)
    options = parser.parse_args()
    report = run_audit(
        options.out,
        seeds=options.seed or (0, 17, 991),
        demo_counts=options.demos or (2, 3, 4, 5, 6),
        queries=options.queries,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
