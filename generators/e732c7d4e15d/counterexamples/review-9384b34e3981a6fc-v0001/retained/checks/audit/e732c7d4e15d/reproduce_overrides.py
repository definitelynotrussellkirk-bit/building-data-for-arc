#!/usr/bin/env python3
"""Reproduce the e732c7d4e15d override-contract audit without editing it."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "e732c7d4e15d"


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("audited_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = args.repo / "generators" / TASK_ID / "generator.py"
    gen = load_generator(source)
    kwargs = {"seed": 12345, "sample_index": 7, "difficulty": "medium"}
    default = gen.generate(**kwargs)
    density_0 = gen.generate(**kwargs, density=0.0)
    density_1 = gen.generate(**kwargs, density=1.0)
    unknown_texture = gen.generate(**kwargs, texture="not-a-declared-texture")
    payload = {
        "schema": "generator-override-audit-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        **kwargs,
        "finding": "advertised density override is ignored; undeclared texture value is silently accepted",
        "density_0_equals_density_1": density_0 == density_1,
        "unknown_texture_equals_default": unknown_texture == default,
        "has_rule_hash": hasattr(gen, "RULE_HASH"),
        "self_check_density_0": gen.self_check(density_0),
        "density_0_grid": density_0,
        "density_1_grid": density_1,
    }
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({k: payload[k] for k in (
        "task_id", "generator_sha256", "density_0_equals_density_1",
        "unknown_texture_equals_default", "has_rule_hash", "self_check_density_0"
    )}, indent=2))
    return 0 if (payload["density_0_equals_density_1"]
                 and payload["unknown_texture_equals_default"]
                 and not payload["has_rule_hash"]
                 and payload["self_check_density_0"] == []) else 1


if __name__ == "__main__":
    raise SystemExit(main())
