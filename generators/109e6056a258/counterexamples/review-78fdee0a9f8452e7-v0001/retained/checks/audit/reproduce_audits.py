#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
from typing import Any

PACKET_ROOT = pathlib.Path(__file__).resolve().parents[3]
REPO = PACKET_ROOT / "WORK" / "repo"
OUT = PACKET_ROOT / "WORK" / "checks" / "audit"


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_sha(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode()
    return sha256_bytes(payload)


def write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def audit_109() -> dict[str, Any]:
    task_id = "109e6056a258"
    mod, source = load_generator(task_id)
    source_hash = sha256_bytes(source.read_bytes())
    seed = "audit-op-tf-exact-controls"
    collisions = []
    observed_a = []
    observed_b = []
    lawful = 0
    for sample_index in range(100):
        a = mod.generate(seed, sample_index, difficulty="medium", op_key=1, tf_key=1)
        b = mod.generate(seed, sample_index, difficulty="medium", op_key=5, tf_key=6)
        if a == b:
            collisions.append(sample_index)
        observed_a.append([a[0][0], a[0][-1]])
        observed_b.append([b[0][0], b[0][-1]])
        if not mod.self_check(a) and not mod.self_check(b):
            lawful += 1
    assert len(collisions) == 100, f"expected all override pairs to collide, got {len(collisions)}/100"
    assert lawful == 100, f"expected lawful paired inputs, got {lawful}/100"
    representative = mod.generate(seed, 0, difficulty="medium", op_key=1, tf_key=1)
    write_json(OUT / task_id / "input.json", representative)
    result = {
        "audit_kind": "reproduced_exact_override_defect",
        "task_id": task_id,
        "generator_sha256": source_hash,
        "generator_version": mod.VERSION,
        "seed": seed,
        "sample_indices": [0, 99],
        "difficulty": "medium",
        "comparison": {
            "overrides_a": {"op_key": 1, "tf_key": 1},
            "overrides_b": {"op_key": 5, "tf_key": 6},
            "identical_inputs": len(collisions),
            "denominator": 100,
            "collision_sample_indices": collisions,
            "observed_key_pairs_a": observed_a,
            "observed_key_pairs_b": observed_b,
            "lawful_by_self_check": lawful,
        },
        "representative": {
            "sample_index": 0,
            "requested_overrides": {"op_key": 1, "tf_key": 1},
            "observed_corner_keys": [representative[0][0], representative[0][-1]],
            "input_sha256": grid_sha(representative),
            "input_path": f"checks/audit/{task_id}/input.json",
            "self_check": mod.self_check(representative),
        },
        "finding": (
            "AXES declares op_key and tf_key as exact controls, but generate() draws both "
            "with layout RNG and never consumes the overrides. Opposite override pairs "
            "therefore produce byte-identical inputs."
        ),
    }
    write_json(OUT / task_id / "reproducer.json", result)
    return result


def audit_c99() -> dict[str, Any]:
    task_id = "c99f630b7541"
    mod, source = load_generator(task_id)
    source_hash = sha256_bytes(source.read_bytes())
    seed = "audit-dead-controls"
    collisions = []
    lawful = 0
    for sample_index in range(100):
        a = mod.generate(seed, sample_index, difficulty="medium", asymmetry=False, anchor_corner=False)
        b = mod.generate(seed, sample_index, difficulty="medium", asymmetry=True, anchor_corner=True)
        if a == b:
            collisions.append(sample_index)
        if not mod.self_check(a) and not mod.self_check(b):
            lawful += 1

    domain_attempts: dict[str, dict[str, Any]] = {}
    for axis in ("n_eights", "n_twos"):
        for value in (1, 5, 6, 7, 8):
            key = f"{axis}={value}"
            try:
                grid = mod.generate(seed, 0, difficulty="medium", **{axis: value})
            except Exception as exc:  # evidence records exact public exception
                domain_attempts[key] = {
                    "accepted": False,
                    "exception_type": type(exc).__name__,
                    "message": str(exc),
                }
            else:
                domain_attempts[key] = {
                    "accepted": True,
                    "self_check": mod.self_check(grid),
                }

    assert len(collisions) == 100, f"expected all boolean override pairs to collide, got {len(collisions)}/100"
    assert lawful == 100, f"expected lawful paired inputs, got {lawful}/100"
    assert all(not row["accepted"] for row in domain_attempts.values()), domain_attempts
    representative = mod.generate(
        seed, 0, difficulty="medium", asymmetry=False, anchor_corner=False
    )
    write_json(OUT / task_id / "input.json", representative)
    result = {
        "audit_kind": "reproduced_axis_contract_defects",
        "task_id": task_id,
        "generator_sha256": source_hash,
        "generator_version": mod.VERSION,
        "seed": seed,
        "sample_indices": [0, 99],
        "difficulty": "medium",
        "dead_boolean_controls": {
            "overrides_a": {"asymmetry": False, "anchor_corner": False},
            "overrides_b": {"asymmetry": True, "anchor_corner": True},
            "identical_inputs": len(collisions),
            "denominator": 100,
            "collision_sample_indices": collisions,
            "lawful_by_self_check": lawful,
        },
        "advertised_domain_probe": {
            "schema_valid": {"n_eights": "1..8", "n_twos": "1..8"},
            "attempts": domain_attempts,
            "rejected_attempts": sum(not row["accepted"] for row in domain_attempts.values()),
            "denominator": len(domain_attempts),
        },
        "representative": {
            "sample_index": 0,
            "requested_overrides": {"asymmetry": False, "anchor_corner": False},
            "input_sha256": grid_sha(representative),
            "input_path": f"checks/audit/{task_id}/input.json",
            "self_check": mod.self_check(representative),
        },
        "finding": (
            "asymmetry and anchor_corner are advertised but never read, so opposite values "
            "collide. In addition, AXES advertises n_eights/n_twos 1..8 while the eager "
            "ctx.draw_int calls reject every probed advertised value outside 2..4."
        ),
    }
    write_json(OUT / task_id / "reproducer.json", result)
    return result


def main() -> None:
    result = {"109e6056a258": audit_109(), "c99f630b7541": audit_c99()}
    write_json(OUT / "summary.json", result)
    print(json.dumps({
        task: {
            "generator_sha256": row["generator_sha256"],
            "audit_kind": row["audit_kind"],
        }
        for task, row in result.items()
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
