#!/usr/bin/env python3
"""Standard-battery checks for generic generators with embedded PROGRAM rules."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from puzzle_generators import runner  # noqa: E402
from scripts.generic_generator_parity import check_task  # noqa: E402


BANDS = ("easy", "medium", "hard")


def _hash(value: Any) -> str:
    payload = json.dumps(value, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load(task_id: str):
    bundle = runner._load_bundle(task_id)
    if bundle.kind != "generic":
        raise ValueError(f"not a generic generator: {task_id}")
    return bundle


def _tasks(module: Any, seeds: int) -> list[dict[str, Any]]:
    tasks = []
    for band in BANDS:
        for seed in range(seeds):
            task = module.generate_task(seed, difficulty=band)
            if not isinstance(task, dict):
                raise TypeError(f"{band}/{seed}: generate_task did not return a dict")
            tasks.append(task)
    return tasks


def _pairs(task: dict[str, Any]) -> list[dict[str, Any]]:
    return list(task.get("train") or []) + list(task.get("test") or [])


def gate_lint(task_id: str, module: Any, seeds: int) -> dict[str, Any]:
    required_values = ("TASK_ID", "VERSION", "PROGRAM", "RULE_HASH")
    missing = [name for name in required_values if not getattr(module, name, None)]
    required_calls = ("generate_task", "self_check_task")
    missing += [name for name in required_calls if not callable(getattr(module, name, None))]
    if missing:
        raise ValueError("missing generic contract members: " + ", ".join(missing))
    if module.TASK_ID != task_id:
        raise ValueError(f"TASK_ID {module.TASK_ID!r} != {task_id!r}")
    runner._load_rule(task_id)
    task = module.generate_task(0, difficulty="medium")
    findings = list(module.self_check_task(task) or [])
    if findings:
        raise ValueError("self-check findings: " + "; ".join(findings[:3]))
    return {"contract_members": len(required_values) + len(required_calls)}


def gate_rule_smoke(task_id: str, module: Any, seeds: int) -> dict[str, Any]:
    passed, detail = check_task(task_id, seeds=seeds, bands=BANDS)
    if not passed:
        raise ValueError(detail)
    return {"detail": detail}


def gate_dist(task_id: str, module: Any, seeds: int) -> dict[str, Any]:
    tasks = _tasks(module, seeds)
    inputs = [_hash(pair["input"]) for task in tasks for pair in _pairs(task)]
    if len(set(inputs)) != len(inputs):
        raise ValueError(
            f"generic input collision: {len(set(inputs))}/{len(inputs)} distinct"
        )
    if any(pair["input"] == pair["output"] for task in tasks for pair in _pairs(task)):
        raise ValueError("generic sample contains an identity pair")
    return {"tasks": len(tasks), "pairs": len(inputs), "distinct_inputs": len(inputs)}


def gate_profile(task_id: str, module: Any, seeds: int) -> dict[str, Any]:
    strict = getattr(module, "strict_canonical_like", None)
    if not callable(strict):
        raise ValueError("generic generator is missing strict_canonical_like")
    checked = 0
    findings = []
    for task in _tasks(module, seeds):
        for pair in _pairs(task):
            checked += 1
            findings.extend(strict(pair["input"]) or [])
    if findings:
        raise ValueError("strict profile findings: " + "; ".join(findings[:3]))
    return {"pairs": checked, "strict_findings": 0}


def gate_semantic(task_id: str, module: Any, seeds: int) -> dict[str, Any]:
    witnesses = getattr(module, "SEMANTIC_WITNESSES", None)
    rivals = getattr(module, "SEMANTIC_RIVALS", None)
    identifiable = getattr(module, "lesson_identifiable", None)
    if not isinstance(witnesses, dict) or not witnesses:
        raise ValueError("generic generator has no SEMANTIC_WITNESSES")
    if not isinstance(rivals, dict) or not rivals:
        raise ValueError("generic generator has no SEMANTIC_RIVALS")
    if not callable(identifiable):
        raise ValueError("generic generator has no lesson_identifiable")
    tasks = _tasks(module, seeds)
    pair_count = 0
    for task in tasks:
        train = list(task.get("train") or [])
        for query in list(task.get("test") or []):
            findings = list(identifiable(train, query) or [])
            if findings:
                raise ValueError("lesson not identifiable: " + "; ".join(findings[:3]))
        for pair in _pairs(task):
            pair_count += 1
            missing = [name for name, fn in witnesses.items() if not fn(pair["input"])]
            surviving = [
                name for name, fn in rivals.items()
                if fn(pair["input"]) == pair["output"]
            ]
            if missing or surviving:
                raise ValueError(
                    f"semantic contract failure: missing={missing} surviving={surviving}"
                )
    return {
        "tasks": len(tasks),
        "pairs": pair_count,
        "witnesses": len(witnesses),
        "rivals": len(rivals),
    }


def gate_override(task_id: str, module: Any, seeds: int) -> dict[str, Any]:
    checked = 0
    for band in BANDS:
        for seed in range(seeds):
            before = random.getstate()
            first = module.generate_task(seed, difficulty=band)
            second = module.generate_task(seed, difficulty=band)
            if first != second:
                raise ValueError(f"nondeterministic generation at {band}/{seed}")
            if first is second:
                raise ValueError(f"aliased task object at {band}/{seed}")
            mutated = copy.deepcopy(first)
            mutated["train"][0]["input"][0][0] ^= 1
            if second == mutated:
                raise ValueError(f"freshness failure at {band}/{seed}")
            if random.getstate() != before:
                raise ValueError(f"global RNG mutation at {band}/{seed}")
            checked += 1
    try:
        module.generate_task(0, difficulty="not-a-band")
    except (ValueError, TypeError):
        pass
    else:
        raise ValueError("unknown difficulty was silently accepted")
    return {"accepted_coordinates": checked, "unknown_difficulty_rejected": True}


def gate_authority(task_id: str, module: Any, seeds: int) -> dict[str, Any]:
    program = module.PROGRAM
    checked = 0
    for task in _tasks(module, seeds):
        if task.get("program") != program:
            raise ValueError("generated task embeds a different PROGRAM")
        meta_hash = (task.get("meta") or {}).get("rule_hash")
        if meta_hash != module.RULE_HASH:
            raise ValueError("generated task meta.rule_hash is stale")
        checked += 1
    return {"tasks": checked, "rule_hash": module.RULE_HASH}


GATES = {
    "lint": gate_lint,
    "rule_smoke": gate_rule_smoke,
    "dist_gate": gate_dist,
    "profile_floor": gate_profile,
    "semantic_gate": gate_semantic,
    "override": gate_override,
    "racket_lint": gate_rule_smoke,
    "authority_sync": gate_authority,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("stage", choices=sorted(GATES))
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    try:
        bundle = _load(args.task_id)
        detail = GATES[args.stage](args.task_id, bundle.generator_module, args.seeds)
        result = {"status": "PASS", "task_id": args.task_id, "stage": args.stage, **detail}
    except Exception as exc:
        result = {
            "status": "FAIL",
            "task_id": args.task_id,
            "stage": args.stage,
            "error": f"{type(exc).__name__}: {exc}",
        }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
