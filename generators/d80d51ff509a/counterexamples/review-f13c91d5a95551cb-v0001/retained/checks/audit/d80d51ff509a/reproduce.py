from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK = "d80d51ff509a"
EXPECTED_SHA = "a2387b78717a08ed6292efbb70bd08079aebba3ade8764a4908f6b77bdfd0d76"


def digest_grid(grid):
    raw = json.dumps(grid, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def attempt(gen, **overrides):
    try:
        grid = gen.generate(19, 41, difficulty="medium", profile_kind="generalized", **overrides)
        return {
            "status": "accepted",
            "grid_sha256": digest_grid(grid),
            "observed": gen.observe_overrides(grid),
            "self_check": gen.self_check(grid, difficulty="medium"),
        }
    except Exception as exc:
        return {"status": "rejected", "error_type": type(exc).__name__, "error": str(exc)}


def main():
    gen, source, source_sha = load_selected_generator(TASK, root=Path.cwd())
    baseline = attempt(gen, grid_h=12, grid_w=16)
    cases = {
        "string_integer_axes": attempt(gen, grid_h="12", grid_w="16"),
        "fractional_axes": attempt(gen, grid_h=12.9, grid_w=16.9),
        "unknown_axis": attempt(gen, grid_h=12, grid_w=16, typo_axis=123),
    }
    report = {
        "schema": "arcpuzzles-audit-reproduction-v1",
        "task_id": TASK,
        "generator_sha256": source_sha,
        "expected_generator_sha256": EXPECTED_SHA,
        "source_hash_matches_assignment": source_sha == EXPECTED_SHA,
        "baseline": baseline,
        "cases": cases,
        "findings": {
            "string_integer_axes_coerced": cases["string_integer_axes"].get("grid_sha256") == baseline.get("grid_sha256"),
            "fractional_axes_truncated": cases["fractional_axes"].get("grid_sha256") == baseline.get("grid_sha256"),
            "unknown_axis_ignored": cases["unknown_axis"].get("grid_sha256") == baseline.get("grid_sha256"),
        },
        "scope": "source-contract only; no Racket-label claim and no source modification",
    }
    out = Path("../checks/audit/d80d51ff509a/finding.json")
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True, indent=2))
    assert report["source_hash_matches_assignment"]
    assert all(report["findings"].values())
    assert baseline["self_check"] == []


if __name__ == "__main__":
    main()
