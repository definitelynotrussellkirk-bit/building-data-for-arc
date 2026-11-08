"""Exact-source contract audit for generator 8b70863caead.

This is audit-only tooling.  It does not edit the audited generator.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK = "8b70863caead"
ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
GEN_PATH = REPO / "generators" / TASK / "generator.py"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "shared" / "runtime"))
sys.path.insert(0, str(REPO / "shared"))


def load():
    spec = importlib.util.spec_from_file_location("audit_8b708", GEN_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load audited generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def call(module, *, seed=991, sample_index=0, difficulty="easy", overrides=None):
    overrides = dict(overrides or {})
    try:
        grid = module.generate(seed, sample_index, difficulty=difficulty, **overrides)
        return {
            "accepted": True,
            "grid_sha256": digest(grid),
            "shape": [len(grid), len(grid[0])],
            "self_check": module.self_check(grid),
            "grid": grid,
        }
    except Exception as exc:  # audit records the public boundary exactly
        return {
            "accepted": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> None:
    module = load()
    baseline = call(module)

    inert_pairs = {
        "n": [2, 5],
        "palette_kind": ["warm", "cool"],
        "palette_size": [2, 5],
        "n_distinct_colors": [2, 5],
        "texture": ["warm", "cool"],
    }
    inert = {}
    for axis, values in inert_pairs.items():
        records = [call(module, overrides={axis: value}) for value in values]
        inert[axis] = {
            "values": values,
            "records": [{k: v for k, v in record.items() if k != "grid"} for record in records],
            "same_as_each_other": records[0].get("grid_sha256") == records[1].get("grid_sha256"),
            "same_as_no_override": all(
                record.get("grid_sha256") == baseline.get("grid_sha256") for record in records
            ),
        }

    invalid_declared_textures = {}
    for texture in module.DEGENERATE_TEXTURES:
        record = call(module, overrides={"texture": texture})
        invalid_declared_textures[texture] = {
            k: v for k, v in record.items() if k != "grid"
        }
        if record.get("accepted"):
            (OUT / f"input-{texture}.json").write_text(
                json.dumps(record["grid"], indent=2) + "\n"
            )

    advertised_range_mismatches = {}
    for axis, value in (("grid_h", 7), ("grid_h", 16), ("grid_w", 9), ("grid_w", 18)):
        advertised_range_mismatches[f"{axis}={value}"] = call(
            module, overrides={axis: value}
        )

    invalid_call_arguments = {}
    probes = [
        ("seed=True", {"seed": True}),
        ("seed=1.75", {"seed": 1.75}),
        ("seed='1'", {"seed": "1"}),
        ("sample_index=-1", {"sample_index": -1}),
        ("sample_index='1'", {"sample_index": "1"}),
        ("difficulty='__invalid_difficulty__'", {"difficulty": "__invalid_difficulty__"}),
        ("difficulty=True", {"difficulty": True}),
    ]
    for label, kwargs in probes:
        seed = kwargs.get("seed", 991)
        sample_index = kwargs.get("sample_index", 0)
        difficulty = kwargs.get("difficulty", "easy")
        record = call(module, seed=seed, sample_index=sample_index, difficulty=difficulty)
        invalid_call_arguments[label] = {k: v for k, v in record.items() if k != "grid"}

    undeclared_or_invalid_overrides = {}
    for axis, value in (
        ("bogus_axis", 1),
        ("texture", "bogus"),
        ("palette_kind", "bogus"),
        ("position_bias", "bogus"),
        ("density", "bogus"),
    ):
        record = call(module, overrides={axis: value})
        undeclared_or_invalid_overrides[f"{axis}={value!r}"] = {
            k: v for k, v in record.items() if k != "grid"
        }

    (OUT / "input-valid-baseline.json").write_text(
        json.dumps(baseline["grid"], indent=2) + "\n"
    )

    summary = {
        "schema": "8b70863caead-generator-contract-audit-v1",
        "task": TASK,
        "generator_version": module.VERSION,
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "baseline": {k: v for k, v in baseline.items() if k != "grid"},
        "inert_advertised_axes": inert,
        "invalid_declared_textures": invalid_declared_textures,
        "advertised_range_mismatches": advertised_range_mismatches,
        "invalid_call_arguments": invalid_call_arguments,
        "undeclared_or_invalid_overrides": undeclared_or_invalid_overrides,
        "aggregate": {
            "inert_axis_pairs": sum(item["same_as_each_other"] for item in inert.values()),
            "inert_axis_pairs_tested": len(inert),
            "declared_degenerate_textures_violating_self_check": sum(
                bool(item.get("self_check")) for item in invalid_declared_textures.values()
            ),
            "declared_degenerate_textures_tested": len(invalid_declared_textures),
            "advertised_range_endpoints_rejected": sum(
                not item["accepted"] for item in advertised_range_mismatches.values()
            ),
            "advertised_range_endpoints_tested": len(advertised_range_mismatches),
            "invalid_call_arguments_accepted": sum(
                item["accepted"] for item in invalid_call_arguments.values()
            ),
            "invalid_call_arguments_tested": len(invalid_call_arguments),
            "invalid_or_unknown_overrides_accepted": sum(
                item["accepted"] for item in undeclared_or_invalid_overrides.values()
            ),
            "invalid_or_unknown_overrides_tested": len(undeclared_or_invalid_overrides),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (OUT / "counterexample.json").write_text(
        json.dumps(
            {
                "declared_valid_axis": "texture",
                "declared_valid_value": "no_motifs",
                "input": json.loads((OUT / "input-no_motifs.json").read_text()),
                "generator_self_check": invalid_declared_textures["no_motifs"]["self_check"],
                "finding": "A value advertised as valid produces an input outside the generator's own invariants.",
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
