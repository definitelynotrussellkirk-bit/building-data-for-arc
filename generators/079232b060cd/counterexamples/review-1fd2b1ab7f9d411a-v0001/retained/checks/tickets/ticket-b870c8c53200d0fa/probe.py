from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TICKET_ID = "ticket-b870c8c53200d0fa"
TASK_ID = "079232b060cd"
PINNED_SHA256 = "41a0b6eb7726c746923245cf5ecb8686ec2f87dd3ab7f94336e2b0a6a452020f"
PROBE_SEED_HEX = "94881bc7369a270f3c8fc46aa9afb0d43183333969b26099e93245c7b859cb28"
ROOT = find_root(__file__)
OUT = ROOT.parent / "checks" / "tickets" / TICKET_ID
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)

assert SOURCE_SHA256 == PINNED_SHA256
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == PINNED_SHA256
assert GEN.AXES["grid_h"]["valid"] == "5..14"

seed = int(PROBE_SEED_HEX, 16)
base = {
    "difficulty": None,
    "texture": "plain",
    "grid_w": 8,
    "seed_count": 2,
}

valid_call = {**base, "grid_h": 11}
valid_grid = GEN.generate(seed, 0, **valid_call)
valid_result = {
    "call": valid_call,
    "status": "returned",
    "shape": [len(valid_grid), len(valid_grid[0])],
    "self_check": GEN.self_check(valid_grid),
}

advertised_call = {**base, "grid_h": 12}
try:
    GEN.generate(seed, 0, **advertised_call)
except Exception as exc:  # retain the public API's actual exception contract
    advertised_result = {
        "call": advertised_call,
        "status": "raised",
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
    }
else:
    advertised_result = {
        "call": advertised_call,
        "status": "returned",
    }

report = {
    "schema": "arcpuzzles-supplementary-api-boundary-v1",
    "ticket_id": TICKET_ID,
    "task_id": TASK_ID,
    "generator_path": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA256,
    "rule_hash": GEN.RULE_HASH if hasattr(GEN, "RULE_HASH") else "1a04aaa4fba8",
    "probe_seed_hex": PROBE_SEED_HEX,
    "sample_index": 0,
    "advertised_axis": {
        "name": "grid_h",
        "valid": GEN.AXES["grid_h"]["valid"],
        "default": GEN.AXES["grid_h"]["default"],
    },
    "comparison": {
        "valid_at_hidden_default_ceiling": valid_result,
        "next_advertised_value": advertised_result,
    },
    "finding": (
        "grid_h=12 is inside the advertised global 5..14 domain but the "
        "default-difficulty path rejects it through a hidden 7..11 draw bound"
    ),
}

assert valid_result["shape"] == [11, 8]
assert valid_result["self_check"] == []
assert advertised_result["status"] == "raised"
assert advertised_result["exception_type"] == "ValueError"

(OUT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report["comparison"], indent=2, sort_keys=True))
