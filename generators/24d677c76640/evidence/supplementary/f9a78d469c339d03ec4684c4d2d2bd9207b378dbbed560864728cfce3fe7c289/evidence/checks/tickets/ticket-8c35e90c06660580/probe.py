"""One source-bound advertised override comparison; no broad checks or labels."""
from __future__ import annotations

import hashlib
import json
import signal
import sys
from pathlib import Path


TICKET_ID = "ticket-8c35e90c06660580"
TASK_ID = "24d677c76640"
EXPECTED_SHA256 = "b1b72a55d26ced9e90bee2fd0f250f2bd673c751a1c4ba9db845232a47c2efbd"
EXPECTED_RULE_HASH = "4358f37c5cb2"
PINNED_SEED = "9acf7ba1d5188a6abe441536e3c54ed9ee57a543399da026330f36160ee644fa"


def main():
    signal.alarm(115)
    root = Path.cwd().resolve()
    sys.path.insert(0, str(root / "shared/runtime"))
    from reviewer_support import load_selected_generator

    module, source, source_sha256 = load_selected_generator(TASK_ID, root=root)
    assert source_sha256 == EXPECTED_SHA256, (source, source_sha256)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == EXPECTED_SHA256
    assert module.RULE_HASH == EXPECTED_RULE_HASH

    common = {
        "difficulty": "medium",
        "grid_h": 7,
        "grid_w": 7,
        "shape_id": 11,
        "anchor_relation": "ne",
    }
    report = {
        "ticket_id": TICKET_ID,
        "type": "api_boundary",
        "task_id": TASK_ID,
        "source": str(source.relative_to(root)),
        "generator_sha256": source_sha256,
        "rule_hash": module.RULE_HASH,
        "pinned_seed_hex": PINNED_SEED,
        "generator_seed": int(PINNED_SEED, 16),
        "sample_index": 0,
        "advertised_boundary": module.AXES["shape_color"],
        "common_arguments": common,
        "calls": [],
        "scope": "One valid/invalid shape_color comparison only; no Racket execution, broader parameter sweep, or safety approval.",
    }
    for name, color in (("valid", 2), ("invalid", 1)):
        call = {"name": name, "shape_color": color}
        try:
            grid = module.generate(
                int(PINNED_SEED, 16), 0, shape_color=color, **common
            )
            call.update({
                "returned_grid": grid,
                "self_check_errors": module.self_check(grid),
                "observed_overrides": module.observe_overrides(grid),
            })
        except Exception as exc:
            call.update({"exception_type": type(exc).__name__, "exception_message": str(exc)})
        report["calls"].append(call)

    valid, invalid = report["calls"]
    passed = (
        "returned_grid" in valid
        and valid.get("self_check_errors") == []
        and valid.get("observed_overrides") == {
            "grid_h": 7, "grid_w": 7, "shape_id": 11,
            "shape_color": 2, "anchor_relation": "ne",
        }
        and invalid.get("exception_type") == "ValueError"
    )
    report["comparison_passed"] = passed
    report["status"] = "completed" if passed else "unknown"
    report["source_unchanged_after_probe"] = hashlib.sha256(source.read_bytes()).hexdigest() == EXPECTED_SHA256
    text = json.dumps(report, indent=2) + "\n"
    Path(__file__).with_name("report.json").write_text(text, encoding="utf-8")
    print(text, end="")
    signal.alarm(0)
    return 0 if passed and report["source_unchanged_after_probe"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
