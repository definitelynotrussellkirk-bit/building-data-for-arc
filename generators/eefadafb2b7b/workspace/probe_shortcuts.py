#!/usr/bin/env python3
"""Reproduce canonical shortcut ambiguity and final curriculum separation.

Run from the packet root with::

    PYTHONPATH=repo:repo/src:repo/shared/runtime python3 \
      repo/generators/eefadafb2b7b/workspace/probe_shortcuts.py \
      --out checks/eefadafb2b7b-shortcut-probe.json

The probe intentionally discovers rivals through the generator's exported
``CANONICAL_SHORTCUTS`` and ``LESSON_COMPETITORS`` declarations.  It does not
maintain a second handwritten rival inventory that can drift from the task.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path
from typing import Any

TASK_ID = "eefadafb2b7b"
REPO = Path(__file__).resolve().parents[3]
PACKET_ROOT = REPO.parent
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
for import_root in (REPO, REPO / "src", REPO / "shared" / "runtime"):
    value = str(import_root)
    if value not in sys.path:
        sys.path.insert(0, value)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_row() -> dict[str, Any]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical row not found: {TASK_ID}")


def _pair_record(index: int, pair: dict[str, Any], shortcuts: dict[str, Any]) -> dict[str, Any]:
    output = pair["output"]
    rival_outputs = {name: rival(pair["input"]) for name, rival in shortcuts.items()}
    return {
        "pair_index": index,
        "intended_output": output,
        "rival_outputs": rival_outputs,
        "all_declared_shortcuts_fit": all(value == output for value in rival_outputs.values()),
    }


def _window_record(gen: Any, seed: int, start: int) -> dict[str, Any]:
    count = int(gen.EXAMPLES_NEEDED)
    grids = [gen.generate(seed, index, difficulty="hard") for index in range(start, start + count)]
    demos = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids]
    query_grid = gen.generate(seed, start + count, difficulty="hard")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    competitor_refutations = {
        name: [
            index
            for index, demo in enumerate(demos)
            if rival(demo["input"]) != demo["output"]
        ]
        for name, rival in gen.LESSON_COMPETITORS.items()
    }
    return {
        "start": start,
        "sample_indices": list(range(start, start + count)),
        "profiles": [gen.observe_overrides(grid)["lesson_profile"] for grid in grids],
        "lesson_identifiability_errors": gen.lesson_identifiable(demos, query),
        "competitor_refutations": competitor_refutations,
        "all_declared_competitors_refuted": all(competitor_refutations.values()),
    }


def _challenge_witness(gen: Any) -> dict[str, Any] | None:
    challenge_path = PACKET_ROOT / "solve" / "challenge.json"
    if not challenge_path.exists():
        return None
    challenge = json.loads(challenge_path.read_text(encoding="utf-8"))
    for index, pair in enumerate(challenge.get("train", [])):
        intended = pair["output"]
        rival = gen.CANONICAL_SHORTCUTS.get("four_connected_bridge")
        if rival is None:
            continue
        rival_output = rival(pair["input"])
        if rival_output != intended:
            return {
                "source": "solve/challenge.json",
                "train_index": index,
                "input": pair["input"],
                "authoritative_racket_output": intended,
                "python_rule_mirror_output": gen.rule_mirror(pair["input"]),
                "four_connected_rival_output": rival_output,
                "validator_errors": gen.self_check(pair["input"]),
                "observed_overrides": gen.observe_overrides(pair["input"]),
            }
    return None


def build_report() -> dict[str, Any]:
    gen = importlib.import_module(f"generators.{TASK_ID}.generator")
    canonical = _canonical_row()
    pairs = list(canonical["train"]) + list(canonical["test"])

    canonical_records = [
        _pair_record(index, pair, gen.CANONICAL_SHORTCUTS)
        for index, pair in enumerate(pairs)
    ]

    seed = 314159
    cyclic_starts = list(range(len(gen.SCHEDULE_PROFILES)))
    windows = [_window_record(gen, seed, start) for start in cyclic_starts]

    profile_witnesses: list[dict[str, Any]] = []
    for sample_index, profile in enumerate(gen.SCHEDULE_PROFILES):
        grid = gen.generate(
            seed,
            sample_index,
            difficulty="hard",
            lesson_profile=profile,
        )
        expected = gen.rule_mirror(grid)
        named_rivals = list(gen.WITNESS_RIVALS[profile])
        rival_outputs = {
            name: gen.SEMANTIC_RIVALS[name](grid)
            for name in named_rivals
        }
        profile_witnesses.append(
            {
                "sample_index": sample_index,
                "overrides": {"lesson_profile": profile},
                "profile": profile,
                "input": grid,
                "intended_output": expected,
                "named_rival_outputs": rival_outputs,
                "validator_errors": gen.self_check(grid),
                "observed_overrides": gen.observe_overrides(grid),
                "witness_predicate": bool(gen.SEMANTIC_WITNESSES[profile](grid)),
                "all_named_rivals_disagree": all(value != expected for value in rival_outputs.values()),
            }
        )

    challenge_witness = _challenge_witness(gen)
    failures: list[str] = []
    for record in canonical_records:
        if not record["all_declared_shortcuts_fit"]:
            failures.append(f"canonical pair {record['pair_index']} rejects a declared shortcut")
    for record in windows:
        if record["lesson_identifiability_errors"]:
            failures.append(
                f"window {record['start']} is not identifiable: "
                + "; ".join(record["lesson_identifiability_errors"])
            )
        if not record["all_declared_competitors_refuted"]:
            failures.append(f"window {record['start']} leaves a declared competitor alive")
    for record in profile_witnesses:
        if record["validator_errors"]:
            failures.append(f"profile {record['profile']} failed validation")
        if not record["witness_predicate"] or not record["all_named_rivals_disagree"]:
            failures.append(f"profile {record['profile']} is not a direct witness")
    if challenge_witness is None:
        failures.append("no emitted four-connectivity witness found in fresh challenge demonstrations")
    elif challenge_witness["validator_errors"]:
        failures.append("fresh challenge witness failed generator validation")

    return {
        "schema": "eefadafb2b7b-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": _sha256(GENERATOR_PATH),
        "rule_hash": gen.RULE_HASH,
        "canonical_pair_count": len(pairs),
        "canonical_shortcuts": list(gen.CANONICAL_SHORTCUTS),
        "canonical_results": canonical_records,
        "canonical_shortcuts_fit_all_pairs": all(
            record["all_declared_shortcuts_fit"] for record in canonical_records
        ),
        "lesson_policy": {
            "examples_needed": gen.EXAMPLES_NEEDED,
            "schedule_profiles": list(gen.SCHEDULE_PROFILES),
            "seed": seed,
            "difficulty": "hard",
            "cyclic_start_count": len(cyclic_starts),
        },
        "cyclic_windows": windows,
        "all_cyclic_windows_identifiable": all(
            not record["lesson_identifiability_errors"]
            and record["all_declared_competitors_refuted"]
            for record in windows
        ),
        "profile_witnesses": profile_witnesses,
        "fresh_challenge_four_connectivity_witness": challenge_witness,
        "failures": failures,
        "ok": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report()
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
