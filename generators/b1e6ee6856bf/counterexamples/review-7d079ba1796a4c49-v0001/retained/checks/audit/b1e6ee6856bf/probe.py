from __future__ import annotations

import hashlib
import importlib.util
import sys
import json
from pathlib import Path

TASK = "b1e6ee6856bf"
OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2] / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
spec = importlib.util.spec_from_file_location(f"audit_{TASK}_generator", REPO / "generators" / TASK / "generator.py")
assert spec and spec.loader
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    requested = {"texture": "single_per_col", "grid_h": 4, "grid_w": 4}
    counterexample = GEN.generate(12345, 0, difficulty="easy", **requested)
    default = GEN.generate(991, 3, difficulty="medium")
    palette_variants = {
        value: GEN.generate(991, 3, difficulty="medium", palette_kind=value)
        for value in GEN.PALETTE_KINDS
    }
    unknown_accepted = False
    unknown_error = None
    try:
        GEN.generate(991, 3, difficulty="medium", definitely_unknown=17)
        unknown_accepted = True
    except Exception as exc:  # evidence only
        unknown_error = f"{type(exc).__name__}: {exc}"

    report = {
        "schema": "audit-probe-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(Path(GEN.__file__).read_bytes()).hexdigest(),
        "seed": 12345,
        "sample_index": 0,
        "difficulty": "easy",
        "requested_overrides": requested,
        "observed_shape": [len(counterexample), len(counterexample[0])],
        "self_check": GEN.self_check(counterexample, difficulty="easy", meta={"overrides": requested}),
        "counterexample_sha256": digest(counterexample),
        "unknown_override_accepted": unknown_accepted,
        "unknown_override_error": unknown_error,
        "palette_kind_digests": {name: digest(grid) for name, grid in palette_variants.items()},
        "palette_kind_unique_outputs": len({digest(grid) for grid in palette_variants.values()}),
        "default_digest": digest(default),
        "findings": [
            "documented grid_h/grid_w overrides are ignored by the degenerate texture path",
            "the returned documented texture is rejected by the generator's own self_check",
            "unknown override keys are accepted",
            "all four documented palette_kind values produce identical output for the same seed/index",
        ],
    }
    (OUT / "input.json").write_text(json.dumps(counterexample, indent=2) + "\n")
    (OUT / "probe-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
