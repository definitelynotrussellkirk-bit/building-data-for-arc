#!/usr/bin/env python3
"""One bounded supported/unsupported scene_family API comparison."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import signal
import sys
import time


TICKET = "ticket-4b2520ea9201c6cd"
TASK = "4ebdc8d865ce"
SOURCE_SHA256 = "943bbd19be3918848e6377245c7f264068812dc9331f0e19a97658d189927797"
RULE_HASH = "6c1ad8a5edc2"
SEED_HEX = "5e4df43017aeaf7d2b7a6fe8a28b5451afdfe80d97d11e5fb623cbc42997c0d8"
ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "repo/generators" / TASK / "generator.py"
COMMAND = ("PYTHONPATH=repo/shared/runtime:repo/src PYTHONDONTWRITEBYTECODE=1 "
           "timeout 120s python -B checks/tickets/" + TICKET + "/probe.py")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deadline(_signum, _frame):
    raise TimeoutError("targeted probe exceeded its internal 115-second deadline")


def observe(module, family):
    call = {"seed": int(SEED_HEX, 16), "sample_index": 0,
            "difficulty": "easy", "scene_family": family}
    started = time.monotonic()
    result = {"arguments": call}
    try:
        grid = module.generate(**call)
        result.update(outcome="returned", grid=grid,
                      dimensions=[len(grid), len(grid[0])],
                      self_check_errors=module.self_check(grid, difficulty="easy"),
                      observed_overrides=module.observe_overrides(grid))
    except Exception as error:
        result.update(outcome="raised", exception_type=type(error).__name__,
                      exception_message=str(error))
    result["elapsed_monotonic_seconds"] = time.monotonic() - started
    return result


def main():
    started = time.monotonic()
    report = {
        "schema": "bounded-api-boundary-probe-v1", "ticket_id": TICKET,
        "type": "api_boundary", "task_id": TASK, "consumer": "target_current_audit",
        "source_path": str(SOURCE.relative_to(ROOT)),
        "expected_source_sha256": SOURCE_SHA256, "pinned_rule_hash": RULE_HASH,
        "probe_sha256": sha256(Path(__file__)), "probe_seed_hex": SEED_HEX,
        "seed_conversion": "int(probe_seed_hex, 16)", "command": COMMAND,
        "cwd": os.getcwd(), "python_version": platform.python_version(),
        "environment": {key: os.environ.get(key) for key in
                        ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE")},
        "budget": {"authoring_minutes": 10, "targeted_probe_seconds": 120,
                   "targeted_probes": 1},
        "authoring_elapsed_seconds": None, "targeted_probes_executed": 1,
        "scope": "One scene_family valid/invalid comparison; no reference execution or suite",
    }
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(115)
    try:
        report["source_sha256_before"] = sha256(SOURCE)
        if report["source_sha256_before"] != SOURCE_SHA256:
            raise RuntimeError("pinned source hash mismatch; target was not imported")
        spec = importlib.util.spec_from_file_location("ticket_target_4ebdc8d865ce", SOURCE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report["advertised_axis"] = module.AXES["scene_family"]
        report["observed_rule_hash"] = module.RULE_HASH
        report["runtime_source_hashes"] = {
            str(Path(sys.modules[name].__file__).resolve().relative_to(ROOT)):
            sha256(Path(sys.modules[name].__file__))
            for name in ("puzzle_generators.base", "puzzle_generators.helpers.grid")}
        valid = report["valid_call"] = observe(module, "linked")
        invalid = report["invalid_call"] = observe(module, "unsupported")
        valid_ok = (valid["outcome"] == "returned" and not valid["self_check_errors"]
                    and valid["observed_overrides"] == {"scene_family": "linked"})
        invalid_ok = (invalid["outcome"] == "raised"
                      and invalid["exception_type"] == "ValueError")
        report["source_sha256_after"] = sha256(SOURCE)
        if report["source_sha256_after"] != SOURCE_SHA256 or module.RULE_HASH != RULE_HASH:
            raise RuntimeError("pinned source/rule identity changed")
        report["status"] = "completed" if valid_ok and invalid_ok else "unknown"
        report["summary"] = (
            "Supported scene_family='linked' returned a valid linked scene; unsupported "
            "scene_family='unsupported' raised ValueError. No issue observed at this boundary."
            if valid_ok and invalid_ok else
            "The single comparison did not establish the expected boundary; inspect observations.")
        code = 0 if report["status"] == "completed" else 3
    except Exception as error:
        report.update(status="blocked", summary=f"{type(error).__name__}: {error}")
        code = 2
    finally:
        signal.alarm(0)
    report["elapsed_monotonic_seconds"] = time.monotonic() - started
    report["timing_scope"] = "probe body including target import; excludes result serialization"
    report["process_exit_status"] = code
    output = Path(__file__).with_name("result.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
