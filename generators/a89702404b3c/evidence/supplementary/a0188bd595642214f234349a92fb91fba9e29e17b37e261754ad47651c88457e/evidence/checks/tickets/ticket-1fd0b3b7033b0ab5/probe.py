from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "a89702404b3c"
PROBE_SEED_HEX = "3507ef74693deef5de1bc0ec6fd6d659dad7ff324a042626f9ea0ee15a7f5891"
repo = Path.cwd()
source = repo / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("ticket_generator", source)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
seed = int(PROBE_SEED_HEX[:16], 16)
base = {"side": 4, "parity": "even", "palette_size": 9}
valid = module.generate(seed, 0, **base)
valid_observed = module.observe_overrides(valid)
invalid_error = None
invalid_observed = None
try:
    invalid = module.generate(seed, 0, side=4.0, parity="even", palette_size=9)
except Exception as exc:  # record actual public API behavior
    invalid_error = {"type": type(exc).__name__, "message": str(exc)}
else:
    invalid_observed = module.observe_overrides(invalid)
result = {
    "schema": "supplementary_ticket_probe/1",
    "ticket_id": "ticket-1fd0b3b7033b0ab5",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "advertised_axis": module.AXES["side"],
    "valid_call": base,
    "valid_observed": valid_observed,
    "invalid_call": {"side": 4.0, "parity": "even", "palette_size": 9},
    "invalid_error": invalid_error,
    "invalid_observed": invalid_observed,
    "finding": invalid_error is None,
    "summary": (
        "Integral float side=4.0 was accepted despite side being advertised as type int."
        if invalid_error is None
        else "Integral float side=4.0 was rejected at the advertised integer boundary."
    ),
}
Path("../checks/tickets/ticket-1fd0b3b7033b0ab5/result.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n"
)
print(json.dumps(result, sort_keys=True))
