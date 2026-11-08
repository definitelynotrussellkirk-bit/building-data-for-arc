"""Capture the still-unmodified v1 prototype before native-family edits.

This is a source-pinned historical capture, not the final-family verifier.
The captured exact programs/inputs can be replayed without importing v1.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
TASK = "8de1c257a9c7"
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"
EXPECTED = "91b35345b49ee1f0efeee799ea9f832bae550a3ef19d7cc5d4acd5b03226978c"


def main():
    source = HOME / "prototype.py"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == EXPECTED
    spec = importlib.util.spec_from_file_location("legacy_stamp_baseline", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    from arcpuzzles.parametric_worker import _real_evaluator
    apply, identity, bridge = _real_evaluator(ROOT / "shared" / "runtime")
    records = []
    calls = 0
    try:
        for setting in module.PARAMETER_VALUES:
            episode = module.generate_episode(0, stamp_transform=setting)
            labels = []
            for pair in episode["train"] + episode["test"]:
                observed = apply(episode["program"], pair["input"])
                calls += 1
                assert observed == pair["output"]
                labels.append(observed)
            records.append(episode)
    finally:
        bridge.close()
    output = ROOT.parent / "checks" / TASK / "legacy-baseline.json"
    assert not output.exists()
    report = {
        "schema": "stamp-legacy-baseline-v1", "task_id": TASK,
        "scope": "One seed, both legacy settings, three demonstrations and one query; freshly replayed labels. No native admission or learner-performance claim.",
        "prototype_sha256": EXPECTED,
        "generator_sha256": hashlib.sha256((HOME.parents[1] / "generator.py").read_bytes()).hexdigest(),
        "rule_hash": "c539e2039994", "racket": identity,
        "racket_evaluations": calls, "episodes": records,
    }
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "captured", "episodes": len(records), "racket_evaluations": calls, "prototype_sha256": EXPECTED}))


if __name__ == "__main__":
    main()
