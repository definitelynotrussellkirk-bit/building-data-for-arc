#!/usr/bin/env python3
"""Bounded protected-Racket and finite-rival audit for repeat-policy episodes.

The native worker supplies protected labels for every retained pair. This tool
checks those labels with an independent two-stage oracle, attacks the visible
lesson with declared shortcut rules, and materializes strict one-query public
turns. It is finite reviewer evidence, not universal uniqueness or acceptance.
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
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "0dba62203065"
POLICIES = ("retain", "mark_repeated")
DEFAULT_SEEDS = (0, 17)
DEFAULT_DEMO_COUNTS = (2, 3, 6)


def _load_local(filename: str, stem: str):
    path = HERE / filename
    body = path.read_bytes()
    name = stem + "_" + hashlib.sha256(str(path).encode() + body).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


prototype = _load_local("prototype.py", "_0dba_repeat_prototype_audit")


def _plain_unique_ints(values: Iterable[int], name: str, low: int, high: int) -> tuple[int, ...]:
    result = tuple(values)
    if not result or len(result) > 64 or any(type(v) is not int or not low <= v <= high for v in result):
        raise ValueError(f"{name} must contain 1..64 plain integers in {low}..{high}")
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must be distinct")
    return result


def build_jobs(*, seeds: Iterable[int] = DEFAULT_SEEDS,
               demo_counts: Iterable[int] = DEFAULT_DEMO_COUNTS) -> list[dict[str, Any]]:
    seeds = _plain_unique_ints(seeds, "seeds", 0, 2**63 - 1)
    demos = _plain_unique_ints(demo_counts, "demo_counts", 2, 6)
    return [
        {"seed": seed, "settings": {"repeat_policy": policy}, "demos": count, "queries": 4}
        for policy in POLICIES
        for seed in seeds
        for count in demos
    ]


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for start_row in range(1, height):
        for start_col in range(width - 1):
            start = (start_row, start_col)
            if grid[start_row][start_col] == 0 or start in seen:
                continue
            stack = [start]
            seen.add(start)
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = row + dr, col + dc
                    neighbor = (rr, cc)
                    if (1 <= rr < height and 0 <= cc < width - 1
                            and grid[rr][cc] != 0 and neighbor not in seen):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(sorted(cells))
    return sorted(result, key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells)))


def independent_oracle(grid: list[list[int]], policy: str) -> list[list[int]]:
    """Execute lookup then optional repeated-color marking without prototype helpers."""
    policy = prototype.validate_policy(policy)
    records = []
    for cells in _components(grid):
        left = min(col for _, col in cells)
        records.append({"cells": cells, "color": grid[0][left]})
    output = deepcopy(grid)
    for record in records:
        for row, col in record["cells"]:
            output[row][col] = record["color"]
    if policy == "mark_repeated":
        frequencies = Counter(record["color"] for record in records)
        for record in records:
            if frequencies[record["color"]] > 1:
                for row, col in record["cells"]:
                    output[row][col] = 9
    return output


def analyze_episode(episode: dict[str, Any], policy: str) -> dict[str, Any]:
    from reviewer_support import public_challenge_bytes, public_challenge_id

    policy = prototype.validate_policy(policy)
    teaching = prototype.audit_episode(episode, policy)
    mismatches = []
    for split in ("train", "test"):
        for index, pair in enumerate(episode[split]):
            if independent_oracle(pair["input"], policy) != pair["output"]:
                mismatches.append({"split": split, "pair_index": index})

    public_failures = []
    ids: list[str] = []
    payloads: list[bytes] = []
    for index, view in enumerate(prototype.sequential_views(episode)):
        if set(view) != {"train", "test"} or len(view.get("test", [])) != 1:
            public_failures.append({"turn": index, "kind": "shape"})
            continue
        if any(set(pair) != {"input"} for pair in view["test"]):
            public_failures.append({"turn": index, "kind": "answer_leak"})
        rendered = json.dumps(view, sort_keys=True)
        if any(token in rendered for token in ("program_solution", "repeat_policy", "mark_repeated", "retain")):
            public_failures.append({"turn": index, "kind": "private_metadata"})
        payload = public_challenge_bytes(view)
        ids.append(public_challenge_id(view))
        payloads.append(payload)
    if len(ids) != len(set(ids)) or len(payloads) != len(set(payloads)):
        public_failures.append({"kind": "duplicate_turn"})

    return {
        **teaching,
        "oracle_mismatches": mismatches,
        "public_turn_failures": public_failures,
        "public_turn_ids": ids,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(out: Path, *, seeds: Iterable[int] = DEFAULT_SEEDS,
        demo_counts: Iterable[int] = DEFAULT_DEMO_COUNTS) -> dict[str, Any]:
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(f"choose a fresh audit directory: {out}")
    out.mkdir(parents=True)

    from arcpuzzles.parametric_worker import evaluate_contract
    from reviewer_support import public_challenge_bytes, public_challenge_id

    adapter = _load_local("adapter.py", "_0dba_repeat_adapter_audit")
    contract = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))
    jobs = build_jobs(seeds=seeds, demo_counts=demo_counts)
    execution = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    _write_json(out / "execution.json", execution)

    failures: list[dict[str, Any]] = []
    episodes: list[dict[str, Any]] = []
    saved_payloads: dict[bytes, str] = {}
    first_seed = min(job["seed"] for job in jobs)
    for episode_index, episode in enumerate(execution["episodes"]):
        policy = episode["settings"]["repeat_policy"]
        record = analyze_episode(episode, policy)
        record.update({
            "episode_index": episode_index,
            "seed": episode["seed"],
            "settings": episode["settings"],
            "demos": len(episode["train"]),
            "queries": len(episode["test"]),
        })
        if record["setting_survivors"] != [policy]:
            failures.append({"kind": "setting_ambiguity", "episode_index": episode_index,
                             "survivors": record["setting_survivors"]})
        if record["harmful_survivors"]:
            failures.append({"kind": "harmful_rival_survivor", "episode_index": episode_index,
                             "rivals": record["harmful_survivors"]})
        if set(record["refuted_rivals"]) != set(prototype.RIVALS):
            failures.append({"kind": "unrefuted_rival", "episode_index": episode_index,
                             "refuted": record["refuted_rivals"]})
        for mismatch in record["oracle_mismatches"]:
            failures.append({"kind": "oracle_mismatch", "episode_index": episode_index, **mismatch})
        for public_failure in record["public_turn_failures"]:
            failures.append({"kind": "public_turn", "episode_index": episode_index, **public_failure})

        single = adapter.generate(episode["seed"], episode["settings"], len(episode["train"]), 1)
        if prototype.sequential_views(episode)[0] != prototype.public_challenge(single):
            failures.append({"kind": "first_turn_prefix_mismatch", "episode_index": episode_index})

        if episode["seed"] == first_seed and len(episode["train"]) == 3:
            for view in prototype.sequential_views(episode):
                payload = public_challenge_bytes(view)
                public_id = public_challenge_id(view)
                previous = saved_payloads.setdefault(payload, public_id)
                if previous != public_id:
                    failures.append({"kind": "public_id_instability", "episode_index": episode_index})
                path = out / "public" / f"{public_id}.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
        episodes.append(record)

    source_paths = [
        ROOT / "generators" / TASK_ID / "generator.py",
        HERE / "adapter.py",
        HERE / "audit.py",
        HERE / "prototype.py",
        HERE / "promotion.json",
        HERE / "programs" / "retain.rkt",
        HERE / "programs" / "mark_repeated.rkt",
    ]
    counts = {
        "jobs": len(jobs),
        "episodes": len(episodes),
        "protected_racket_evaluations": execution["racket_evaluations"],
        "protected_label_pairs": sum(len(ep["train"]) + len(ep["test"]) for ep in execution["episodes"]),
        "named_rival_checks": len(episodes) * len(prototype.RIVALS),
        "setting_checks": len(episodes) * len(prototype.POLICIES),
        "public_turns_checked": len(episodes) * 4,
        "saved_public_turns": len(saved_payloads),
        "exact_30x30_queries": sum(
            len(pair["input"]) == 30 and len(pair["input"][0]) == 30
            for ep in execution["episodes"] for pair in ep["test"]
        ),
    }
    report = {
        "schema": "post-lookup-repeat-policy-audit-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "scope": "finite declared settings/rivals and recorded seeds/counts only",
        "jobs": jobs,
        "counts": counts,
        "racket": execution["racket"],
        "source_sha256": {path.relative_to(ROOT).as_posix(): _sha256(path) for path in source_paths},
        "episodes": episodes,
        "failures": failures,
        "limits": [
            "Finite named rivals do not prove universal lesson uniqueness.",
            "Independent oracle and rivals are reviewer Python; retained pair labels are protected-Racket outputs.",
            "This audit is reviewer evidence, not owner acceptance or training admission.",
        ],
    }
    _write_json(out / "audit.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--demo-counts", nargs="+", type=int, default=list(DEFAULT_DEMO_COUNTS))
    args = parser.parse_args(argv)
    report = run(args.out, seeds=args.seeds, demo_counts=args.demo_counts)
    print(json.dumps({"status": report["status"], "counts": report["counts"],
                      "failures": len(report["failures"]), "out": str(args.out)}, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
