from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "1314f4ccf5cc"
TICKET_SEED = "489f7414c8cf2e2a728a7cca6d0b02bfae267d0742e055989ad213298df47ed2"
EXPECTED_SOURCE_SHA256 = "e3bc887168cfb5a07de7c6ea80ad1acaa7b31a40e54e104ce71f03bd060c2578"
ROOT = Path(__file__).resolve().parents[3] / "repo"
OUT = Path(__file__).resolve().parent / "boundary.json"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("ticket_1314_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    source = ROOT / "generators" / TASK_ID / "generator.py"
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source_sha == EXPECTED_SOURCE_SHA256
    module = load_module(source)
    seed = int.from_bytes(bytes.fromhex(TICKET_SEED)[:8], "big") & ((1 << 63) - 1)

    valid_value = module.SCENE_PROFILES[0]
    grid = module.generate(seed, 0, scene_profile=valid_value)
    observed = module.observe_overrides(grid)
    errors = module.self_check(grid)
    assert observed == {"scene_profile": valid_value}
    assert errors == []

    invalid_value = "public_train_0"
    invalid_exception = None
    try:
        module.generate(seed, 0, scene_profile=invalid_value)
    except Exception as exc:
        invalid_exception = {"type": type(exc).__name__, "message": str(exc)}
    if invalid_exception is None:
        raise AssertionError("invalid scene_profile was silently accepted")
    assert invalid_exception["type"] == "ValueError"

    record = {
        "schema": "arcpuzzles-ticket-api-boundary-v1",
        "ticket_id": "ticket-bcf1e665f5429bf1",
        "task_id": TASK_ID,
        "source_sha256": source_sha,
        "probe_seed_hex": TICKET_SEED,
        "derived_integer_seed": seed,
        "advertised_axis": "scene_profile",
        "valid_call": {
            "value": valid_value,
            "shape": [len(grid), len(grid[0])],
            "observed_overrides": observed,
            "self_check_errors": errors,
        },
        "invalid_call": {
            "value": invalid_value,
            "exception": invalid_exception,
        },
        "result": "exact advertised value is observable and validator-clean; adjacent undeclared value is rejected",
    }
    OUT.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "valid_value": valid_value,
        "observed": observed,
        "self_check_errors": errors,
        "invalid_value": invalid_value,
        "invalid_exception": invalid_exception,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
