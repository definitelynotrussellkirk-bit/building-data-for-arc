"""One source-bound API boundary comparison; no peer edits or output labels."""
import hashlib
import json
from pathlib import Path
import time

from reviewer_support import find_root, load_selected_generator

TICKET = "ticket-b53b5a63816ffaaf"
TASK_ID = "9c75b1456763"
EXPECTED_SHA = "d5056d94e7217a201f16d249328bf02f931acde3a301dfdffa2444e6e997a1c1"
EXPECTED_RULE = "58004efe7e78"
SEED_HEX = "2be40081a1f39212e274b915bcc0503f329593c1e478970360948d2a92bd3215"
SEED = int(SEED_HEX, 16)
COMMON = {"difficulty": "hard", "profile": "p18_5", "layout": "bent"}


def main():
    started = time.monotonic()
    report = {"schema": "arc-api-boundary-probe-v1", "ticket_id": TICKET,
              "type": "api_boundary", "task_id": TASK_ID,
              "status": "inconclusive", "elapsed_minutes": None,
              "seed_hex": SEED_HEX, "seed": SEED,
              "seed_derivation": "int(ticket_seed_hex, 16)", "sample_index": 0,
              "source_sha256_expected": EXPECTED_SHA,
              "rule_hash_expected": EXPECTED_RULE,
              "api_case": {
                  "boundary": "nodes_per_network upper bound: integer 4 versus integer 5",
                  "advertised_type": "int", "advertised_valid": "2..4",
                  "common_kwargs": COMMON,
                  "source_contract": "generators/9c75b1456763/generator.py#AXES",
                  "notes_contract": "generators/9c75b1456763/notes.md#D4",
                  "api_document": "docs/reference/PUZZLE_GENERATOR_SPEC.md#Axes"},
              "cases": [], "generate_calls": 0,
              "scope": "One targeted runtime probe, one valid/invalid call comparison; no census.",
              "racket_execution": "not_applicable: input/override API boundary only",
              "peer_edits": False,
              "limits": ["One pinned seed and sample index, one profile, one layout, one difficulty.",
                         "Axis realization is reported by the selected observe_overrides implementation.",
                         "No label correctness, global API coverage, approval, or training admission claim."]}
    try:
        root = find_root(__file__)
        module, source_path, digest = load_selected_generator(TASK_ID, root=root)
        report.update(source_sha256=digest,
                      source_path=source_path.relative_to(root).as_posix(),
                      rule_hash=getattr(module, "RULE_HASH", None),
                      advertised_axis=module.AXES.get("nodes_per_network"))
        if digest != EXPECTED_SHA or report["rule_hash"] != EXPECTED_RULE:
            raise RuntimeError("pinned source/rule identity mismatch; no generator calls executed")
        for name, value in (("valid_upper_bound", 4), ("invalid_adjacent_value", 5)):
            case = {"name": name, "kwargs": dict(COMMON, nodes_per_network=value)}
            report["cases"].append(case)
            stage = "generate"
            try:
                report["generate_calls"] += 1
                grid = module.generate(SEED, 0, **case["kwargs"])
                case.update(outcome="returned", input=grid,
                            shape=[len(grid), len(grid[0])],
                            input_sha256=hashlib.sha256(json.dumps(
                                grid, separators=(",", ":")).encode()).hexdigest())
                stage = "self_check"
                case["self_check_errors"] = module.self_check(grid)
                stage = "observe_overrides"
                case["observed_overrides"] = module.observe_overrides(grid)
            except Exception as error:
                case.update(outcome="exception", exception_stage=stage,
                            exception_type=type(error).__name__, exception_message=str(error))
        valid, invalid = report["cases"]
        good_valid = (valid.get("outcome") == "returned"
                      and valid.get("shape") == [18, 18]
                      and valid.get("self_check_errors") == []
                      and valid.get("observed_overrides") == {
                          "profile": "p18_5", "nodes_per_network": 4, "layout": "bent"})
        good_invalid = (invalid.get("outcome") == "exception"
                        and invalid.get("exception_stage") == "generate"
                        and invalid.get("exception_type") == "ValueError")
        report["status"] = "no_finding" if good_valid and good_invalid else "finding"
        report["checks"] = {"valid_upper_bound_realized": good_valid,
                            "invalid_adjacent_value_rejected": good_invalid}
        report["conclusion"] = (
            "At this pinned seed/index, nodes_per_network=4 yields a lawful 18x18 "
            "input with all requested axes recovered, while 5 raises ValueError. "
            "No finding at the tested upper boundary."
            if report["status"] == "no_finding" else
            "The two-call comparison did not satisfy the advertised boundary; inspect the retained cases.")
    except Exception as error:
        report["error"] = {"type": type(error).__name__, "message": str(error)}
        report["conclusion"] = "Execution was inconclusive; no boundary-wide conclusion is justified."
    report["runtime_elapsed_seconds"] = time.monotonic() - started
    evidence = Path(__file__).resolve().with_name("evidence.json")
    evidence.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    print(str(evidence))
    return 0 if report["status"] == "no_finding" else 1


if __name__ == "__main__":
    raise SystemExit(main())
