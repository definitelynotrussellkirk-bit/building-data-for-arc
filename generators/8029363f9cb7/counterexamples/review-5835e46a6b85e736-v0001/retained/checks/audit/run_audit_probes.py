#!/usr/bin/env python3
"""Reproduce the two findings-only adversarial audits in this review packet.

This script intentionally reads each target's *declared* contract instead of
hard-coding rival names or scheduled values, so future edits change the probe's
questions rather than silently producing stale evidence.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

PACKET_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACKET_ROOT / "repo"
for path in (REPO_ROOT / "src", REPO_ROOT / "shared" / "runtime", REPO_ROOT):
    sys.path.insert(0, str(path))

from reviewer_support import canonical_pairs  # noqa: E402


def load_generator(task_id: str):
    source = REPO_ROOT / "generators" / task_id / "generator.py"
    name = f"audit_probe_{task_id}"
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module, source


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n")


def audit_declared_shortcuts(task_id: str = "8029363f9cb7") -> dict[str, Any]:
    gen, source = load_generator(task_id)
    pairs = canonical_pairs(task_id, root=REPO_ROOT)
    declared = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    matches: dict[str, list[bool]] = {}
    first: dict[str, Any] | None = None
    for name, rival in declared.items():
        row: list[bool] = []
        for canonical_index, pair in enumerate(pairs):
            rival_output = rival(pair["input"])
            agrees = rival_output == pair["output"]
            row.append(agrees)
            if first is None and not agrees:
                first = {
                    "rival": name,
                    "canonical_pair": canonical_index,
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input": pair["input"],
                    "intended_output": pair["output"],
                    "rival_output": rival_output,
                }
        matches[name] = row

    out_dir = PACKET_ROOT / "checks" / "audit" / task_id
    if first is not None:
        write_json(out_dir / "input.json", first["input"])
    result = {
        "task_id": task_id,
        "generator_sha256": sha256(source),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "declared_canonical_shortcut_matches": matches,
        "all_declared_shortcuts_fit_all_canonical_pairs": bool(matches)
        and all(all(row) for row in matches.values()),
        "first_disagreement": first,
        "command": ["python3", "../checks/audit/run_audit_probes.py"],
        "cwd": "repo",
    }
    write_json(out_dir / "probe.json", result)
    return result


def _axis_valid_values(axis: dict[str, Any]) -> list[str]:
    valid = axis.get("valid", "")
    if isinstance(valid, str):
        return [value for value in valid.split("|") if value]
    if isinstance(valid, (list, tuple)):
        return [str(value) for value in valid]
    return []


def audit_schedule_axis(task_id: str = "806425ca81b3") -> dict[str, Any]:
    gen, source = load_generator(task_id)
    scheduled_constant = list(getattr(gen, "SCHEDULE_PROFILES", ()))
    valid = _axis_valid_values(gen.AXES["scene_profile"])
    scheduled_outputs = [gen.schedule_profile(0, index, "medium")
                         for index in range(len(scheduled_constant))]
    attempts = []
    for index, profile in enumerate(scheduled_outputs):
        try:
            gen.generate(0, index, difficulty="medium", scene_profile=profile)
        except Exception as exc:  # finding is the public rejection itself
            attempts.append({
                "profile": profile,
                "override_status": "rejected",
                "exception": type(exc).__name__,
                "message": str(exc),
            })
        else:
            attempts.append({"profile": profile, "override_status": "accepted"})

    result = {
        "task_id": task_id,
        "generator_sha256": sha256(source),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "schedule_profiles_constant": scheduled_constant,
        "scene_profile_valid": valid,
        "schedule_profile_outputs": scheduled_outputs,
        "invalid_scheduled_values": sorted(set(scheduled_outputs) - set(valid)),
        "override_attempts": attempts,
        "command": ["python3", "../checks/audit/run_audit_probes.py"],
        "cwd": "repo",
    }
    write_json(PACKET_ROOT / "checks" / "audit" / task_id / "probe.json", result)
    return result


def main() -> int:
    first = audit_declared_shortcuts()
    second = audit_schedule_axis()
    print(json.dumps({
        first["task_id"]: {
            "all_declared_shortcuts_fit_all_canonical_pairs":
                first["all_declared_shortcuts_fit_all_canonical_pairs"],
            "first_disagreement": first["first_disagreement"]["rival"]
                if first["first_disagreement"] else None,
        },
        second["task_id"]: {
            "invalid_scheduled_values": second["invalid_scheduled_values"],
            "override_attempts": second["override_attempts"],
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
