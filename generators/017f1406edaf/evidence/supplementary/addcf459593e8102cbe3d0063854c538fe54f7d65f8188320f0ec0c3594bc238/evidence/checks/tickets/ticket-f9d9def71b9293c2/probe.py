from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "017f1406edaf"
PINNED_SOURCE_SHA256 = "e80637ec485a311e67a526463fdf36166f860c7e21cb7885643ba710708edadd"
PROBE_SEED_HEX = "0f0b4fb15b984e43665b5453f323619e6ffb3d52b37bdd3198b7f64f3199156f"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
OUT = Path(__file__).with_name("report.json")


def main() -> None:
    if SOURCE_SHA256 != PINNED_SOURCE_SHA256:
        raise RuntimeError(f"source hash drift: {SOURCE_SHA256}")
    seed = int(PROBE_SEED_HEX[:16], 16)
    sample_index = 1
    valid = GEN.generate(seed, sample_index, difficulty="medium", K=2)
    observed = GEN.observe_overrides(valid)
    if observed["K"] != 2 or GEN.self_check(valid):
        raise RuntimeError("valid K=2 override did not round-trip")
    invalid = None
    try:
        GEN.generate(seed, sample_index, difficulty="medium", K=True)
    except Exception as exc:  # exact actual boundary behavior is retained below
        invalid = {"exception_type": type(exc).__name__, "message": str(exc)}
    if invalid is None:
        raise RuntimeError("invalid bool K override was accepted")
    report = {
        "schema": "arcpuzzles-ticket-api-boundary-v1",
        "ticket_id": "ticket-f9d9def71b9293c2",
        "task_id": TASK_ID,
        "probe_seed_hex": PROBE_SEED_HEX,
        "derived_seed": seed,
        "sample_index": sample_index,
        "source_path": str(SOURCE.relative_to(ROOT)),
        "source_sha256": SOURCE_SHA256,
        "boundary": "K override exact integer 2..6; bool must not be treated as int",
        "valid_call": {
            "kwargs": {"difficulty": "medium", "K": 2},
            "observed_overrides": observed,
            "self_check": [],
            "shape": [len(valid), len(valid[0])],
        },
        "invalid_call": {
            "kwargs": {"difficulty": "medium", "K": True},
            **invalid,
        },
        "outcome": "completed",
        "finding": None,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"outcome": "completed", "invalid": invalid}, sort_keys=True))


if __name__ == "__main__":
    main()
